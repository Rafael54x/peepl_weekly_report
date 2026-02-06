# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplPicOverview(models.Model):
    _name = 'peepl.pic.overview'
    _description = 'PIC Overview'

    user_id = fields.Many2one('res.users', string='User', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    job_position = fields.Char(string='Job Position')
    total_tasks = fields.Integer(string='Total Tasks')
    completed = fields.Integer(string='Completed')
    in_progress = fields.Integer(string='In Progress')
    not_started = fields.Integer(string='Not Started')
    delayed = fields.Integer(string='Delayed')
    plan = fields.Integer(string='Plan')
    overdue = fields.Integer(string='Overdue')
    avg_progress = fields.Float(string='Avg Progress (%)')

    @api.model
    def _migrate_position_to_job_position(self):
        """Migrate old position field to job_position"""
        try:
            # Drop old column if exists
            self.env.cr.execute("ALTER TABLE peepl_pic_overview DROP COLUMN IF EXISTS position")
            # Clear all existing records
            self.env.cr.execute("DELETE FROM peepl_pic_overview")
            self.env.cr.commit()
        except Exception as e:
            print(f"Migration error: {e}")
    
    @api.model
    def update_all_stats(self):
        """Update all PIC overview statistics"""
        users_with_reports = self.env['peepl.weekly.report'].search([]).mapped('pic_id')
        
        all_overview_records = self.search([])
        users_to_keep = set(users_with_reports.ids)
        records_to_delete = all_overview_records.filtered(lambda r: r.user_id.id not in users_to_keep)
        records_to_delete.unlink()
        
        for user in users_with_reports:
            assignment = self.env['peepl.user.assignment'].sudo().search([
                ('user_id', '=', user.id),
                ('active', '=', True)
            ], limit=1)
            
            reports = self.env['peepl.weekly.report'].search([('pic_id', '=', user.id)])
            existing = self.search([('user_id', '=', user.id)], limit=1)
            
            vals = {
                'user_id': user.id,
                'department_id': assignment.department_id.id if assignment and assignment.department_id else False,
                'job_position': assignment.job_id.name if assignment and assignment.job_id else 'No Position',
                'total_tasks': len(reports),
                'completed': len(reports.filtered(lambda r: r.status == 'completed')),
                'in_progress': len(reports.filtered(lambda r: r.status == 'in_progress')),
                'not_started': len(reports.filtered(lambda r: r.status == 'not_started')),
                'delayed': len(reports.filtered(lambda r: r.status == 'delayed')),
                'plan': len(reports.filtered(lambda r: r.status == 'plan')),
                'overdue': len(reports.filtered(lambda r: r.status == 'overdue')),
                'avg_progress': sum(reports.mapped('progress')) / len(reports) if reports else 0.0,
            }
            
            if existing:
                existing.write(vals)
            else:
                self.create(vals)

    def update_overview(self):
        self.update_all_stats()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }