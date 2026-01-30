# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeeplUserAssignment(models.Model):
    _name = 'peepl.user.assignment'
    _description = 'Peepl User Assignment'

    user_id = fields.Many2one('res.users', string='User', required=True)
    allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_users')
    position_id = fields.Many2one('hr.contract.type', string='Employment Types', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    assigned_by = fields.Many2one('res.users', string='Assigned By', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            # Try to get department from hr.employee first
            try:
                employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
                if employee and employee.department_id:
                    self.department_id = employee.department_id.id
                    return
            except:
                pass
            
            # Fallback to existing assignment
            existing_assignment = self.search([
                ('user_id', '=', self.user_id.id),
                ('active', '=', True),
                ('department_id', '!=', False)
            ], limit=1)
            
            if existing_assignment:
                self.department_id = existing_assignment.department_id.id

    @api.onchange('position_id')
    def _onchange_position_id(self):
        if self.position_id and self.position_id.name and 'bod' in self.position_id.name.lower():
            self.department_id = False

    @api.constrains('user_id', 'position_id', 'department_id')
    def _check_assignment_rules(self):
        for record in self:
            current_user = self.env.user
            
            # Check if department is required (not BOD)
            if record.position_id and record.position_id.name and 'bod' not in record.position_id.name.lower() and not record.department_id:
                raise ValidationError("Department is required for non-BOD positions.")
            
            # BOD can assign anyone to any department
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                continue
            
            # Manager can only assign staff to their own department
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                if record.position_id.name and 'staff' not in record.position_id.name.lower():
                    raise ValidationError("Manager can only assign Staff level positions.")
                
                # Get current user's department
                current_assignment = self.search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                if current_assignment and record.department_id != current_assignment.department_id:
                    raise ValidationError("Manager can only assign users to their own department.")
            
            else:
                raise ValidationError("You don't have permission to assign users.")

    def write(self, vals):
        result = super(PeeplUserAssignment, self).write(vals)
        # Trigger PIC overview update
        if 'user_id' in vals or 'position_id' in vals or 'department_id' in vals or 'active' in vals:
            self._update_pic_overview()
        return result

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # Auto-set department from user's HR employee if not BOD
            if vals.get('user_id') and vals.get('position_id'):
                position = self.env['hr.contract.type'].browse(vals['position_id'])
                if position.name and 'bod' in position.name.lower():
                    vals['department_id'] = False
                elif not vals.get('department_id'):
                    # Try to get department from hr.employee
                    try:
                        employee = self.env['hr.employee'].search([('user_id', '=', vals['user_id'])], limit=1)
                        if employee and employee.department_id:
                            vals['department_id'] = employee.department_id.id
                    except:
                        # Fallback to existing assignment or current user's department
                        existing_assignment = self.search([
                            ('user_id', '=', vals['user_id']),
                            ('active', '=', True),
                            ('department_id', '!=', False)
                        ], limit=1)
                        
                        if existing_assignment:
                            vals['department_id'] = existing_assignment.department_id.id
                        else:
                            current_user_assignment = self.search([
                                ('user_id', '=', self.env.user.id),
                                ('active', '=', True)
                            ], limit=1)
                            if current_user_assignment and current_user_assignment.department_id:
                                vals['department_id'] = current_user_assignment.department_id.id
        
        result = super(PeeplUserAssignment, self).create(vals_list)
        self._update_pic_overview()
        return result

    def _update_pic_overview(self):
        self.env['peepl.pic.overview'].update_all_stats()

    def sync_all_assignments(self):
        assignments = self.search([('active', '=', True)])
        for assignment in assignments:
            assignment._update_user_groups(assignment)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': f'Successfully synced {len(assignments)} user assignments with access groups',
            }
        }

    @api.depends('create_uid', 'user_id')
    def _compute_allowed_users(self):
        for record in self:
            current_user = self.env.user
            # Get already assigned users
            assigned_user_ids = self.search([('active', '=', True)]).mapped('user_id').ids
            
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                # BOD: all unassigned users
                record.allowed_user_ids = self.env['res.users'].search([('id', 'not in', assigned_user_ids)])
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager: unassigned users from same department only
                try:
                    # Get manager's department from hr.employee
                    manager_employee = self.env['hr.employee'].search([('user_id', '=', current_user.id)], limit=1)
                    if manager_employee and manager_employee.department_id:
                        # Get unassigned users from same department
                        unassigned_users = self.env['res.users'].search([('id', 'not in', assigned_user_ids)])
                        same_dept_users = []
                        
                        for user in unassigned_users:
                            user_employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                            if user_employee and user_employee.department_id.id == manager_employee.department_id.id:
                                same_dept_users.append(user.id)
                        
                        record.allowed_user_ids = self.env['res.users'].browse(same_dept_users)
                    else:
                        # Manager has no department, show no users
                        record.allowed_user_ids = self.env['res.users']
                except:
                    record.allowed_user_ids = self.env['res.users']
            else:
                # Staff: only themselves if not assigned
                if current_user.id not in assigned_user_ids:
                    record.allowed_user_ids = current_user
                else:
                    record.allowed_user_ids = self.env['res.users']