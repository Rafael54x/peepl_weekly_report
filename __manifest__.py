# -*- coding: utf-8 -*-
{
    'name': 'Peepl Report - Weekly Report',
    'version': '19.0.1.0.11',
    'category': 'report/Projects',
    'summary': 'Weekly Report',
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
    'depends': ['base', 'web', 'hr'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/peepl_weekly_report_views.xml',
        'views/inherited_views.xml',
        'views/peepl_weekly_report_filtered_tree.xml',
        'views/peepl_dashboard_views.xml',
        'views/peepl_pic_overview_views.xml',
        'views/peepl_user_assignment_views.xml',
        'views/peepl_field_template_views.xml',
        'views/peepl_weekly_report_bod_views.xml',
        'views/peepl_department_delete_wizard_views.xml',
        'views/peepl_division_views.xml',
        'data/peepl_field_template_demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'peepl_weekly_report/static/src/js/hide_staff_menus.js',
            'peepl_weekly_report/static/src/js/render_notes.js',
            'peepl_weekly_report/static/src/js/column_resize_new.js',
            'peepl_weekly_report/static/src/js/dashboard.js',
            'peepl_weekly_report/static/src/js/field_template_reload.js',
            'peepl_weekly_report/static/src/js/weekly_report_custom_view.js',
            'peepl_weekly_report/static/src/js/pic_overview_custom_view.js',
            'peepl_weekly_report/static/src/js/bod_menu_hider.js',
            'peepl_weekly_report/static/src/js/progress_color.js',
            'peepl_weekly_report/static/src/js/weekly_access_refresh.js',
            'peepl_weekly_report/static/src/js/user_access_reload.js',
            'peepl_weekly_report/static/src/js/hide_breadcrumb.js',
            'peepl_weekly_report/static/src/js/history_back_action.js',
            'peepl_weekly_report/static/src/js/hide_save_button.js',
            'peepl_weekly_report/static/src/js/department_create_redirect.js',
            'peepl_weekly_report/static/src/css/dashboard.css',
            'peepl_weekly_report/static/src/css/column_resize_new.css',
            'peepl_weekly_report/static/src/css/list_view.css',
            'peepl_weekly_report/static/src/css/kanban_view.css',
            'peepl_weekly_report/static/src/css/pic_overview.css',
            'peepl_weekly_report/static/src/css/field_template.css',
            'peepl_weekly_report/static/src/css/progress_color.css',
            'peepl_weekly_report/static/src/css/project_task_multiline.css',
            'peepl_weekly_report/static/src/xml/dashboard.xml',
            'peepl_weekly_report/static/src/xml/weekly_report_custom_view.xml',
            'peepl_weekly_report/static/src/xml/pic_overview_custom_view.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': None,
    'pre_init_hook': None,
    'uninstall_hook': None,
    'external_dependencies': {
        'python': [],
    },
}