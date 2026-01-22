# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeeplUserAssignment(models.Model):
    _name = 'peepl.user.assignment'
    _description = 'Peepl User Assignment'

    user_id = fields.Many2one('res.users', string='User', required=True)
    position_id = fields.Many2one('peepl.position', string='Positions', required=True)
    department_id = fields.Many2one('peepl.department', string='Department', required=True)
    assigned_by = fields.Many2one('res.users', string='Assigned By', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('position_id')
    def _onchange_position_id(self):
        # Remove onchange for now - will handle in write method only
        pass

    @api.constrains('user_id', 'position_id', 'department_id')
    def _check_assignment_rules(self):
        for record in self:
            current_user = self.env.user
            
            # BOD can assign anyone to any department
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                continue
            
            # Manager can only assign staff to their own department
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                if record.position_id.level != 'staff':
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
        result = super(PeeplUserAssignment, self).create(vals_list)
        # Trigger PIC overview update
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

    @api.model
    def manual_sync_all(self):
        """Manual method to sync all assignments - can be called from console"""
        assignments = self.search([('active', '=', True)])
        for assignment in assignments:
            assignment._update_user_groups(assignment)
        return len(assignments)