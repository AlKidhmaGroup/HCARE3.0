# -*- coding: utf-8 -*-
{
    'name': 'Revenue Report',
    'version': '10.4',
    'category': 'Generic Modules/Others',
    'sequence': 1,
    'summary': 'Manage Reporting',
    'description': """
Revenue Reports
    """,
    'author': 'Al Khidma Systems',
    'depends': ['base','pragtech_dental_management', 'detailed_insurance'],
    'data': [
        'invoices.xml',
        'wizard/revenue_report_wizard.xml',
            ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
