# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Consent(models.Model):
    _name = "consent.consent"

    name = fields.Char('Consent Name', required=True)
    model_name = fields.Char('Model Name')
    treatment_ids = fields.One2many('product.product', 'consent_id', 'Treatments')
