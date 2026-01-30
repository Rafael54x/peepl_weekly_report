from odoo import models, fields, api, tools


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

    def open_record(self):
        """Override default open to show weekly reports list"""
        self.ensure_one()
        return self.action_open_reports()