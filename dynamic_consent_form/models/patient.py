# -*- coding: utf-8 -*-
from datetime import date
import base64
from odoo import api, fields, models, _


class MedicalPatient(models.Model):
    _inherit = "medical.patient"

    @api.multi
    def attach_consent(self, consent_form):
        data, data_format = consent_form.consent_detail_id.report_template_id.render([consent_form.id])
        self.env['ir.attachment'].create({
            'name': str(self.name.name) + "_" + str(consent_form.register_date)+ '_' + str(consent_form.consent_detail_id.name),
            'type': 'binary',
            'datas': base64.encodestring(data),
            'datas_fname': str(self.name.name) + '_' + str(consent_form.consent_detail_id.name) + '.pdf',
            'res_model': 'medical.patient',
            'res_id': self.id,
            'patient_id': self.id,
            'mimetype': 'application/pdf'
        })