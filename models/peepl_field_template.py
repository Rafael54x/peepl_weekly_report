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
        ('selection', 'Dropdown'),
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
        # Direct sync to weekly report model
        self._sync_template_column('peepl.weekly.report')

    def _sync_template_column(self, model):
        """Create/update field on a specific model for this template"""
        for template in self:
            column = template._column_name()
            
            # Check if field exists
            existing_field = self.env['ir.model.fields'].sudo().search([
                ('name', '=', column),
                ('model', '=', model)
            ], limit=1)

            # If field exists and type changed, delete it first
            if existing_field and existing_field.ttype != template.field_type:
                existing_field.sudo().unlink()
                existing_field = False
            
            field_data = {
                'name': column,
                'field_description': template.name,
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

            if not existing_field:
                # Create new field
                self.env['ir.model.fields'].sudo().create(field_data)
            else:
                # Update existing field (only if type is same)
                existing_field.sudo().write({
                    'field_description': template.name,
                    'selection': field_data.get('selection', ''),
                    'relation': field_data.get('relation', ''),
                })

    def write(self, vals):
        """Trigger field sync when template is modified"""
        res = super().write(vals)
        if any(key in vals for key in ['name', 'field_type', 'selection_values', 'relation_model', 'active']):
            try:
                self._sync_all_template_columns()
                # Force registry reload and setup
                self.env.registry.clear_cache()
                self.env['peepl.weekly.report']._setup_complete()
                # Commit to ensure changes are applied
                self.env.cr.commit()
            except Exception:
                # Skip sync during upgrade/install to avoid conflicts
                pass
        return res

    def unlink(self):
        """Remove dynamic fields when template is deleted"""
        try:
            self._find_template_column().unlink()
        except Exception:
            pass
        res = super().unlink()
        # Force registry reload after deletion
        self.env.registry.clear_cache()
        return res

    @api.model
    def create(self, vals):
        """Trigger field sync when new template is created"""
        record = super().create(vals)
        try:
            # Sync field immediately
            record._sync_all_template_columns()
            # Force registry reload and setup
            self.env.registry.clear_cache()
            self.env['peepl.weekly.report']._setup_complete()
            # Commit to ensure field is created
            self.env.cr.commit()
        except Exception:
            # Skip sync during upgrade/install to avoid conflicts
            pass
        return record
    
    def action_refresh_page(self):
        """Return action to reload the page"""
        # Force reload model fields
        self.env['peepl.weekly.report']._setup_complete()
        self.env.registry.clear_cache()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': 'Fields updated successfully!',
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                },
            }
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
        """Get field template names filtered by department context"""
        domain = [('active', '=', True)]
        
        # Check for department filter - BOD acts as manager of clicked department
        dept_filter = self.env.context.get('dept_filter')
        if dept_filter:
            domain.append(('department_id', '=', dept_filter))
        else:
            # Regular role-based filtering
            current_user = self.env.user
            if not current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id),
                    ('active', '=', True)
                ], limit=1)
                if assignment and assignment.department_id:
                    domain.append(('department_id', '=', assignment.department_id.id))
            # BOD without dept_filter sees all templates (normal behavior)
        
        templates = self.env['peepl.field.template'].search(domain)
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
        """Filter dynamic fields based on department filter"""
        fields = super().fields_get(allfields, attributes)
        
        # Get department filter
        dept_id = self.env.context.get('dept_filter')
        if dept_id:
            # Force filtering for BOD when dept_filter is set
            allowed_templates = self.env['peepl.field.template'].sudo().search([
                ('department_id', '=', dept_id),
                ('active', '=', True)
            ])
            allowed_fnames = [template._column_name() for template in allowed_templates]
            
            # Remove all dynamic fields that don't belong to this department
            for fname in list(fields.keys()):
                if fname.startswith('x_field') and fname.endswith('_value'):
                    if fname not in allowed_fnames:
                        del fields[fname]
        
        # Set proper labels and selection options for remaining fields
        templates = self.env['peepl.field.template'].sudo().search([('active', '=', True)])
        for template in templates:
            fname = template._column_name()
            if fname in fields:
                fields[fname]['string'] = template.name
                # Add selection options for dropdown fields
                if template.field_type == 'selection' and template.selection_values:
                    options = [line.strip() for line in template.selection_values.split('\n') if line.strip()]
                    fields[fname]['selection'] = [(opt, opt) for opt in options]
                    fields[fname]['type'] = 'selection'
        
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
        if self.env.context.get("studio"):
            return arch, view
            
        # Get department filter or use role-based filtering
        dept_id = self.env.context.get('dept_filter')
        if dept_id:
            templates = self.env['peepl.field.template'].sudo().search([
                ('department_id', '=', dept_id),
                ('active', '=', True)
            ], order='sequence')
        else:
            templates = self.env['peepl.field.template'].search([('active', '=', True)], order='sequence')
        
        if not templates:
            return arch, view
            
        from lxml import etree
        
        if view_type == 'form':
            # Find the second group or create one
            groups = arch.findall('.//group')
            if len(groups) >= 2:
                target_group = groups[1]
            else:
                # Create a new group if not enough groups exist
                sheet = arch.find('.//sheet')
                if sheet is not None:
                    target_group = etree.SubElement(sheet, 'group')
                    target_group.set('string', 'Custom Fields')
                else:
                    return arch, view
            
            for template in templates:
                fname = template._column_name()
                # Check if field exists in model fields
                if fname in self._fields:
                    field_elem = etree.SubElement(target_group, 'field')
                    field_elem.set('name', fname)
                    field_elem.set('placeholder', f'{template.department_id.name} Custom Template')
                    
                    # Add widget based on field type
                    if template.field_type == 'selection':
                        field_elem.set('widget', 'selection')
                    elif template.field_type == 'char':
                        field_elem.set('widget', 'char')
        
        elif view_type == 'list':
            # Find notes field and add custom fields before it
            notes_node = arch.find('.//field[@name="notes"]')
            if notes_node is not None:
                parent = notes_node.getparent()
                notes_index = list(parent).index(notes_node)
                
                for i, template in enumerate(templates):
                    fname = template._column_name()
                    if fname in self._fields:
                        field_elem = etree.Element('field')
                        field_elem.set('name', fname)
                        field_elem.set('optional', 'show')
                        field_elem.set('width', '150px')
                        
                        # Insert before notes field
                        parent.insert(notes_index + i, field_elem)
        
        return arch, view
