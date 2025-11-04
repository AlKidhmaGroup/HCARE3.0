# -*- coding: utf-8 -*-
{
    'name': 'Detailed Insurance',
    'version': '1.3',
    'category': 'Accounting',
    'author': 'Al Khidma Systems',
    'website': 'http://www.alkhidmasystems.com',
    'license': 'AGPL-3',
    'depends': ['pragtech_dental_management', 'basic_insurance'],
    'data': [
        'views/insurance.xml',
        'views/dental.xml',
        'views/invoice.xml',
        'wizard/update_copay_wizard.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'images': [],
}
