# -*- coding: utf-8 -*-
{
    'name': 'Basic Insurance',
    'version': '1.4',
    'category': 'Accounting',
    'author': 'Al Khidma Systems',
       'website': 'http://www.alkhidmasystems.com',
    'license': 'AGPL-3',
    'depends': ['pragtech_dental_management', 'update_invoice_payment','cost_center_hierarchy'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/insurance.xml',
        'views/dental.xml',
        'views/invoice.xml',
        'views/policy_holder.xml',
        'wizard/income_by_insurance_company.xml',
        'wizard/claim_wizard.xml',
        'report/reports.xml',
        'report/report_income_by_insurance_company.xml',
        'report/claim_report_temp.xml',
        'report/account_invoice_report_view.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'images': [],
}
