# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplDepartmentDeleteWizard(models.TransientModel):
    _name = 'peepl.department.delete.wizard'
    _description = 'Department Delete Confirmation Wizard'

    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    department_name = fields.Char(string='Department Name', readonly=True)
    employee_count = fields.Integer(string='Employees', readonly=True)
    report_count = fields.Integer(string='Reports', readonly=True)

    def action_confirm_delete(self):
        self.ensure_one()
        if self.department_id:
            self.department_id.sudo().unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': f'Department "{self.department_name}" deleted successfully',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
