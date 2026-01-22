# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    report_email = fields.Char(string='Report Email', config_parameter='peepl_weekly_report.report_email')
    auto_send = fields.Boolean(string='Auto Send Report', config_parameter='peepl_weekly_report.auto_send')
    current_user_role = fields.Char(string='Your Access Level', compute='_compute_current_user_role', readonly=True)

    def _compute_current_user_role(self):
        for record in self:
            user = self.env.user
            if user.has_group('peepl_weekly_report.group_peepl_bod'):
                record.current_user_role = 'BOD'
            elif user.has_group('peepl_weekly_report.group_peepl_manager'):
                record.current_user_role = 'Manager'
            elif user.has_group('peepl_weekly_report.group_peepl_staff'):
                record.current_user_role = 'Staff'
            else:
                record.current_user_role = 'No Access'

    @api.model
    def get_current_user_id(self):
        return self.env.user.id
