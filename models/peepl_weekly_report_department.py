from odoo import models, fields, api, tools
from odoo.exceptions import UserError


class PeeplWeeklyReportDepartment(models.Model):
    _name = 'peepl.weekly.report.department'
    _description = 'Weekly Report Department'
    _rec_name = 'department_id'
    _auto = False

    department_id = fields.Many2one('hr.department', string='Department')
    manager_id = fields.Many2one('hr.employee', string='Manager')
    company_id = fields.Many2one('res.company', string='Company')
    color = fields.Integer(string='Color')
    total_reports = fields.Integer(string='Total Reports')
    status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status')
    field_template_ids = fields.One2many('peepl.field.template', 'department_id', string='Field Templates')
    user_assignment_ids = fields.One2many('peepl.user.assignment', 'department_id', string='User Assignments')
    division_ids = fields.One2many('peepl.division', 'department_id', string='Divisions')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    d.id,
                    d.id as department_id,
                    d.manager_id,
                    d.company_id,
                    d.color,
                    COALESCE(COUNT(wr.id), 0) as total_reports,
                    CASE 
                        WHEN COUNT(wr.id) = 0 THEN 'draft'
                        WHEN COUNT(CASE WHEN wr.status != 'completed' THEN 1 END) > 0 THEN 'draft'
                        ELSE 'done'
                    END as status
                FROM hr_department d
                LEFT JOIN peepl_weekly_report wr ON wr.department_id = d.id
                GROUP BY d.id, d.manager_id, d.company_id, d.color
            )
        """ % self._table)

    def write(self, vals):
        """Override write to handle One2many fields properly"""
        self.ensure_one()
        
        # Handle field_template_ids changes
        if 'field_template_ids' in vals:
            for command in vals['field_template_ids']:
                if command[0] == 2:  # Delete
                    self.env['peepl.field.template'].browse(command[1]).unlink()
                elif command[0] == 1:  # Update
                    self.env['peepl.field.template'].browse(command[1]).write(command[2])
                elif command[0] == 0:  # Create
                    command[2]['department_id'] = self.department_id.id
                    self.env['peepl.field.template'].create(command[2])
        
        # Handle user_assignment_ids changes
        if 'user_assignment_ids' in vals:
            for command in vals['user_assignment_ids']:
                if command[0] == 2:  # Delete
                    self.env['peepl.user.assignment'].browse(command[1]).unlink()
                elif command[0] == 1:  # Update
                    self.env['peepl.user.assignment'].browse(command[1]).write(command[2])
                elif command[0] == 0:  # Create
                    create_vals = command[2].copy()
                    create_vals['department_id'] = self.department_id.id
                    # Remove invalid fields
                    create_vals.pop('user_assignment_ids', None)
                    create_vals.pop('field_template_ids', None)
                    create_vals.pop('division_ids', None)
                    self.env['peepl.user.assignment'].create(create_vals)
        
        # Handle division_ids changes
        if 'division_ids' in vals:
            for command in vals['division_ids']:
                if command[0] == 2:  # Delete
                    self.env['peepl.division'].browse(command[1]).unlink()
                elif command[0] == 1:  # Update
                    self.env['peepl.division'].browse(command[1]).write(command[2])
                elif command[0] == 0:  # Create
                    create_vals = command[2].copy()
                    create_vals['department_id'] = self.department_id.id
                    # Remove invalid fields
                    create_vals.pop('user_assignment_ids', None)
                    create_vals.pop('field_template_ids', None)
                    create_vals.pop('division_ids', None)
                    self.env['peepl.division'].create(create_vals)
        
        return True

    def action_open_reports(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'weekly_report_custom_view',
            'name': f'Weekly Reports - {self.department_id.name}',
            'context': {
                'dept_filter': self.department_id.id,
                'dept_name': self.department_id.name,
            },
        }

    def action_open_configuration(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Department Configuration',
            'res_model': 'peepl.weekly.report.department',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def create(self, vals_list):
        # Redirect to hr.department create
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Department',
            'res_model': 'hr.department',
            'view_mode': 'form',
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'message': 'Please refresh the page to see updated data.',
                'sticky': False,
            }
        }

    def action_delete_department(self):
        self.ensure_one()
        department = self.env['hr.department'].sudo().browse(self.department_id.id)
        if department.exists():
            employee_count = self.env['hr.employee'].sudo().search_count([('department_id', '=', department.id)])
            report_count = self.env['peepl.weekly.report'].sudo().search_count([('department_id', '=', department.id)])
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirm Delete Department',
                'res_model': 'peepl.department.delete.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_department_id': department.id,
                    'default_department_name': department.name,
                    'default_employee_count': employee_count,
                    'default_report_count': report_count,
                }
            }
        return {'type': 'ir.actions.act_window_close'}

    def open_record(self):
        """Override default open to show weekly reports list"""
        self.ensure_one()
        return self.action_open_reports()