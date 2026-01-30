# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml.builder import E

class PeeplWeeklyReportBod(models.Model):
    _name = 'peepl.weekly.report.bod'
    _description = 'BOD Weekly Report View'
    _inherit = ['peepl.weekly.report', 'peepl.field.template.mixin']  # Inherit mixin too
    _table = 'peepl_weekly_report'  # Use same table
    _auto = False  # Don't create separate table
    
    def _get_view(self, view_id=None, view_type='form', **options):
        """Override to filter fields by department context"""
        arch, view = super()._get_view(view_id, view_type, **options)
        
        # Only filter if we have department context from BOD department click
        dept_filter = self.env.context.get('default_department_id')
        if not dept_filter:
            return arch, view
            
        # Get all field templates
        all_templates = self.env['peepl.field.template'].search([('active', '=', True)])
        dept_templates = all_templates.filtered(lambda t: t.department_id.id == dept_filter)
        
        # Hide fields that don't belong to clicked department
        try:
            for template in all_templates:
                fname = template._column_name()
                field_nodes = arch.findall(f'.//field[@name="{fname}"]')
                for field_node in field_nodes:
                    if template not in dept_templates:
                        field_node.set('column_invisible', '1')
        except Exception:
            pass
            
        return arch, view