from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import Warning


class PatientOverdueReportWizard(models.TransientModel):
    _name = "patient.overdue.report"

    def _get_patient_id(self):
        domain = [('company_id', '=', self.company_id.id)]
        return domain

    def _get_doctor_id(self):
        domain = []
        doc_ids = None
        group_dental_doc_menu = self.env.user.has_group('pragtech_dental_management.group_dental_doc_menu')
        group_dental_user_menu = self.env.user.has_group('pragtech_dental_management.group_dental_user_menu')
        group_dental_mng_menu = self.env.user.has_group('pragtech_dental_management.group_dental_mng_menu')
        if group_dental_doc_menu and not group_dental_user_menu and not group_dental_mng_menu:
            dom_partner = [('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
                           ('company_id', '=', self.company_id.id)]
            partner_ids = [x.id for x in self.env['res.partner'].search(dom_partner)]
            if partner_ids:
                doc_ids = [x.id for x in self.env['medical.physician'].search([('name', 'in', partner_ids),
                                                                               (
                                                                               'company_id', '=', self.company_id.id)])]
        else:
            doc_ids = [x.id for x in self.env['medical.physician'].search([('company_id', '=', self.company_id.id)])]
        domain = [('id', 'in', doc_ids)]
        return domain

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

    company_id = fields.Many2one('res.company', "Company", domain=_get_company_id, required=True)
    is_only_doctor = fields.Boolean()
    period_start = fields.Date("Period From")
    period_stop = fields.Date("Period To")
    patient = fields.Many2one('medical.patient', "Patient", domain=_get_patient_id)
    doctor = fields.Many2one('medical.physician', "Doctor", domain=_get_doctor_id)

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.doctor and self.doctor.company_id != self.company_id:
            self.doctor = False
        domain = self._get_doctor_id()
        return {
            'domain': {'doctor': domain}
        }

    @api.model
    def default_get(self, fields):
        res = super(PatientOverdueReportWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        res['is_only_doctor'] = False
        self._get_doctor_id()
        self._get_patient_id()
        doc_ids = None
        group_dental_doc_menu = self.env.user.has_group('pragtech_dental_management.group_dental_doc_menu')
        group_dental_user_menu = self.env.user.has_group('pragtech_dental_management.group_dental_user_menu')
        group_dental_mng_menu = self.env.user.has_group('pragtech_dental_management.group_dental_mng_menu')
        if group_dental_doc_menu and not group_dental_user_menu and not group_dental_mng_menu:
            res['is_only_doctor'] = True
            dom_partner = [('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
                           ('company_id', '=', self.env.user.company_id.id)]
            partner_ids = [x.id for x in self.env['res.partner'].search(dom_partner)]
            if partner_ids:
                doc_ids = [x.id for x in self.env['medical.physician'].search([('name', 'in', partner_ids)])]
        if doc_ids:
            res['doctor'] = doc_ids[0]
        return res

    @api.multi
    def patient_overdue_report(self):
        patient = False
        doctor = False
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        if self.patient:
            # name = self.patient.name_get()

            name = self.patient.name.name
            if self.patient.patient_id:
                name = '[' + self.patient.patient_id + ']' + name
            patient = [self.patient.id, name]
        data = {
            'company_id': [self.company_id.id, self.company_id.name],
            'period_start': self.period_start or False,
            'period_stop': self.period_stop or False,
            'patient': patient,
            'doctor': doctor,
        }
        return self.env.ref('pragtech_dental_management.act_report_patient_overdue').report_action(self, data=data)


class ReportPatientOverdue(models.AbstractModel):
    _name = 'report.pragtech_dental_management.report_patient_overdue'

    @api.model
    def get_pat_overdue_details(self, company_id=False, period_start=False, period_stop=False, patient=False,
                                doctor=False):
        dom = [
            ('type', '=', 'out_invoice'),
            ('company_id', '=', company_id[0]),
            ('is_patient', '=', True),
            ('state', '=', 'open')
        ]
        if period_start:
            dom.append(('date_invoice', '>=', period_start))
        if period_stop:
            dom.append(('date_invoice', '<=', period_stop))
        if patient:
            dom.append(('patient', '=', patient[0]))
        if doctor:
            dom.append(('dentist', '=', doctor[0]))
        invoices = self.env['account.invoice'].search(dom)
        invoice_list = []
        patients = {}
        data = {}
        for inv in invoices:
            if inv.patient:
                inv_data = {
                    'number': inv.number,
                    'date': inv.date_invoice,
                    'dentist': inv.dentist.name_get()[0][1] or '',
                    'due': inv.residual_signed
                }
                due = inv.residual_signed
                if inv.patient.id not in list(data.keys()):
                    patients[inv.patient.id] = inv.patient.name_get()[0][1]
                    data[inv.patient.id] = {
                        'invoices': [inv_data],
                        'sum': inv.residual_signed
                    }
                else:
                    data[inv.patient.id]['invoices'].append(inv_data)
                    data[inv.patient.id]['sum'] += due
        return {
            'orders': data,
            'patients': patients
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_pat_overdue_details(
            data['company_id'],
            data['period_start'],
            data['period_stop'],
            data['patient'],
            data['doctor'],
        ))
        return data
