# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class Model(models.Model):
	_inherit = 'ir.model'
	
	consent_table = fields.Boolean('Is machine related?')
	consent_no_create = fields.Boolean('Consent No Create?')
	consent_no_delete = fields.Boolean('Consent No Delete?')
	name_readonly = fields.Boolean('Name Readonly?')
	
	@api.model
	def create(self, vals):
		return super(Model, self).create(vals) 
	
	@api.multi
	def update_consent_view(self):
		for rec in self:
			for view in rec.view_ids.filtered(lambda r: r.type=='tree'):
				arch_view ="""<tree"""
				if rec.consent_no_create:
					arch_view += """ create='0'"""
				if rec.consent_no_delete:
					arch_view += """ delete='0'"""
				arch_view += """ editable="bottom">"""
				for field in rec.field_id.filtered(lambda r: r.visible_in_consent_tree).sorted(key=lambda t: t.dynamic_sequence):
					if field.name =="x_name" and rec.name_readonly:
						arch_view += """<field name='""" + field.name+"""' readonly="1" force_save="1"/>"""
					else:
						arch_view += """<field name='""" + field.name+"""'/>"""
				arch_view += """</tree>"""
				view.arch_base = arch_view
				
