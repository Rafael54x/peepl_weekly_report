# -*- coding: utf-8 -*-
from lxml.builder import E
from odoo import api, fields, models, _
from odoo.tools import make_index_name, create_index


class PeeplFieldTemplate(models.Model):
    """Field templates for weekly reports - similar to survey.template"""
    _name = 'peepl.field.template'
    _description = 'Weekly Report Field Template'
    _order = 'sequence, id'

    name = fields.Text('Field Name', required=True, translate=True)
    description = fields.Text('Description', translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    allowed_department_ids = fields.Many2many('hr.department', compute='_compute_allowed_departments')
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Multiline Text'),
        ('integer', 'Integer'),
        ('float', 'Decimal'),
        ('boolean', 'Checkbox'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('selection', 'Dropdown'),
        ('many2one', 'Many2one'),
    ], string='Field Type', default='char', required=True)
    selection_values = fields.Text('Selection Values', help='One per line for dropdown')
    relation_model = fields.Char('Related Model', help='e.g. res.partner')

    def _column_name(self):
        """Return the field name for this template (e.g., 'x_field1_value')"""
        self.ensure_one()
        return f"x_field{self.id}_value"

    def _find_template_column(self, model=False):
        """Find the ir.model.fields record for this template's field"""
        domain = [('name', 'in', [template._column_name() for template in self])]
        if model:
            domain.append(('model', '=', model))
        return self.env['ir.model.fields'].sudo().search(domain)

    def _sync_all_template_columns(self):
        """Sync fields on all models inheriting peepl.field.template.mixin"""
        try:
            model_names = self.env.registry.descendants(
                ['peepl.field.template.mixin'], '_inherit'
            ) - {'peepl.field.template.mixin'}
            for model in model_names:
                self._sync_template_column(model)
        except Exception:
            # Fallback to direct model sync
            self._sync_template_column('peepl.weekly.report')

    def _sync_template_column(self, model):
        """Create/update/delete field on a specific model for this template"""
        try:
            for template in self:
                prev_stored = template._find_template_column(model)
                column = template._column_name()
                description = template.name

                field_data = {
                    'name': column,
                    'field_description': description,
                    'state': 'manual',
                    'model': model,
                    'model_id': self.env['ir.model']._get_id(model),
                    'ttype': template.field_type,
                    'copied': True,
                }

                # Add selection values
                if template.field_type == 'selection' and template.selection_values:
                    options = [line.strip() for line in template.selection_values.split('\n') if line.strip()]
                    field_data['selection'] = str([(opt, opt) for opt in options])
                
                # Add relation model
                if template.field_type == 'many2one' and template.relation_model:
                    field_data['relation'] = template.relation_model

                if not prev_stored:
                    # Create new field
                    field = self.env['ir.model.fields'].with_context(
                        update_custom_fields=True
                    ).sudo().create(field_data)
                    
                    # Create index if model has _auto
                    Model = self.env[model]
                    if Model._auto:
                        tablename = Model._table
                        indexname = make_index_name(tablename, column)
                        try:
                            create_index(self.env.cr, indexname, tablename, [column], 'btree', f'{column} IS NOT NULL')
                            field['index'] = True
                        except Exception:
                            pass
                else:
                    # Update existing field
                    prev_stored.write(field_data)
        except Exception:
            pass

    def write(self, vals):
        """Trigger field sync when template is modified"""
        res = super().write(vals)
        if any(key in vals for key in ['name', 'field_type', 'selection_values', 'relation_model', 'active']):
            try:
                self._sync_all_template_columns()
                self.env.registry.clear_cache('stable')
                self.env.registry.init_models(self.env.cr, ['peepl.weekly.report'], self.env.context)
            except Exception:
                pass
        return res

    def unlink(self):
        """Remove dynamic fields when template is deleted"""
        try:
            self._find_template_column().unlink()
        except Exception:
            pass
        res = super().unlink()
        try:
            self.env.registry.clear_cache('stable')
            self.env.registry.init_models(self.env.cr, ['peepl.weekly.report'], self.env.context)
        except Exception:
            pass
        # Add delay notification before reload
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': 'Field deleted. Page will reload...',
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                },
            }
        }

    @api.model
    def create(self, vals):
        """Trigger field sync when new template is created"""
        record = super().create(vals)
        try:
            record._sync_all_template_columns()
            self.env.registry.clear_cache('stable')
            self.env.registry.init_models(self.env.cr, ['peepl.weekly.report'], self.env.context)
        except Exception:
            pass
        return record
    
    def action_refresh_page(self):
        """Return action to reload the page"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    @api.depends('create_uid')
    def _compute_allowed_departments(self):
        """Compute allowed departments based on user role"""
        for record in self:
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                # BOD: all departments
                record.allowed_department_ids = self.env['hr.department'].search([])
            else:
                # Manager/Staff: only their department
                assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if assignment and assignment.department_id:
                    record.allowed_department_ids = assignment.department_id
                else:
                    record.allowed_department_ids = self.env['hr.department']


class PeeplFieldTemplateMixin(models.AbstractModel):
    """Mixin that provides dynamic fields - similar to survey.template.fields.mixin"""
    _name = 'peepl.field.template.mixin'
    _description = 'Field Template Mixin'

    def _get_template_fnames(self):
        """Get all field template names that exist on this model"""
        templates = self.env['peepl.field.template'].search([('active', '=', True)])
        return [fname for template in templates if (fname := template._column_name()) in self]

    def _get_field_responses(self):
        """Return dict of template_id: response for this record"""
        result = {}
        for fname in self._get_template_fnames():
            if self[fname]:
                template_id = int(fname.split('field')[1].split('_')[0])
                result[template_id] = self[fname]
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Customize field labels with template names"""
        fields = super().fields_get(allfields, attributes)
        try:
            if not self.env.context.get("studio"):
                templates = self.env['peepl.field.template'].search([('active', '=', True)])
                for template in templates:
                    fname = template._column_name()
                    if fname in fields:
                        fields[fname]['string'] = template.name
        except Exception:
            pass
        return fields

    def _get_view(self, view_id=None, view_type='form', **options):
        """Intercept view to patch it with dynamic fields"""
        arch, view = super()._get_view(view_id, view_type, **options)
        try:
            return self._patch_view(arch, view, view_type)
        except Exception:
            return arch, view

    def _patch_view(self, arch, view, view_type):
        """Inject template fields into views dynamically"""
        try:
            if not self.env.context.get("studio"):
                # Search templates - record rules will automatically filter by department
                templates = self.env['peepl.field.template'].search([('active', '=', True)], order='sequence')
                
                if view_type == 'list':
                    notes_node = arch.find('.//field[@name="notes"]')
                    if notes_node is not None:
                        for template in templates:
                            fname = template._column_name()
                            # Only add if field exists in model
                            if fname not in self._fields:
                                continue
                            
                            field_attrs = {
                                'name': fname,
                                'optional': 'show',
                                'width': '200px',
                            }
                            
                            # Add widget based on field type
                            if template.field_type == 'text':
                                field_attrs['widget'] = 'text'
                            elif template.field_type == 'boolean':
                                field_attrs['widget'] = 'boolean_toggle'
                            elif template.field_type == 'date':
                                field_attrs['widget'] = 'date'
                            elif template.field_type == 'datetime':
                                field_attrs['widget'] = 'datetime'
                            elif template.field_type == 'float':
                                field_attrs['widget'] = 'float'
                            elif template.field_type == 'integer':
                                field_attrs['widget'] = 'integer'
                            
                            notes_node.addprevious(E.field(**field_attrs))
                
                elif view_type == 'form':
                    groups = arch.findall('.//group')
                    if len(groups) >= 2:
                        target_group = groups[1]
                        for template in templates:
                            fname = template._column_name()
                            # Only add if field exists in model
                            if fname not in self._fields:
                                continue
                            
                            field_attrs = {'name': fname}
                            
                            # Add widget for form view
                            if template.field_type == 'text':
                                field_attrs['widget'] = 'text'
                            elif template.field_type == 'boolean':
                                field_attrs['widget'] = 'boolean_toggle'
                            
                            target_group.append(E.field(**field_attrs))
        except Exception:
            pass
        
        return arch, view
