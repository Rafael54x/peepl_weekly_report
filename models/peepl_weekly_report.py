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
    project_task = fields.Text(string='Project / Task', required=True)
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
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                continue
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
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
            'tag': 'history_back',
        }

    def action_back(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'history_back',
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
            # Skip if manually set to completed
            if record.status == 'completed':
                continue
            
            # Auto-set to overdue if deadline passed and not completed
            if record.deadline and record.deadline < today and record.status != 'completed':
                record.status = 'overdue'
            # Auto-change from overdue to delayed if deadline is extended to future
            elif record._origin.status == 'overdue' and record.deadline and record.deadline >= today:
                record.status = 'delayed'

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
        # Prevent changing from overdue to other status except completed and delayed
        if self._origin.status == 'overdue' and self.status not in ['overdue', 'completed', 'delayed']:
            self.status = 'overdue'

    @api.onchange('deadline')
    def _onchange_deadline(self):
        # Auto-change from overdue to delayed if new deadline is after today
        if self.status == 'overdue' and self.deadline:
            if self.deadline >= date.today():
                self.status = 'delayed'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._update_pic_overview()
        return records

    def write(self, vals):
        # If deadline is changed when status is overdue, check if new deadline is after old deadline
        if 'deadline' in vals:
            for record in self:
                if record.status == 'overdue' and vals['deadline'] and record.deadline:
                    # Convert string to date if needed
                    new_deadline = vals['deadline'] if isinstance(vals['deadline'], date) else fields.Date.from_string(vals['deadline'])
                    if new_deadline > record.deadline:
                        vals['status'] = 'delayed'
        
        # Prevent changing from overdue to other status except completed or delayed
        if 'status' in vals:
            for record in self:
                if record.status == 'overdue' and vals['status'] not in ['completed', 'delayed']:
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
        """Update PIC overview"""
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
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                # BOD: all users
                assigned_users = self.env['peepl.user.assignment'].search([('active', '=', True)]).mapped('user_id')
                record.allowed_pic_ids = assigned_users
            elif current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                # Manager: only users from same department
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if user_assignment and user_assignment.department_id:
                    dept_assignments = self.env['peepl.user.assignment'].search([
                        ('department_id', '=', user_assignment.department_id.id),
                        ('active', '=', True)
                    ])
                    record.allowed_pic_ids = dept_assignments.mapped('user_id')
                else:
                    record.allowed_pic_ids = self.env['res.users']
            else:
                # Staff: only themselves
                record.allowed_pic_ids = current_user

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Override to inject department-specific fields in list and form view"""
        result = super().fields_view_get(view_id, view_type, toolbar, submenu)
        
        # Debug logging
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"fields_view_get called: view_type={view_type}, context={self.env.context}")
        
        if view_type in ['tree', 'form']:
            try:
                dept_id = self.env.context.get('dept_filter')
                _logger.info(f"Department filter: {dept_id}")
                
                if dept_id:
                    templates = self.env['peepl.field.template'].sudo().search([
                        ('department_id', '=', dept_id),
                        ('active', '=', True)
                    ], order='sequence')
                    _logger.info(f"Found {len(templates)} templates for dept {dept_id}")
                    
                    if templates:
                        from lxml import etree
                        doc = etree.fromstring(result['arch'])
                        
                        if view_type == 'form':
                            # Try multiple approaches to inject fields
                            notebook = doc.xpath('//notebook')
                            if notebook:
                                _logger.info("Found notebook, adding page")
                                page_elem = etree.Element('page')
                                page_elem.set('string', f'{self.env["hr.department"].browse(dept_id).name} Fields')
                                
                                group_elem = etree.Element('group')
                                for template in templates:
                                    fname = template._column_name()
                                    _logger.info(f"Adding field: {fname}")
                                    field_elem = etree.Element('field')
                                    field_elem.set('name', fname)
                                    field_elem.set('string', template.name)
                                    field_elem.set('placeholder', f'[{template.department_id.name}] {template.name}')
                                    group_elem.append(field_elem)
                                
                                page_elem.append(group_elem)
                                notebook[0].append(page_elem)
                            else:
                                # Fallback: add to sheet
                                _logger.info("No notebook found, adding to sheet")
                                sheet = doc.xpath('//sheet')
                                if sheet:
                                    group_elem = etree.Element('group')
                                    group_elem.set('string', f'{self.env["hr.department"].browse(dept_id).name} Fields')
                                    for template in templates:
                                        fname = template._column_name()
                                        field_elem = etree.Element('field')
                                        field_elem.set('name', fname)
                                        field_elem.set('string', template.name)
                                        field_elem.set('placeholder', f'[{template.department_id.name}] {template.name}')
                                        group_elem.append(field_elem)
                                    sheet[0].append(group_elem)
                        
                        elif view_type == 'tree':
                            notes_field = doc.xpath('//field[@name="notes"]')
                            if notes_field:
                                parent = notes_field[0].getparent()
                                notes_index = list(parent).index(notes_field[0])
                                
                                for i, template in enumerate(templates):
                                    fname = template._column_name()
                                    field_elem = etree.Element('field')
                                    field_elem.set('name', fname)
                                    field_elem.set('string', template.name)
                                    field_elem.set('optional', 'show')
                                    
                                    parent.insert(notes_index + 1 + i, field_elem)
                        
                        result['arch'] = etree.tostring(doc, encoding='unicode')
                        _logger.info("Updated arch with dynamic fields")
            except Exception as e:
                _logger.error(f"Error in fields_view_get: {e}")
        
        return result

    @api.model
    def action_weekly_report_with_dept_filter(self):
        """Action that automatically adds department filter for Manager/Staff users"""
        current_user = self.env.user
        
        # Check if user is BOD - no filter needed
        if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
            return {
                'type': 'ir.actions.client',
                'tag': 'weekly_report_custom_view',
                'name': 'Weekly Reports',
            }
        
        # For Manager/Staff - get their department
        assignment = self.env['peepl.user.assignment'].search([
            ('user_id', '=', current_user.id),
            ('active', '=', True)
        ], limit=1)
        
        if assignment and assignment.department_id:
            dept_id = assignment.department_id.id
            dept_name = assignment.department_id.name
            
            return {
                'type': 'ir.actions.client',
                'tag': 'weekly_report_custom_view',
                'name': f'Weekly Reports - {dept_name}',
                'context': {
                    'dept_filter': dept_id,
                    'dept_name': dept_name,
                }
            }
        
        # Fallback - no department found
        return {
            'type': 'ir.actions.client',
            'tag': 'weekly_report_custom_view',
            'name': 'Weekly Reports',
        }
