from odoo import models, fields, api


class PatientByProcedureWizard(models.TransientModel):
    _name = 'patient.by.procedure.wizard'
    _description = 'Patient By Procedure Wizard'

    def _get_company_id(self):
        domain_company = []
        company_ids = None
        group_multi_company = self.env.user.has_group('base.group_multi_company')
        if group_multi_company:
            company_ids = [x.id for x in self.env['res.company'].search([('id', 'in', self.env.user.company_ids.ids)])]
            domain_company = [('id', 'in', company_ids)]
        else:
            domain_company = [('id', '=', self.env.user.company_id.id)]
        return domain_company

    # def _get_doctor_id(self):
    #     doc_ids = None
    #     group_dental_doc_menu = self.env.user.has_group(
    #         'pragtech_dental_management.group_dental_doc_menu')
    #     group_dental_user_menu = self.env.user.has_group(
    #         'pragtech_dental_management.group_dental_user_menu')
    #     group_dental_mng_menu = self.env.user.has_group(
    #         'pragtech_dental_management.group_dental_mng_menu')
    #     if (group_dental_doc_menu and not group_dental_user_menu and not
    #             group_dental_mng_menu):
    #         dom_partner = [
    #             ('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
    #             ('company_id', '=', self.company_id.id)]
    #         partner_ids = [x.id for x in self.env['res.partner'].search(
    #             dom_partner)]
    #         if partner_ids:
    #             doc_ids = [x.id for x in self.env['medical.physician'].search(
    #                 [('name', 'in', partner_ids),
    #                  ('company_id', '=', self.company_id.id)])]
    #     else:
    #         doc_ids = [x.id for x in self.env['medical.physician'].search(
    #             [('company_id', '=', self.company_id.id)])]
    #     domain = [('id', 'in', doc_ids)]
    #     return domain
    #
    # def _get_patient_id(self):
    #     return [('company_id', '=', self.company_id.id)]

    company_id = fields.Many2one('res.company', "Company",
                                 domain=_get_company_id, required=True)
    date_start = fields.Date('From Date', required=True,
                             default=fields.Date.context_today)
    date_end = fields.Date('To Date', required=True,
                           default=fields.Date.context_today)
    doctor_ids = fields.Many2many(
        'medical.physician', 'patient_by_procedure_physician', 'wiz_id',
        'doctor', string="Doctor")
    patient_ids = fields.Many2many(
        'medical.patient', 'patient_by_procedure_patient', 'wiz_id',
        'patient', string="Patient")

    @api.model
    def default_get(self, fields):
        res = super(PatientByProcedureWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        return res

    @api.multi
    def print_report(self):
        datas = {
            'active_ids': self.env.context.get('active_ids', []),
            'form': self.read(self.fetch_form_fields())[0]
        }
        datas['form']['company_id'] = [self.company_id.id, self.company_id.name]
        values = self.env.ref(
            'pragtech_dental_management.patient_by_procedure_qweb'
        ).report_action(self, data=datas)
        return values

    def fetch_form_fields(self):
        return ['date_start', 'date_end', 'doctor_ids', 'patient_ids']
