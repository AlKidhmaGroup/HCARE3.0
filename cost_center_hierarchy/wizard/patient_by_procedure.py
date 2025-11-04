from odoo import models, fields, api


class PatientByProcedureWizard(models.TransientModel):
    _inherit = 'patient.by.procedure.wizard'

    department_ids = fields.Many2many(
        'medical.department', 'patient_by_procedure_dept',
        'wiz_id', 'dept_id', string='Department')

    @api.onchange('department_ids')
    def onchange_department_ids(self):
        s_domain = []
        if self.department_ids:
            doctor_ids = []
            for dept in self.department_ids:
                doctor_ids += dept.doctor_ids.ids
            s_domain += [('id', 'in', doctor_ids)]
        return {
            'domain': {
                'doctor_ids': s_domain
            }
        }

    def fetch_form_fields(self):
        res = super(PatientByProcedureWizard, self).fetch_form_fields()
        res.append('department_ids')
        return res
