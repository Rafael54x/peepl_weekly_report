# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class PeeplWeeklyReport(models.Model):
    _name = 'peepl.weekly.report'
    _description = 'Peepl Weekly Report'
    _inherit = ['peepl.field.template.mixin']
    _rec_name = 'project_task'
    _order = 'name asc'
    
    @api.model
    def _setup_complete(self):
        """Force setup completion for dynamic fields"""
        super()._setup_complete()
        # Refresh field definitions
        self._fields.clear()
        self._setup_fields()
        return True

    name = fields.Integer(string='No', required=True, readonly=True, copy=False, default=lambda self: self._get_next_number())
    display_number = fields.Integer(string='No', compute='_compute_display_number', store=False)
    
    @api.depends('name', 'department_id')
    def _compute_display_number(self):
        """Compute display number based on user role"""
        current_user = self.env.user
        
        # BOD: show actual number
        if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
            for record in self:
                record.display_number = record.name
        else:
            # Manager/Staff: show sequential number per department
            assignment = self.env['peepl.user.assignment'].search([
                ('user_id', '=', current_user.id),
                ('active', '=', True)
            ], limit=1)
            
            if assignment and assignment.department_id:
                # Get all reports from same department, ordered by name
                dept_reports = self.search([
                    ('department_id', '=', assignment.department_id.id)
                ], order='name asc')
                
                # Create mapping of actual number to display number
                number_map = {report.id: idx + 1 for idx, report in enumerate(dept_reports)}
                
                for record in self:
                    record.display_number = number_map.get(record.id, record.name)
            else:
                for record in self:
                    record.display_number = record.name
    
    def copy(self, default=None):
        if default is None:
            default = {}
        # Pastikan nomor unik saat duplikat
        new_number = self._get_next_number()
        while self.search([('name', '=', new_number)]):
            new_number += 1
        default['name'] = new_number
        return super().copy(default)
    pic_id = fields.Many2one('res.users', string='PIC', required=True)
    allowed_pic_ids = fields.Many2many('res.users', compute='_compute_allowed_pic_ids')
    allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_users')
    department_filter_ids = fields.Many2many('hr.department', string='Department Filter', compute='_compute_department_filter')
    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department', store=True)
    client_id = fields.Many2one('res.partner', string='Client', required=True)
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
    ], string='Status', required=True, default='not_started', compute='_compute_status', store=True, readonly=False, group_expand='_group_expand_status')
    progress = fields.Integer(string='Progress (%)', default=0)
    notes = fields.Html(string='Notes')
    notes_decoded = fields.Html(string='Notes Decoded', compute='_compute_notes_decoded')
    
    @api.depends('notes')
    def _compute_notes_decoded(self):
        import html
        for record in self:
            if record.notes:
                # Decode HTML entities
                decoded = html.unescape(record.notes)
                # Clean up editor attributes
                import re
                decoded = re.sub(r'data-oe-version="[^"]*"', '', decoded)
                decoded = re.sub(r'data-last-history-steps="[^"]*"', '', decoded)
                record.notes_decoded = decoded
            else:
                record.notes_decoded = ''

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
        # Cari nomor yang hilang terlebih dahulu - bypass record rules untuk dapat nomor global
        existing_numbers = self.sudo().search([]).mapped('name')
        if not existing_numbers:
            return 1
        
        # Cari gap/nomor yang hilang
        existing_numbers.sort()
        for i in range(1, max(existing_numbers) + 1):
            if i not in existing_numbers:
                return i
        
        # Jika tidak ada gap, gunakan nomor berikutnya
        next_num = max(existing_numbers) + 1
        # Pastikan nomor unik
        while next_num in existing_numbers:
            next_num += 1
        return next_num

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
        if self.status == 'completed':
            self.progress = 100
        elif self.deadline and self.deadline < date.today() and self.status != 'overdue' and self.status != 'completed':
            self.status = 'overdue'
        # Prevent changing from overdue to other status except completed
        if self._origin.status == 'overdue' and self.status != 'overdue' and self.status != 'completed':
            self.status = 'overdue'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._update_pic_overview()
        return records

    def write(self, vals):
        # Prevent changing from overdue to other status except completed
        if 'status' in vals:
            for record in self:
                if record.status == 'overdue' and vals['status'] != 'completed':
                    vals['status'] = 'overdue'
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
    def _compute_department_filter(self):
        for record in self:
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                # BOD: all departments
                record.department_filter_ids = self.env['hr.department'].search([])
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager: only their department
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.department_id:
                    record.department_filter_ids = user_assignment.department_id
                else:
                    record.department_filter_ids = self.env['hr.department']
            else:
                # Staff: no department filter needed
                record.department_filter_ids = self.env['hr.department']

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

    @api.model
    def _group_expand_status(self, statuses, domain):
        """Expand all status groups in kanban view"""
        return [key for key, _ in self._fields['status'].selection]

    @api.depends('create_uid')
    def _compute_allowed_pic_ids(self):
        for record in self:
            # Get all assigned users from user assignment
            assigned_users = self.env['peepl.user.assignment'].search([('active', '=', True)]).mapped('user_id')
            record.allowed_pic_ids = assigned_users



    def action_open_form(self):
        """Open form view for this record"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Weekly Report - {self.project_task}',
            'res_model': 'peepl.weekly.report',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
