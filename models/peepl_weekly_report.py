# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class PeeplWeeklyReport(models.Model):
    _name = 'peepl.weekly.report'
    _description = 'Peepl Weekly Report'
    _rec_name = 'project_task'

    name = fields.Integer(string='No', required=True, readonly=True, copy=False, default=lambda self: self._get_next_number())
    pic_id = fields.Many2one('res.users', string='PIC', required=True)
    allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_users')
    department_id = fields.Many2one('peepl.department', string='Department', compute='_compute_department', store=True)
    client_id = fields.Many2one('peepl.client', string='Client', required=True)
    request_form = fields.Char(string='Request Form')
    project_task = fields.Char(string='Project / Task', required=True)
    deadline = fields.Date(string='Deadline')
    status = fields.Selection([
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
        ('not_started', 'Not Started'),
        ('delayed', 'Delayed'),
        ('plan', 'Plan'),
        ('overdue', 'Overdue'),
    ], string='Status', required=True, compute='_compute_status', store=True, readonly=False)
    progress = fields.Integer(string='Progress (%)', default=0)
    notes = fields.Html(string='Notes')

    @api.constrains('pic_id')
    def _check_pic_department(self):
        for record in self:
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager: can only assign to users in same department
                manager_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                
                pic_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', record.pic_id.id),
                    ('active', '=', True)
                ], limit=1)
                
                if manager_assignment and pic_assignment:
                    if manager_assignment.department_id != pic_assignment.department_id:
                        raise ValidationError(f"Manager can only assign tasks to users in the same department ({manager_assignment.department_id.name}).")
            elif current_user.has_group('peepl_weekly_report.group_peepl_staff'):
                # Staff: can only assign to themselves
                if record.pic_id != current_user:
                    raise ValidationError("Staff can only assign tasks to themselves.")
    def _get_next_number(self):
        last_record = self.search([], order='name desc', limit=1)
        return (last_record.name + 1) if last_record else 1

    def action_save_close(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': 'Saved successfully',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


    @api.depends('pic_id')
    def _compute_department(self):
        for record in self:
            if record.pic_id:
                assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', record.pic_id.id),
                    ('active', '=', True)
                ], limit=1)
                record.department_id = assignment.department_id.id if assignment else False
            else:
                record.department_id = False

    @api.depends('deadline', 'status')
    def _compute_status(self):
        today = date.today()
        for record in self:
            # Auto-set to overdue if deadline passed and not completed
            if (record.deadline and record.deadline < today and 
                record.status != 'completed' and record.status != 'overdue'):
                record.status = 'overdue'

    @api.model
    def update_overdue_status(self):
        """Cron job to update overdue status daily"""
        today = date.today()
        overdue_reports = self.search([
            ('deadline', '<', today),
            ('status', '!=', 'completed'),
            ('status', '!=', 'overdue')
        ])
        overdue_reports.write({'status': 'overdue'})
        return len(overdue_reports)

    @api.onchange('status')
    def _onchange_status(self):
        if self.deadline and self.deadline < date.today() and self.status != 'overdue' and self.status != 'completed':
            self.status = 'overdue'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._update_pic_overview()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(field in vals for field in ['progress', 'pic_id', 'status']):
            self._update_pic_overview()
        return result

    def unlink(self):
        result = super().unlink()
        self._update_pic_overview()
        return result

    def _update_pic_overview(self):
        self.env['peepl.pic.overview'].update_all_stats()

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError("Progress must be between 0 and 100.")

    @api.depends('create_uid')
    def _compute_allowed_users(self):
        for record in self:
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                # BOD: all users
                record.allowed_user_ids = self.env['res.users'].search([])
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
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
                    record.allowed_user_ids = dept_assignments.mapped('user_id')
                else:
                    record.allowed_user_ids = self.env['res.users']
            else:
                # Staff: only themselves
                record.allowed_user_ids = current_user
