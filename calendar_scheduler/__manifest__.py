# -*- coding: utf-8 -*-
{
	'name': "Calendar Scheduler",

	'summary': 'Calendar Scheduler View',

	'description': """ """,

	'author': 'Al Khidma Systems',
	'website': "",

	'category': 'Uncategorized',
	'version': '11.0.1.2.2',

	'depends': [
		'web',
		'base',
		'pragtech_dental_management',
		'resource',
		'hr_holidays',
	],

	'data': [
		'security/ir.model.access.csv',
		'data/state_color_data.xml',
		'views/hr_config_settings.xml',
		'views/calendar.xml',
		'views/state_color_view.xml',
		'views/saloon_scheduler.xml',
		'views/working_time.xml',
		'wizard/reschedule_wizard.xml',
		'report/report_rescheduled.xml',
	],
	'qweb': ['static/src/xml/*.xml'],

	'demo': [],
	'application': True,
	'post_init_hook': 'update_appointment_color',
}
