# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeeplUserAssignment(models.Model):
    _name = 'peepl.user.assignment'
    _description = 'Peepl User Assignment'

    user_id = fields.Many2one('res.users', string='User', required=True)
    allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_users', compute_sudo=True)
    allowed_job_ids = fields.Many2many('hr.job', compute='_compute_allowed_jobs', compute_sudo=True)
    allowed_department_ids = fields.Many2many('hr.department', compute='_compute_allowed_departments', compute_sudo=True)
    job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    division_id = fields.Many2one('peepl.division', string='Division')
    division_users = fields.Html(string='Division Users', compute='_compute_division_users')
    assigned_by = fields.Many2one('res.users', string='Assigned By', default=lambda self: self.env.user, readonly=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('division_id', 'user_id')
    def _compute_division_users(self):
        for record in self:
            if record.division_id:
                current_user = self.env.user
                if current_user.has_group('peepl_weekly_report.group_peepl_manager') or current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                    division_assignments = self.sudo().search([
                        ('division_id', '=', record.division_id.id),
                        ('active', '=', True),
                        ('user_id', '!=', record.user_id.id)
                    ])
                    
                    supervisors = []
                    managers = []
                    staff = []
                    
                    for assignment in division_assignments:
                        user_name = assignment.user_id.name
                        if assignment.user_id.has_group('peepl_weekly_report.group_peepl_manager'):
                            managers.append(user_name)
                        elif assignment.user_id.has_group('peepl_weekly_report.group_peepl_supervisor'):
                            supervisors.append(user_name)
                        else:
                            staff.append(user_name)
                    
                    html = '<style>.division-card{background:var(--o-view-background-color,#fff);color:var(--o-main-text-color,#000);border:1px solid var(--o-border-color,#dee2e6)}</style>'
                    
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">'
                    
                    for mgr in managers:
                        html += f'''
                        <div class="division-card o_kanban_record" style="border-radius: 5px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div><i class="fa fa-user-tie"></i> {mgr}</div>
                        </div>
                        '''
                    
                    for sup in supervisors:
                        html += f'''
                        <div class="division-card o_kanban_record" style="border-radius: 5px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div><i class="fa fa-user"></i> {sup}</div>
                        </div>
                        '''
                    
                    for st in staff:
                        html += f'''
                        <div class="division-card o_kanban_record" style="border-radius: 5px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div><i class="fa fa-user"></i> {st}</div>
                        </div>
                        '''
                    
                    html += '</div>'
                    
                    record.division_users = html if (managers or supervisors or staff) else '<div class="alert alert-warning">No users in this division</div>'
                else:
                    record.division_users = ''
            else:
                record.division_users = ''

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            # Auto-fill department and job from hr.employee
            employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            if employee:
                if employee.department_id:
                    self.department_id = employee.department_id.id
                if employee.job_id:
                    self.job_id = employee.job_id.id
                return
            
            # Fallback to existing assignment
            existing_assignment = self.search([
                ('user_id', '=', self.user_id.id),
                ('active', '=', True)
            ], limit=1)
            
            if existing_assignment:
                if existing_assignment.department_id:
                    self.department_id = existing_assignment.department_id.id
                if existing_assignment.job_id:
                    self.job_id = existing_assignment.job_id.id

    @api.constrains('job_id', 'department_id')
    def _check_assignment_rules(self):
        """Validate data only - NOT for permission checks"""
        for record in self:
            # Check if department is required (not BOD)
            if record.job_id and record.job_id.name and 'bod' not in record.job_id.name.lower() and not record.department_id:
                raise ValidationError("Department is required for non-BOD positions.")

    def write(self, vals):
        # Permission checks BEFORE write
        current_user = self.env.user
        if not current_user.has_group('peepl_weekly_report.group_peepl_bod'):
            if current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                # Supervisor: only same division
                supervisor_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                if supervisor_assignment and supervisor_assignment.division_id:
                    if vals.get('division_id') and vals['division_id'] != supervisor_assignment.division_id.id:
                        raise ValidationError("Supervisor can only assign users to their own division.")
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                manager_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                if vals.get('job_id'):
                    job = self.env['hr.job'].browse(vals['job_id'])
                    if job.name and 'manager' in job.name.lower():
                        raise ValidationError("Manager cannot assign other Manager positions.")
                if manager_assignment and vals.get('department_id') and vals['department_id'] != manager_assignment.department_id.id:
                    raise ValidationError("Manager can only assign users to their own department.")
            else:
                raise ValidationError("You don't have permission to modify assignments.")
        
        result = super(PeeplUserAssignment, self).write(vals)
        # Trigger PIC overview update with sudo
        if 'user_id' in vals or 'job_id' in vals or 'department_id' in vals or 'active' in vals:
            self.sudo()._update_pic_overview()
        return result

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        # Permission checks BEFORE create
        current_user = self.env.user
        if not current_user.has_group('peepl_weekly_report.group_peepl_bod'):
            if current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                # Supervisor: only same division
                supervisor_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                for vals in vals_list:
                    if supervisor_assignment and supervisor_assignment.division_id:
                        if vals.get('division_id') and vals['division_id'] != supervisor_assignment.division_id.id:
                            raise ValidationError("Supervisor can only assign users to their own division.")
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager/Supervisor checks
                manager_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                for vals in vals_list:
                    if vals.get('job_id'):
                        job = self.env['hr.job'].browse(vals['job_id'])
                        if job.name and 'manager' in job.name.lower():
                            raise ValidationError("Manager cannot assign other Manager positions.")
                    if manager_assignment and vals.get('department_id') and vals['department_id'] != manager_assignment.department_id.id:
                        raise ValidationError("Manager can only assign users to their own department.")
            else:
                raise ValidationError("You don't have permission to assign users.")
        
        for vals in vals_list:
            # Auto-set department and job from user's HR employee
            if vals.get('user_id'):
                employee = self.env['hr.employee'].sudo().search([('user_id', '=', vals['user_id'])], limit=1)
                if employee:
                    if employee.department_id and not vals.get('department_id'):
                        vals['department_id'] = employee.department_id.id
                    if employee.job_id and not vals.get('job_id'):
                        vals['job_id'] = employee.job_id.id
                
                # Handle BOD positions
                if vals.get('job_id'):
                    job = self.env['hr.job'].browse(vals['job_id'])
                    if job.name and 'bod' in job.name.lower():
                        vals['department_id'] = False
        
        result = super(PeeplUserAssignment, self).create(vals_list)
        self.sudo()._update_pic_overview()
        return result

    def _update_pic_overview(self):
        """Update PIC overview with sudo to bypass permission issues"""
        self.env['peepl.pic.overview'].sudo().update_all_stats()

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

    @api.depends_context('uid')
    def _compute_allowed_departments(self):
        for record in self:
            current_user = self.env.user
            
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                record.allowed_department_ids = self.env['hr.department'].sudo().search([])
            elif current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                # Supervisor: same department only
                supervisor_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                if supervisor_assignment and supervisor_assignment.department_id:
                    record.allowed_department_ids = supervisor_assignment.department_id
                else:
                    record.allowed_department_ids = self.env['hr.department']
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                manager_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                if manager_assignment and manager_assignment.department_id:
                    record.allowed_department_ids = manager_assignment.department_id
                else:
                    record.allowed_department_ids = self.env['hr.department']
            else:
                record.allowed_department_ids = self.env['hr.department']

    @api.depends_context('uid')
    def _compute_allowed_jobs(self):
        for record in self:
            current_user = self.env.user
            
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                record.allowed_job_ids = self.env['hr.job'].sudo().search([])
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager') or current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                record.allowed_job_ids = self.env['hr.job'].sudo().search([('name', 'not ilike', 'manager'), ('name', 'not ilike', 'bod')])
            else:
                record.allowed_job_ids = self.env['hr.job']

    @api.depends_context('uid')
    def _compute_allowed_users(self):
        import logging
        _logger = logging.getLogger(__name__)
        
        for record in self:
            current_user = self.env.user
            assigned_user_ids = self.sudo().search([('active', '=', True)]).mapped('user_id').ids
            
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                record.allowed_user_ids = self.env['res.users'].sudo().search([('id', 'not in', assigned_user_ids)])
            elif current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                # Supervisor: only users from same department (not division)
                try:
                    supervisor_assignment = self.sudo().search([('user_id', '=', current_user.id), ('active', '=', True)], limit=1)
                    if supervisor_assignment and supervisor_assignment.department_id:
                        dept_employees = self.env['hr.employee'].sudo().search([
                            ('department_id', '=', supervisor_assignment.department_id.id),
                            ('user_id', '!=', False),
                            ('user_id', 'not in', assigned_user_ids)
                        ])
                        record.allowed_user_ids = dept_employees.mapped('user_id')
                    else:
                        record.allowed_user_ids = self.env['res.users']
                except Exception as e:
                    _logger.exception("Error computing allowed users for supervisor: %s", e)
                    record.allowed_user_ids = self.env['res.users']
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                try:
                    manager_employee = self.env['hr.employee'].sudo().search([('user_id', '=', current_user.id)], limit=1)
                    if manager_employee and manager_employee.department_id:
                        # Optimized: get all employees from same department at once
                        dept_employees = self.env['hr.employee'].sudo().search([
                            ('department_id', '=', manager_employee.department_id.id),
                            ('user_id', '!=', False),
                            ('user_id', 'not in', assigned_user_ids)
                        ])
                        record.allowed_user_ids = dept_employees.mapped('user_id')
                    else:
                        record.allowed_user_ids = self.env['res.users']
                except Exception as e:
                    _logger.exception("Error computing allowed users for manager: %s", e)
                    record.allowed_user_ids = self.env['res.users']
            else:
                if current_user.id not in assigned_user_ids:
                    record.allowed_user_ids = current_user
                else:
                    record.allowed_user_ids = self.env['res.users']