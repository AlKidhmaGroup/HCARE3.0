from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import UserError


class ConsentTableCreationWizard(models.TransientModel):
	_name = "consent.table.creation"

	name = fields.Char('Table Name', default='x_', required=True)
	field_description = fields.Char('Description', required=True)
	info = fields.Text('Note', required=False)

	@api.multi
	def create_table_wizard(self):
		wizard_table = self.env['ir.model'].search([('model', '=', self.name)])
		if not wizard_table:
			dyn_vals = {'model': self.name,
						'is_mail_thread': False,
						'field_id': [[0, 'virtual_112', {'name': 'x_name', 'field_description': 'Name', 'ttype': 'char', 'required': False, 'readonly': False, 'index': False,'visible_in_consent_tree':True}]],
						'name': self.name,
						'transient': False,
						'info': self.info,
						'transient': False,
						'consent_table' : True,
						'access_ids':[(0,0,{'group_id':self.env.ref('base.group_user').id,
										    'name':'access_'+self.name,
										    'perm_read':True,
										    'perm_write':True,
										    'perm_create':True,
										    'perm_unlink':True})]
						}
			table_id = self.env['ir.model'].sudo().create(dyn_vals)
			self.env['ir.ui.view'].create({   'arch_base':'<tree editable="bottom"><field name="%s"/></tree>' % 'x_name',
	                                           'name':self.name+'_tree',
	                                           'type':'tree',
	                                           'model':self.name,
	                                           'mode':'primary',
	                                           'active':True})
			
		else:
			raise UserError('Table Name already exist `')

