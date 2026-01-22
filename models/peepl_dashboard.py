# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplDashboard(models.Model):
    _name = 'peepl.dashboard'
    _description = 'Peepl Dashboard'

    name = fields.Char(string='Dashboard Name', default='Dashboard')
    total_reports = fields.Integer(string='Total Reports', compute='_compute_stats')
    total_users = fields.Integer(string='Total Users', compute='_compute_stats')
    total_departments = fields.Integer(string='Total Departments', compute='_compute_stats')

    @api.depends()
    def _compute_stats(self):
        for record in self:
            record.total_reports = self.env['peepl.weekly.report'].search_count([])
            record.total_users = self.env['peepl.user.assignment'].search_count([('active', '=', True)])
            record.total_departments = self.env['peepl.department'].search_count([('active', '=', True)])
    
    @api.model
    def create_default_dashboard(self):
        if not self.search([]):
            self.create({'name': 'Main Dashboard'})