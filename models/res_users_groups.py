from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    weekly_report_access = fields.Selection([
        ('none', 'No Access'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('bod', 'BOD')
    ], string='Weekly Report Access', default='none')
    
    def action_sync_weekly_report_access(self):
        """Force hard refresh like Ctrl+Shift+R"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
    
    def write(self, vals):
        result = super().write(vals)
        if 'weekly_report_access' in vals:
            self._update_groups_from_dropdown()
        return result
    
    def _update_groups_from_dropdown(self):
        """Update group membership based on dropdown selection"""
        staff_group = self.env.ref('peepl_weekly_report.group_peepl_staff', raise_if_not_found=False)
        manager_group = self.env.ref('peepl_weekly_report.group_peepl_manager', raise_if_not_found=False)
        bod_group = self.env.ref('peepl_weekly_report.group_peepl_bod', raise_if_not_found=False)
        
        # Remove all weekly report groups first
        if staff_group:
            self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, staff_group.id))
        if manager_group:
            self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, manager_group.id))
        if bod_group:
            self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, bod_group.id))
        
        # Add selected group based on dropdown
        if self.weekly_report_access == 'staff' and staff_group:
            self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, staff_group.id))
        elif self.weekly_report_access == 'manager' and manager_group:
            self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, manager_group.id))
        elif self.weekly_report_access == 'bod' and bod_group:
            self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, bod_group.id))
        
        # Clear cache to ensure UI updates
        self.env.registry.clear_cache()
    
    @api.onchange('weekly_report_access')
    def _onchange_weekly_report_access(self):
        if self.weekly_report_access and self.id:
            staff_group = self.env.ref('peepl_weekly_report.group_peepl_staff', raise_if_not_found=False)
            manager_group = self.env.ref('peepl_weekly_report.group_peepl_manager', raise_if_not_found=False)
            bod_group = self.env.ref('peepl_weekly_report.group_peepl_bod', raise_if_not_found=False)
            
            # Only execute for existing records (not NewId)
            if isinstance(self.id, int):
                # Remove all weekly report groups first
                if staff_group:
                    self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, staff_group.id))
                if manager_group:
                    self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, manager_group.id))
                if bod_group:
                    self.env.cr.execute("DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s", (self.id, bod_group.id))
                
                # Add selected group
                if self.weekly_report_access == 'staff' and staff_group:
                    self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, staff_group.id))
                elif self.weekly_report_access == 'manager' and manager_group:
                    self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, manager_group.id))
                elif self.weekly_report_access == 'bod' and bod_group:
                    self.env.cr.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (self.id, bod_group.id))