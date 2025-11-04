# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class MedicalAppointment(models.Model):
    _inherit = 'medical.appointment'

    @api.multi
    def get_consent_forms(self):
        
        consent_action = self.env.ref('dynamic_consent_form.action_consents_details').read()[0]
        consent_action['context'] = {'default_patient_id': self.patient.id, 'default_doctor_id': self.doctor.id}
        consent_action['target']= 'new'
        return consent_action
        
        # return {
        #     'name': _('Consent form'),
        #     'view_id': self.env.ref('dynamic_consent_form.consent_form_wizard').id,
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'consent.wizard',
        #     'target': 'new',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'context': {'default_patient_id': self.patient.id, 'default_doctor_id': self.doctor.id}
        # }