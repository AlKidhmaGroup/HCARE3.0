# -*- coding: utf-8 -*-
from odoo import api, fields, models

class PrimaryDiagnosis(models.Model):
    _name = 'primary.diagnosis'
    _rec_name = 'code'

    code = fields.Char('Name', required=True)
    description = fields.Text('Description')
