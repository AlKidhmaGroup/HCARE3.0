from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class SignWizard(models.TransientModel):
    _name = 'treatment.sign.wizard'

    digital_signature = fields.Binary(string='Signature')
    treatment = fields.Char("Treatment", readonly=True)
    doctor = fields.Char("Doctor", readonly=True)
    patient = fields.Char("Patient", readonly=True)
    updated_date = fields.Date('Updated Date', default=fields.Date.context_today, required=True)

    @api.multi
    def action_confirm(self):
        act_id = self.env.context.get('active_ids', [])
        treatment = self.env['medical.teeth.treatment'].search([('id', 'in', act_id)])
        treatment.write({'signature': self.digital_signature,
                         'updated_date':self.updated_date,
                         'wizard_treatment': self.treatment,
                         'wizard_doctor': self.doctor,
                       })
        treatment.print_consent()
