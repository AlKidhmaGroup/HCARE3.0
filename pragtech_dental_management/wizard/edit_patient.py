from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class EditPatient(models.TransientModel):
    _name = 'edit.patient'

    new_patient_id = fields.Char('New Patient ID', required=True)
    patient_id = fields.Many2one('medical.patient', 'Patient', required=False)

    @api.multi
    def action_confirm(self):
        wizard_vals = self.read()[0]
        if wizard_vals['patient_id']:
            patient = self.env['medical.patient'].browse(wizard_vals['patient_id'][0])
            this_patient_company = patient.company_id
            new_patient_id = wizard_vals['new_patient_id']
            med_patient_code = self.env['ir.sequence'].search([('code', '=', 'medical.patient'),('company_id', '=', this_patient_company.id)])
            if this_patient_company.patient_prefix:
                len_prefix = len(this_patient_company.patient_prefix)
                if this_patient_company.patient_prefix not in new_patient_id:
                    raise UserError(_('Please enter valid Prefex (%s) for Patients') %
                                    this_patient_company.patient_prefix)
                if not new_patient_id[len_prefix:].isdigit():
                    raise UserError(_('Please Enter Proper Patient ID.'))
                patient.write({'patient_id': wizard_vals['new_patient_id']})
                if int(new_patient_id[len_prefix:]) >= med_patient_code.number_next_actual:
                    med_patient_code[0].write({'number_next_actual': int(new_patient_id[len_prefix:])+1})
            else:
                # if not new_patient_id.isdigit():
                #     raise UserError(_('Please Enter Proper Patient ID'))
                patient.write({'patient_id': wizard_vals['new_patient_id']})
                if new_patient_id.isdigit():
                    if int(new_patient_id) >= med_patient_code.number_next_actual:
                        med_patient_code[0].write({'number_next_actual': int(new_patient_id)+1})
