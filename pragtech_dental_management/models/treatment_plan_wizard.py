from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class PlanWizard(models.TransientModel):
    _name = 'treatment.plan.wizard'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
        default=_get_default_company_id, readonly=True)
    plan_signature = fields.Binary(string='Signature')
    appt_id = fields.Many2one('medical.appointment', "Appointment", readonly=True)
    doctor = fields.Char("Doctor", readonly=True)
    patient = fields.Char("Patient", readonly=True)
    updated_date = fields.Date('Updated Date', default=fields.Date.context_today, required=True, readonly=True)
    operations = fields.Many2many('medical.teeth.treatment', compute='_compute_operations')
    treatment_plan_content = fields.Html(related='company_id.treatment_plan_content')

    @api.multi
    @api.model
    @api.depends('doctor')
    def _compute_operations(self):
        oper_obj = self.env['medical.teeth.treatment']
        if self.appt_id:
            oper_ids = oper_obj.search([('patient_id', '=', self.appt_id.patient.id), ('state', 'in', ['planned'])])
        else:
            oper_ids = False
        self.operations = oper_ids

    @api.onchange("appt_id")
    def onchange_appt(self):
        for record in self:
            if record.appt_id:
                record.doctor = record.appt_id.doctor.name.name
                record.patient = record.appt_id.patient_name


    @api.multi
    def action_confirm(self):
        act_id = self.env.context.get('active_ids', [])
        appt = self.env['medical.appointment'].search([('id', 'in', act_id)])
        appt.write({'plan_signature': self.plan_signature,
                    'treatment_plan_date': self.updated_date,
                       })
        appt.attach_treatment_plan()
