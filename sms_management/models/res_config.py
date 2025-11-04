# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import api, exceptions, fields, models


class SMSSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_payment_sms = fields.Boolean(string="Payment Receipt SMS", default=False )
    confirmed_appt_only = fields.Boolean(string="Sent Confirmed Appt Only in SMS", default=False)
    
    @api.model
    def get_values(self):
        res = super(SMSSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        send_payment_sms = literal_eval(ICPSudo.get_param(
            'send_payment_sms', default='False'))
        confirmed_appt_only = literal_eval(ICPSudo.get_param(
            'confirmed_appt_only', default='False'))
        res.update({
            'send_payment_sms': send_payment_sms,
            'confirmed_appt_only':confirmed_appt_only
        })
        return res

    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        super(SMSSettings, self).set_values()
        ICPSudo.set_param("send_payment_sms", self.send_payment_sms)
        ICPSudo.set_param("confirmed_appt_only", self.confirmed_appt_only)


