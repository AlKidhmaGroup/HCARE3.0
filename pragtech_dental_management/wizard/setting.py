# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from mock import DEFAULT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import hashlib
import time
from odoo.exceptions import Warning
import json
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    registration_invoice_product_id = fields.Many2one('product.product','Registration Invoice Product')
    basic_product_id = fields.Many2one('product.product', 'Basic Checkup Product')
    # default_discount_account = fields.Many2one('account.account', string='Invoice Discount Account')
    module_mdc_quantity_paylines = fields.Boolean('Quantity on payment lines')
    module_concerned_doctor_clinical_finding = fields.Boolean('Multiple Complaints and Findings(Doctor Favourite)')
    module_concerned_doctor_p_diagnosis = fields.Boolean('Multiple Primary diagnosis')
    module_concerned_doctor_procedure = fields.Boolean('Multiple Procedure(Doctor Favourite)')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        registration_invoice_product_id = literal_eval(ICPSudo.get_param('registration_invoice_product_id', default='False'))
        if registration_invoice_product_id and not self.env['product.product'].browse(registration_invoice_product_id).exists():
            registration_invoice_product_id = False
        basic_product_id = literal_eval(ICPSudo.get_param('basic_product_id', default='False'))
        if basic_product_id and not self.env['product.product'].browse(basic_product_id).exists():
            basic_product_id = False
        res.update({'registration_invoice_product_id': registration_invoice_product_id,
                    'basic_product_id': basic_product_id})
        return res
    
    
    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).set_values()
        ICPSudo.set_param("registration_invoice_product_id", self.registration_invoice_product_id.id)
        ICPSudo.set_param("basic_product_id", self.basic_product_id.id)
        ICPSudo.set_param("pragtech_dental_management.module_mdc_quantity_paylines", self.module_mdc_quantity_paylines)
        ICPSudo.set_param("pragtech_dental_management.module_concerned_doctor_clinical_finding", self.module_concerned_doctor_clinical_finding)
        ICPSudo.set_param("pragtech_dental_management.module_concerned_doctor_p_diagnosis", self.module_concerned_doctor_p_diagnosis)
        ICPSudo.set_param("pragtech_dental_management.module_concerned_doctor_procedure", self.module_concerned_doctor_procedure)
