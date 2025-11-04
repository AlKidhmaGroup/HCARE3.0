# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ConsentDefaults(models.Model):
    _name = 'consent.defaults'
    _description = 'Consent Defaults'

    sequence = fields.Integer(default=1)
    name = fields.Char('Name',required=True)
    field_id = fields.Many2one('ir.model.fields',string="Field")
    arabic_name = fields.Char('Arabic Name')