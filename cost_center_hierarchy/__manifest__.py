# -*- coding: utf-8 -*-
{
    'name': 'Cost Center Hierarchy',
    'version': '10.3',
    'category': '',
    'sequence': 2,
    'summary': '',
    'description': """
    """,
    'author': 'Al Khidma Systems',
    'depends': ['pragtech_dental_management', 'account_cost_center'],
    'data': [
        'security/ir.model.access.csv',
        'security/multi_company_security.xml',
        'data/cron.xml',
        'views/physician.xml',
        'views/department.xml',
        'views/cost_center.xml',
        'views/company.xml',
        'wizard/user_creation.xml',
        'wizard/patient_by_procedure.xml',
        'wizard/income_by_doctor.xml',
            ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
