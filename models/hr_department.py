from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    weekly_report_ids = fields.One2many(
        'peepl.weekly.report',
        'department_id',
        string='Weekly Reports'
    )

    weekly_report_count = fields.Integer(
        string='Report Count',
        compute='_compute_weekly_report_count'
    )

    user_assignment_ids = fields.One2many(
        'peepl.user.assignment',
        'department_id',
        string='User Assignments'
    )

    @api.depends('weekly_report_ids')
    def _compute_weekly_report_count(self):
        for dept in self:
            dept.weekly_report_count = len(dept.weekly_report_ids)