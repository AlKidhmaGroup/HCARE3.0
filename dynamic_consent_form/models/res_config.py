# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models
from ast import literal_eval
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    consent_form_font_size = fields.Float('Overtime Hourly rate(Holiday)')
    consent_header = fields.Boolean('Consent Form Header And Footer')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        consent_header = literal_eval(ICPSudo.get_param('consent_header', default='False'))
        # consent_form_font_size = ICPSudo.get_param('consent_form_font_size', default=20)
        res.update(
            # consent_form_font_size= float(consent_form_font_size),
            consent_form_font_size= float(self.env['ir.config_parameter'].sudo().get_param('dynamic_consent_form.consent_form_font_size')) or 12.00,
        )
        res.update({'consent_header': consent_header})
        return res

    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        super(ResConfigSettings, self).set_values()
        old_font_size = self.env['ir.config_parameter'].sudo().get_param('dynamic_consent_form.consent_form_font_size')
        self.env['ir.config_parameter'].sudo().set_param('dynamic_consent_form.consent_form_font_size', self.consent_form_font_size)
        ICPSudo.set_param("consent_header", self.consent_header)
        
        if old_font_size != self.consent_form_font_size:
            for rec in self.env['consent.details'].search([]):
                if rec.report_template_id:
                    rec.delete_report_template()
                    rec.modify_report_template()
                if rec.report_blank_template_id:
                    rec.delete_blank_report_template()
                    rec.create_blank_report_template()
