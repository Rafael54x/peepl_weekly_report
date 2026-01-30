# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplPicOverview(models.Model):
    _name = 'peepl.pic.overview'
    _description = 'PIC Overview'

    user_id = fields.Many2one('res.users', string='User', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    position = fields.Char(string='Employment Types')
    total_tasks = fields.Integer(string='Total Tasks')
    completed = fields.Integer(string='Completed')
    in_progress = fields.Integer(string='In Progress')
    not_started = fields.Integer(string='Not Started')
    delayed = fields.Integer(string='Delayed')
    plan = fields.Integer(string='Plan')
    overdue = fields.Integer(string='Overdue')
    avg_progress = fields.Float(string='Avg Progress (%)')

    @api.model
    def update_all_stats(self):
        """Update all PIC overview statistics"""
        # Get all users with weekly reports
        users_with_reports = self.env['peepl.weekly.report'].search([]).mapped('pic_id')
        
        # Delete existing records
        self.search([]).unlink()
        
        # Create new records
        for user in users_with_reports:
            assignment = self.env['peepl.user.assignment'].search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ], limit=1)
            
            reports = self.env['peepl.weekly.report'].search([('pic_id', '=', user.id)])
            
            self.create({
                'user_id': user.id,
                'department_id': assignment.department_id.id if assignment and assignment.department_id else False,
                'position': assignment.position_id.name if assignment and assignment.position_id else 'No Assignment',
                'total_tasks': len(reports),
                'completed': len(reports.filtered(lambda r: r.status == 'completed')),
                'in_progress': len(reports.filtered(lambda r: r.status == 'in_progress')),
                'not_started': len(reports.filtered(lambda r: r.status == 'not_started')),
                'delayed': len(reports.filtered(lambda r: r.status == 'delayed')),
                'plan': len(reports.filtered(lambda r: r.status == 'plan')),
                'overdue': len(reports.filtered(lambda r: r.status == 'overdue')),
                'avg_progress': sum(reports.mapped('progress')) / len(reports) if reports else 0.0,
            })

    def update_overview(self):
        self.update_all_stats()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }