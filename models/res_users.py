# -*- coding: utf-8 -*-

from odoo import models, api, fields

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    weekly_report_access = fields.Selection([
        ('none', 'No Access'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('bod', 'BOD')
    ], string='Weekly Report Access', compute='_compute_weekly_access', inverse='_set_weekly_access')
    
    def _compute_weekly_access(self):
        for user in self:
            if user.has_group('peepl_weekly_report.group_peepl_bod'):
                user.weekly_report_access = 'bod'
            elif user.has_group('peepl_weekly_report.group_peepl_manager'):
                user.weekly_report_access = 'manager'
            elif user.has_group('peepl_weekly_report.group_peepl_staff'):
                user.weekly_report_access = 'staff'
            else:
                user.weekly_report_access = 'none'
    
    def _set_weekly_access(self):
        for user in self:
            # Remove all groups
            groups_to_remove = [
                'peepl_weekly_report.group_peepl_staff',
                'peepl_weekly_report.group_peepl_manager', 
                'peepl_weekly_report.group_peepl_bod'
            ]
            for group_xml_id in groups_to_remove:
                try:
                    group = self.env.ref(group_xml_id)
                    user.write({'groups_id': [(3, group.id)]})
                except:
                    pass
            
            # Add selected group
            if user.weekly_report_access != 'none':
                group_map = {
                    'staff': 'peepl_weekly_report.group_peepl_staff',
                    'manager': 'peepl_weekly_report.group_peepl_manager',
                    'bod': 'peepl_weekly_report.group_peepl_bod'
                }
                try:
                    group = self.env.ref(group_map[user.weekly_report_access])
                    user.write({'groups_id': [(4, group.id)]})
                except:
                    pass

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        # Check if this is called from weekly report PIC field
        if self.env.context.get('from_weekly_report_pic'):
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager: only users from same department
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if user_assignment:
                    dept_assignments = self.env['peepl.user.assignment'].search([
                        ('department_id', '=', user_assignment.department_id.id),
                        ('active', '=', True)
                    ])
                    allowed_user_ids = dept_assignments.mapped('user_id').ids
                    if allowed_user_ids:
                        domain = (domain or []) + [('id', 'in', allowed_user_ids)]
                    else:
                        domain = (domain or []) + [('id', '=', False)]  # No users if no assignments
        
        return super().name_search(name=name, domain=domain, operator=operator, limit=limit)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        # Also filter search_read for Many2one field
        if self.env.context.get('from_weekly_report_pic'):
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if user_assignment:
                    dept_assignments = self.env['peepl.user.assignment'].search([
                        ('department_id', '=', user_assignment.department_id.id),
                        ('active', '=', True)
                    ])
                    allowed_user_ids = dept_assignments.mapped('user_id').ids
                    if allowed_user_ids:
                        domain = (domain or []) + [('id', 'in', allowed_user_ids)]
                    else:
                        domain = (domain or []) + [('id', '=', False)]
        
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)