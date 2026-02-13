# -*- coding: utf-8 -*-

from odoo import models, api, fields

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # Computed field for record rules
    weekly_report_department_ids = fields.Many2many(
        'hr.department',
        compute='_compute_weekly_department_ids',
        string='Weekly Report Departments'
    )
    weekly_report_division_ids = fields.Many2many(
        'peepl.division',
        compute='_compute_weekly_division_ids',
        string='Weekly Report Divisions'
    )
    user_assignment_ids = fields.One2many('peepl.user.assignment', 'user_id', string='User Assignments')
    
    @api.depends_context('uid')
    def _compute_weekly_department_ids(self):
        """Compute user's departments for record rules"""
        for user in self:
            assignments = self.env['peepl.user.assignment'].sudo().search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ])
            user.weekly_report_department_ids = assignments.mapped('department_id')
    
    @api.depends_context('uid')
    def _compute_weekly_division_ids(self):
        """Compute user's divisions for record rules"""
        for user in self:
            assignments = self.env['peepl.user.assignment'].sudo().search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ])
            user.weekly_report_division_ids = assignments.mapped('division_id')

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        # Filter by department from department configuration
        if self.env.context.get('filter_department_id'):
            dept_id = self.env.context.get('filter_department_id')
            assigned_user_ids = self.env['peepl.user.assignment'].sudo().search([('active', '=', True)]).mapped('user_id').ids
            dept_employees = self.env['hr.employee'].sudo().search([
                ('department_id', '=', dept_id),
                ('user_id', '!=', False),
                ('user_id', 'not in', assigned_user_ids)
            ])
            allowed_user_ids = dept_employees.mapped('user_id').ids
            domain = (domain or []) + [('id', 'in', allowed_user_ids or [False])]
        elif self.env.context.get('from_weekly_report_pic'):
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id), ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.division_id:
                    division_assignments = self.env['peepl.user.assignment'].search([
                        ('division_id', '=', user_assignment.division_id.id), ('active', '=', True)
                    ])
                    allowed_user_ids = division_assignments.mapped('user_id').ids
                    domain = (domain or []) + [('id', 'in', allowed_user_ids or [False])]
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id), ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.department_id:
                    dept_assignments = self.env['peepl.user.assignment'].search([
                        ('department_id', '=', user_assignment.department_id.id), ('active', '=', True)
                    ])
                    allowed_user_ids = dept_assignments.mapped('user_id').ids
                    domain = (domain or []) + [('id', 'in', allowed_user_ids or [False])]
        return super().name_search(name=name, domain=domain, operator=operator, limit=limit)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('from_weekly_report_pic'):
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_supervisor'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id), ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.division_id:
                    division_assignments = self.env['peepl.user.assignment'].search([
                        ('division_id', '=', user_assignment.division_id.id), ('active', '=', True)
                    ])
                    allowed_user_ids = division_assignments.mapped('user_id').ids
                    domain = (domain or []) + [('id', 'in', allowed_user_ids or [False])]
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id), ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.department_id:
                    dept_assignments = self.env['peepl.user.assignment'].search([
                        ('department_id', '=', user_assignment.department_id.id), ('active', '=', True)
                    ])
                    allowed_user_ids = dept_assignments.mapped('user_id').ids
                    domain = (domain or []) + [('id', 'in', allowed_user_ids or [False])]
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)