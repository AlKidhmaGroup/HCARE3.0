from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import Warning
from datetime import datetime


class AdvancePaymentReportWizard(models.TransientModel):
    _name = "advance.payment.report"

    def _get_doctor_id(self):
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
                                                                                   'company_id', '=',
                                                                                   self.company_id.id)])]
        else:
            doc_ids = [x.id for x in self.env['medical.physician'].search([('company_id', '=', self.company_id.id)])]
        domain = [('id', 'in', doc_ids)]
        return domain

    def _get_company_id(self):
        group_multi_company = self.env.user.has_group('base.group_multi_company')
        if group_multi_company:
            company_ids = [x.id for x in self.env['res.company'].search([('id', 'in', self.env.user.company_ids.ids)])]
            domain_company = [('id', 'in', company_ids)]
        else:
            domain_company = [('id', '=', self.env.user.company_id.id)]
        return domain_company

    company_id = fields.Many2one('res.company', "Company", domain=_get_company_id, required=True)
    period_start = fields.Date("Period From", default=fields.Date.context_today)
    period_stop = fields.Date("Period To", default=fields.Date.context_today)
    patient = fields.Many2one('res.partner', "Patient", domain=[('is_patient', '=', True)])
    is_only_doctor = fields.Boolean()
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
        res = super(AdvancePaymentReportWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        res['is_only_doctor'] = False
        self._get_doctor_id()
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
    def sale_report(self):
        doctor = False
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        data = {
            'period_start': self.period_start,
            'period_stop': self.period_stop,
            'patient_id': self.patient.id,
            'patient': self.patient.name,
            'doctor': doctor,
            'company_id': [self.company_id.id, self.company_id.name],
        }
        return self.env.ref('advance_payment_option.advance_payment_report').report_action(self, data=data)


class ReportAdvPayment(models.AbstractModel):
    _name = 'report.advance_payment_option.advance_payment_report_pdf'

    @api.model
    def get_adv_payment_details(self, period_start=False, period_stop=False, patient_id=False, patient=False,
                                doctor=False, company_id=False):
        dom = [
            ('partner_type', '=', 'customer'),
            ('advance', '=', True),
            ('state', 'in', ('posted', 'reconciled')),
            ('company_id', '=', company_id[0]),
        ]
        if period_start:
            dom.append(('payment_date', '>=', period_start))
        if period_stop:
            dom.append(('payment_date', '<=', period_stop))
        if patient:
            dom.append(('partner_id', '=', patient_id))
        if doctor:
            dom.append(('doctor_id', '=', doctor[0]))
        payment_records = self.env['account.payment'].search(dom)
        order_list = []
        cash_count = 0
        card_count = 0
        for payment in payment_records:
            doctor = ''
            if payment.doctor_id:
                doctor = payment.doctor_id.name.name
            pay_mode = False
            cash = 0
            credit = 0
            journal_obj = self.env['account.journal']
            cash_journals = journal_obj.search([('type', '=', 'cash')]).ids
            bank_journals = journal_obj.search([('type', '=', 'bank')]).ids
            domain = [('account_id', '=', payment.partner_id.property_account_receivable_id.id),
                      ('partner_id', '=', payment.partner_id.id),
                      ('move_id.state', '=', 'posted'),
                      ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                      ('amount_residual_currency', '!=', 0.0),
                      ('credit', '>', 0), ('debit', '=', 0)]
            amount_to_show = 0
            lines = self.env['account.move.line'].search(domain)
            for line in lines:
                to_show = line.company_id.currency_id.with_context(date=line.date).compute(
                    abs(line.amount_residual), self.env.user.company_id.currency_id)
                amount_to_show += to_show

            if payment.journal_id.id in cash_journals:
                cash += payment.amount
                cash_count += 1
                pay_mode = 'cash'
            if payment.journal_id.id in bank_journals:
                credit += payment.amount
                card_count += 1
                pay_mode = 'card'
            if payment.payment_type == 'inbound':
                order_data = {
                    'name': payment.name,
                    'journal_id': payment.journal_id.name,
                    'payment_date': payment.payment_date,
                    'patient': payment.partner_id.name,
                    'type': 'out_invoice',
                    'doctor': doctor,
                    'cash': cash,
                    'credit': credit,
                    'pay_mode': pay_mode,
                    'amount': payment.amount - amount_to_show,
                    'amount_residual': amount_to_show,
                }
            else:
                if cash:
                    cash = -cash
                if credit:
                    credit = -credit
                order_data = {
                    'name': payment.name,
                    'journal_id': payment.journal_id.name,
                    'payment_date': payment.payment_date,
                    'patient': payment.partner_id.name,
                    'type': 'out_refund',
                    'doctor': doctor,
                    'cash': cash,
                    'credit': credit,
                    'pay_mode': pay_mode,
                    'amount': -payment.amount - amount_to_show,
                    'amount_residual': amount_to_show,
                }
            if order_data:
                order_list.append(order_data)
        return {
            'orders': sorted(order_list, key=lambda l: l['name']),
            'period_start': period_start,
            'period_stop': period_stop,
            'payment_mode': False,
            'cash': cash_count,
            'card': card_count,
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_adv_payment_details(data['period_start'],
                                                 data['period_stop'],
                                                 data['patient_id'],
                                                 data['patient'],
                                                 data['doctor'],
                                                 data['company_id'],
                                                 ))
        if data['period_start']:
            data['period_start'] = datetime.strptime(data['period_start'], '%Y-%m-%d')
        if data['period_stop']:
            data['period_stop'] = datetime.strptime(data['period_stop'], '%Y-%m-%d')
        return data
