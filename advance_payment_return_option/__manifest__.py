{
    'name': "Advance Payment Return Management",
    'version': '0.7',
    'sequence': 2,
    'author': 'Al Khidma Systems',
    'category': 'Invoicing',
    'description': 'Allows you to manage advance payment return option',
    'depends': ['advance_payment_option'],
    'data': [
        'wizard/advance_return_payment_view.xml',
        'views/advance_payments.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
