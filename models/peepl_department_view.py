from odoo import models, fields, api, tools


class PeeplDepartmentView(models.Model):
    _name = 'peepl.department.view'
    _description = 'Department View for Weekly Reports'
    _auto = False

    name = fields.Char(string='Department Name')
    manager_id = fields.Many2one('hr.employee', string='Manager')
    weekly_report_count = fields.Integer(string='Reports')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    d.id,
                    d.name,
                    d.manager_id,
                    COUNT(wr.id) as weekly_report_count
                FROM hr_department d
                LEFT JOIN peepl_weekly_report wr ON wr.department_id = d.id
                WHERE wr.id IS NOT NULL
                GROUP BY d.id, d.name, d.manager_id
            )
        """ % self._table)