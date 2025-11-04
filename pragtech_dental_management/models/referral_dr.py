# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ReferralDoctor(models.Model):
    _name = "referral.dr"

    name = fields.Char('Doctor Name', required=True)
    clinic = fields.Char('Clinic')
