# -*- coding: utf-8 -*-
{
    'name': 'Peepl Report - Weekly Report',
    'version': '19.0.1.0.2',
    'category': 'report/Projects',
    'summary': 'Weekly Report policy for assessment services',
    'description': """
Peepl Report - Weekly Report
============================

A comprehensive weekly reporting system for project management and team oversight.

Key Features:
* Weekly report tracking and management
* PIC (Person In Charge) overview and statistics
* Department-based access control and filtering
* Interactive dashboard with real-time analytics
* Position-based permissions (Staff, Manager, BOD)
* Client and project task management
* Progress tracking with status indicators
* Mobile-responsive design

    """,
    'author': 'Peepl',
    'website': 'https://peepl.tech',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/peepl_weekly_report_security.xml',
        'security/ir.model.access.csv',
        'security/peepl_record_rules.xml',
        'data/peepl_position_data.xml',
        'data/peepl_cron_data.xml',
        'views/peepl_weekly_report_views.xml',
        'views/peepl_dashboard_views.xml',
        'views/peepl_pic_overview_views.xml',
        'views/res_config_settings_views.xml',
        'views/peepl_department_views.xml',
        'views/peepl_position_views.xml',
        'views/peepl_client_views.xml',
        'views/peepl_user_assignment_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'peepl_weekly_report/static/src/js/dashboard.js',
            'peepl_weekly_report/static/src/css/dashboard.css',
            'peepl_weekly_report/static/src/css/list_view.css',
            'peepl_weekly_report/static/src/css/kanban_view.css',
            'peepl_weekly_report/static/src/css/pic_overview.css',
            'peepl_weekly_report/static/src/xml/dashboard.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'uninstall_hook': None,
    'external_dependencies': {
        'python': [],
    },
}