# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
import base64
from odoo.tools.misc import xlwt
import io
from odoo.exceptions import Warning, UserError
from datetime import date, datetime


class SalesReportWizard(models.TransientModel):
    _name = "sale.report.wizard"

    def _get_payment_mode_id(self):
        domain = [('invoice_journal', '=', True), ('type', 'in', ('bank', 'cash')),
                  ('company_id', '=', self.company_id.id)]
        return domain

    def _get_insurance_company_id(self):
        domain = [('is_insurance_company', '=', True), ('company_id', '=', self.company_id.id)]
        return domain

    def _get_cashier_id(self):
        domain = [('company_id', '=', self.company_id.id)]
        return domain

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
                                                                                   'company_id', '=',
                                                                                   self.company_id.id)])]
        else:
            doc_ids = [x.id for x in self.env['medical.physician'].search([('company_id', '=', self.company_id.id)])]
        domain = [('id', 'in', doc_ids)]
        return domain

    is_only_doctor = fields.Boolean()
    date_type = fields.Selection([('invoice', 'Invoice Date'),
                                  ('payment', 'Payment Date')],
                                 string='Based on', required=True, default='payment')
    patient_type = fields.Selection([('self', 'Self Pay'),
                                     ('insurance', 'Insurance'),
                                     ('both', 'Self Pay & Insurance'), ],
                                    string='Patient Type', required=True, default='both')
    period_start = fields.Date("Period From", required=True, default=fields.Date.context_today)
    period_stop = fields.Date("Period To", required=True, default=fields.Date.context_today)
    doctor = fields.Many2one('medical.physician', "Doctor", domain=_get_doctor_id)
    patient = fields.Many2one('medical.patient', "Patient", domain=_get_patient_id)
    cashier = fields.Many2one('res.users', 'Cashier', domain=_get_cashier_id)
    payment_mode = fields.Many2one('account.journal', 'Payment Mode', domain=_get_payment_mode_id)
    insurance_company = fields.Many2one('res.partner', 'Insurance Company', domain=_get_insurance_company_id)
    data = fields.Binary('File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose language
                              ('get', 'get')], default='choose')
    name = fields.Char('File Name', readonly=True)

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

    @api.onchange('patient')
    def onchange_patient(self):
        if self.patient and self.patient.company_id != self.company_id:
            self.patient = False

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.doctor and self.doctor.company_id != self.company_id:
            self.doctor = False
        if self.patient and self.patient.company_id != self.company_id:
            self.patient = False
        if self.cashier and self.cashier.company_id != self.company_id:
            self.cashier = False
        if self.insurance_company and self.insurance_company.company_id != self.company_id:
            self.insurance_company = False
        if self.payment_mode and self.payment_mode.company_id != self.company_id:
            self.payment_mode = False
        doctor_domain = self._get_doctor_id()
        patient_domain = self._get_patient_id()
        cashier_domain = self._get_cashier_id()
        insurance_company_domain = self._get_insurance_company_id()
        payment_mode_domain = self._get_payment_mode_id()
        return {
            'domain': {'doctor': doctor_domain, 'patient': patient_domain, 'cashier': cashier_domain,
                       'insurance_company': insurance_company_domain, 'payment_mode': payment_mode_domain}
        }

    @api.model
    def default_get(self, fields):
        res = super(SalesReportWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        res['is_only_doctor'] = False
        self._get_doctor_id()
        self._get_patient_id()
        self._get_cashier_id()
        self._get_insurance_company_id()
        self._get_payment_mode_id()
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
    def send_sale_report(self):
        doctor = False
        payment_mode = False
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        cashier = False
        if self.cashier:
            cashier = [self.cashier.id, self.cashier.name]
        if self.payment_mode:
            payment_mode = [self.payment_mode.id, self.payment_mode.name, self.payment_mode.type]
        insurance_company = False
        if self.insurance_company:
            insurance_company = [self.insurance_company.id, self.insurance_company.name]
        patient = False
        if self.patient:
            name = self.patient.name.name
            if self.patient.patient_id:
                name = '[' + self.patient.patient_id + ']' + name
            patient = [self.patient.id, name]
        patient_type = 'Self Pay & Insurance'
        if self.patient_type == 'self':
            patient_type = 'Self Pay'
        elif self.patient_type == 'insurance':
            patient_type = 'Insurance'
        data = {
            'date_type': self.date_type,
            'patient_type': patient_type,
            'period_start': self.period_start,
            'period_stop': self.period_stop,
            'doctor': doctor,
            'patient': patient,
            'insurance_company': insurance_company,
            'payment_mode': payment_mode,
            'cashier': cashier,
            'company_id': [self.company_id.id, self.company_id.name],
        }
        report_id = 'sales_report.sales_report'
        pdf = self.env.ref(report_id).render_qweb_pdf(self.ids, data=data)
        b64_pdf = base64.b64encode(pdf[0])
        attachment_name = 'Sales Report: ' + str(self.period_start) + " To " + str(self.period_stop)
        attachment_id = self.env['ir.attachment'].create({
            'name': attachment_name,
            'type': 'binary',
            'datas': b64_pdf,
            'datas_fname': attachment_name + '.pdf',
            # 'store_fname': attachment_name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
        attach = {
            attachment_id.id,
        }
        user = self.env['res.users'].browse(SUPERUSER_ID)
        from_email = user.partner_id.email
        mail_values = {
            'reply_to': from_email,
            'email_to': from_email,
            'subject': attachment_name,
            'body_html': """<div>
            <p>Hello,</p>
            <p>This email was created automatically by Odoo H Care. Please find the attached sales reports.</p>
                            </div>
                            <div>Thank You</div>""",
            'attachment_ids': [(6, 0, attach)]
        }
        mail_id = self.env['mail.mail'].create(mail_values)
        mail_id.send()
        if mail_id.state == 'exception':
            message = mail_id.failure_reason
            raise Warning(message)
            # self.env.user.notify_warning(message, title='Mail Delivery Failed !!!', sticky=True)
        else:
            message = "Daily report mail sent successfully."
            self.env.user.notify_info(message, title='Email sent', sticky=True)

    @api.multi
    def sale_report(self):
        doctor = False
        cashier = False
        if self.cashier:
            cashier = [self.cashier.id, self.cashier.name]
        payment_mode = False
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        if self.payment_mode:
            payment_mode = [self.payment_mode.id, self.payment_mode.name, self.payment_mode.type]
        insurance_company = False
        if self.insurance_company:
            insurance_company = [self.insurance_company.id, self.insurance_company.name]
        patient = False
        if self.patient:
            name = self.patient.name.name
            if self.patient.patient_id:
                name = '[' + self.patient.patient_id + ']' + name
            patient = [self.patient.id, name]
        date_type = 'Invoice Date'
        if self.date_type == 'payment':
            date_type = 'Payment Date'
        patient_type = 'Self Pay & Insurance'
        if self.patient_type == 'self':
            patient_type = 'Self Pay'
        elif self.patient_type == 'insurance':
            patient_type = 'Insurance'
        data = {
            'date_type': date_type,
            'patient_type': patient_type,
            'period_start': self.period_start,
            'period_stop': self.period_stop,
            'doctor': doctor,
            'patient': patient,
            'insurance_company': insurance_company,
            'payment_mode': payment_mode,
            'cashier': cashier,
            'company_id': [self.company_id.id, self.company_id.name],
        }
        return self.env.ref('sales_report.sales_report').report_action(self, data=data)

    @api.model
    def get_sale_details(self, date_type=False, patient_type=False, period_start=False, period_stop=False, doctor=False,
                         patient=False,
                         insurance_company=False, payment_mode=False, cashier=False, company_id=False):
        journal_obj = self.env['account.journal']
        journal_ids = journal_obj.search([('invoice_journal', '=', True), ('company_id', '=', company_id[0])])
        jrnl_data = {}
        for j in journal_ids:
            jrnl_data[j.id] = {'name': j.name, 'sum': 0}
        if date_type == 'Invoice Date':
            dom = [
                ('date_invoice', '>=', period_start),
                ('date_invoice', '<=', period_stop),
                ('company_id', '=', company_id[0]),
                ('type', 'in', ('out_invoice', 'out_refund')),
                ('is_patient', '=', True),
                ('state', 'in', ('open', 'paid'))
            ]
            if doctor:
                dom.append(('dentist', '=', doctor[0]))
            if patient:
                dom.append(('patient', '=', patient[0]))
            if patient_type == 'Self Pay':
                dom.append(('insurance_card', '=', False))
            elif patient_type == 'Insurance':
                dom.append(('insurance_card', '!=', False))
                if insurance_company:
                    dom.append(('insurance_company', '=', insurance_company[0]))
            orders_new = self.env['account.invoice'].search(dom)
            order_list = []
            for order in orders_new:
                jrnls = {}
                for j in journal_ids:
                    jrnls[j.id] = 0
                patient_name = False
                if order.patient:
                    nam = order.patient.name.name
                    patient_name = '[' + order.patient.patient_id + ']' + nam
                result = order._get_payments_vals()
                disc_total = 0.0
                for line in order.invoice_line_ids:
                    if line.discount_value:
                        disc_total += line.discount_value
                    if line.discount:
                        disc_total += (
                                              line.price_unit * line.quantity * line.discount * line.amt_paid_by_patient) / 10000
                if order.discount_value:
                    disc_total += order.discount_value
                if order.discount:
                    order_amount_total = order.amount_untaxed + order.amount_tax
                    disc_total += (order_amount_total * order.discount or 0.0) / 100.0
                move_lin_obj = self.env['account.move.line']
                for pay in result:
                    payment_obj = move_lin_obj.browse(pay['payment_id'])
                    amt = pay['amount']
                    if payment_obj.journal_id.id in jrnl_data.keys() and payment_obj.journal_id.id in jrnls.keys():
                        if order.type == 'out_invoice':
                            jrnls[payment_obj.journal_id.id] += amt
                            jrnl_data[payment_obj.journal_id.id]['sum'] += amt
                        else:
                            jrnls[payment_obj.journal_id.id] += -1 * amt
                            jrnl_data[payment_obj.journal_id.id]['sum'] += -1 * amt

                if order.type == 'out_invoice':
                    order_data = {
                        'number': order.number,
                        'patient': patient_name,
                        'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                        'insurance_company': order.insurance_company and order.insurance_company.name or False,
                        'insurance_company_id': order.insurance_company or False,
                        'date_invoice': order.date_invoice,
                        'insurance_total': order.insurance_total,
                        'amount_total': order.amount_total,
                        'type': order.type,
                        'jrnls': jrnls,
                        'disc_total': disc_total,
                        'due': order.residual_signed,
                        'initial_amt': order.amount_total + disc_total + order.insurance_total + order.treatment_group_disc_total,
                        'treatment_group_disc_total': order.treatment_group_disc_total
                    }
                else:
                    insurance_total = amount_total = treatment_group_disc_total = 0.0
                    if order.insurance_total:
                        insurance_total = -1 * order.insurance_total
                    if order.amount_total:
                        amount_total = -1 * order.amount_total
                    if disc_total:
                        disc_total = -disc_total
                    if order.treatment_group_disc_total:
                        treatment_group_disc_total = -1 * order.treatment_group_disc_total
                    order_data = {
                        'number': order.number,
                        'patient': patient_name,
                        'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                        'insurance_company': order.insurance_company and order.insurance_company.name or False,
                        'insurance_company_id': order.insurance_company or False,
                        'date_invoice': order.date_invoice,
                        'insurance_total': insurance_total,
                        'amount_total': amount_total,
                        'type': order.type,
                        'jrnls': jrnls,
                        'disc_total': disc_total,
                        'due': order.residual_signed,
                        'initial_amt': amount_total + disc_total + insurance_total + treatment_group_disc_total,
                        'treatment_group_disc_total': treatment_group_disc_total
                    }

                order_list.append(order_data)
        else:
            dom = [
                ('payment_date', '>=', period_start),
                ('payment_date', '<=', period_stop),
                ('partner_type', '=', 'customer'),
                ('company_id', '=', company_id[0]),
                ('state', 'in', ('posted', 'reconciled'))
            ]
            if payment_mode:
                dom.append(('journal_id', '=', payment_mode[0]))
            if cashier:
                dom.append(('create_uid', '=', cashier[0]))
            payment_records = self.env['account.payment'].search(dom)
            order_list = []
            for payment in payment_records:
                if payment.journal_id.id in jrnl_data.keys():
                    order_data = {}
                    if payment.advance:
                        flag = 0
                        if patient and payment.partner_id.id != patient[0]:
                            flag = 1
                        if doctor and payment.doctor_id.id != doctor[0]:
                            flag = 1
                        if flag == 0:
                            if payment.payment_type == 'inbound':
                                jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_invoice',
                                    'journal': payment.journal_id.id,
                                    'amount': payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False,
                                    'payment_id':payment.id 
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_refund',
                                    'journal': payment.journal_id.id,
                                    'amount': -1 * payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False,
                                    'payment_id':payment.id 
                                }
                    elif len(payment.invoice_ids) == 1:
                        order = payment.invoice_ids
                        flag = 0
                        if not order.is_patient:
                            flag = 1
                        if doctor and order.dentist.id != doctor[0]:
                            flag = 1
                        if patient and order.patient.id != patient[0]:
                            flag = 1
                        if patient_type == 'Self Pay':
                            if order.insurance_company:
                                flag = 1
                        elif patient_type == 'Insurance':
                            if not order.insurance_company:
                                flag = 1
                            if insurance_company and order.insurance_company.id != insurance_company[0]:
                                flag = 1
                        order_data = {}
                        if flag == 0:
                            patient_name = False
                            if order.patient:
                                nam = order.patient.name.name
                                patient_name = '[' + order.patient.patient_id + ']' + nam
                            if order.type == 'out_invoice':
                                jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                                order_data = {
                                    'number': order.number,
                                    'bill_date': order.date_invoice,
                                    'payment_date': payment.payment_date,
                                    'patient': patient_name,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total  or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'amount': payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': order.number,
                                    'bill_date': order.date_invoice,
                                    'payment_date': payment.payment_date,
                                    'patient': patient_name,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total  or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'amount': -1 * payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }

                    else:
                        if payment.payment_type == 'inbound':
                            jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                            order_data = {
                                'number': payment.name,
                                'bill_date': "",
                                'payment_date': payment.payment_date,
                                'patient': payment.partner_id.name,
                                'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                'insurance_company': False,
                                'insurance_total': 0,
                                'insurance_company_id': False,
                                'date_invoice': False,
                                'type': 'out_invoice',
                                'journal': payment.journal_id.id,
                                'amount': payment.amount,
                                'cashier': payment.create_uid and payment.create_uid.name or False
                            }
                        else:
                            jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                            order_data = {
                                'number': payment.name,
                                'bill_date': "",
                                'payment_date': payment.payment_date,
                                'patient': payment.partner_id.name,
                                'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                'insurance_company': False,
                                'insurance_total': 0,
                                'insurance_company_id': False,
                                'date_invoice': False,
                                'type': 'out_refund',
                                'journal': payment.journal_id.id,
                                'amount': -1 * payment.amount,
                                'cashier': payment.create_uid and payment.create_uid.name or False
                            }
                    if order_data:
                        order_list.append(order_data)
        insurance_company_list = []
        insurance_company_dict = {}
        if date_type == 'Invoice Date':
            for orders in order_list:
                if orders['insurance_company_id'] and orders['insurance_company_id'] not in insurance_company_list:
                    insurance_company_list.append(orders['insurance_company_id'])
                    insurance_company_dict[orders['insurance_company_id'].id] = {
                                                                         'name': orders['insurance_company_id'].name,
                                                                         'id': orders['insurance_company_id'].id,
                                                                         'patient_share': 0.0,
                                                                         'insurance_share': 0.0,
                                                                         'total': 0.0 }
            for insur in insurance_company_dict:
                for orders in order_list:
                    if orders['insurance_company_id'] and insur == orders['insurance_company_id'].id:
                        insurance_company_dict[insur]['patient_share'] += orders['amount_total']
                        insurance_company_dict[insur]['insurance_share'] += orders['insurance_total']
                        # total = orders['amount_total'] + orders['insurance_total']
                        total = orders['initial_amt']
                        insurance_company_dict[insur]['total'] += orders['amount_total'] + orders['insurance_total']

        # else:
        #     for order in order_list:
        #         if order.get('insurance_company') and order.get('insurance_company') not in insurance_company_dict:
        #             insurance_company_dict.update({order.get('insurance_company'): order.get(
        #                 'insurance_total') if order.get('type') == 'out_invoice' else -1 * order.get(
        #                 'insurance_total')})
        #         else:
        #             if order.get('insurance_company',False):
        #                 if order.get('type') == 'out_invoice':
        #                     insurance_company_dict[order.get('insurance_company')] += order.get('insurance_total')
        #                 elif order.get('type') == 'out_refund':
        #                     insurance_company_dict[order.get('insurance_company')] -= order.get('insurance_total')
        return {
            'insurance_company_dict': insurance_company_dict,
            'orders': sorted(order_list, key=lambda l: l['number']),
            'jrnl_data': jrnl_data,
            'flag': 4
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_sale_details(data['date_type'],
                                          data['patient_type'],
                                          data['period_start'],
                                          data['period_stop'],
                                          data['doctor'], data['patient'],
                                          data['insurance_company'],
                                          data['payment_mode'],
                                          data['cashier'],
                                          data['company_id']))
        # data['period_start'] = datetime.strptime(data['period_start'], '%Y-%m-%d')
        # data['period_stop'] = datetime.strptime(data['period_stop'], '%Y-%m-%d')
        return data

    @api.multi
    def generate_backlog_excel_report(self):
        doctor = False
        cashier = False
        if self.cashier:
            cashier = [self.cashier.id, self.cashier.name]
        payment_mode = False
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        if self.payment_mode:
            payment_mode = [self.payment_mode.id, self.payment_mode.name, self.payment_mode.type]
        insurance_company = False
        if self.insurance_company:
            insurance_company = [self.insurance_company.id, self.insurance_company.name]
        patient = False
        if self.patient:
            name = self.patient.name.name
            if self.patient.patient_id:
                name = '[' + self.patient.patient_id + ']' + name
            patient = [self.patient.id, name]
        date_type = 'Invoice Date'
        if self.date_type == 'payment':
            date_type = 'Payment Date'
        patient_type = 'Self Pay & Insurance'
        if self.patient_type == 'self':
            patient_type = 'Self Pay'
        elif self.patient_type == 'insurance':
            patient_type = 'Insurance'
        wiz_date_start = self.period_start
        wiz_date_end = self.period_stop
        if not wiz_date_start:
            raise UserError(_('Please enter Period From'))
        if not wiz_date_end:
            raise UserError(_('Please enter Period To'))
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('SALES REPORT SUMMARY')
        bold_teal = xlwt.easyxf("font: bold on, color teal_ega;")
        style_head = xlwt.easyxf('alignment: wrap True;'
                                "pattern: pattern solid, fore-colour teal_ega; "
                                "font: name Times New Roman, color white, bold on;"
                                "align: horiz center, vert center; "
                                "borders: left thin, right thin, top thin, bottom medium;"
                                )
        bold_main = xlwt.easyxf("font: bold on; ")
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, bold on, color black;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;"
                                          , num_format_str='#,##0.00')
        bold_2_decimal = xlwt.easyxf(
                                    "pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, bold on, color black;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;"
                                          , num_format_str='#,##0.00')
        bold_red = xlwt.easyxf(
                                "pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, bold on, color red;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;"
                                )
        bold_2_decimal_red = xlwt.easyxf(
                                        "pattern: pattern solid, fore-colour white; "
                                        "font: name Times New Roman, color red, bold on;"
                                        "align: horiz center, vert center; "
                                        "borders: left thin, right thin, top thin, bottom medium;"
                                        , num_format_str='#,##0.00')
        bold_2_decimal_red_center = xlwt.easyxf(
                                    "pattern: pattern solid, fore-colour white; "
                                  "font: name Times New Roman, color red, bold on;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;"
                                  , num_format_str='#,##0.00')
        r = 0
        c = 3
        company_name = self.env.user.company_id.name 
        title = xlwt.easyxf("font: name Times New Roman,height 300, color teal_ega, bold True, name Arial;"
                            " align: horiz center, vert center;")
        title_black = xlwt.easyxf("font: name Times New Roman,height 300, color black, name Arial;"
                            " align: horiz center, vert center;")
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour teal_ega; "
                                  "font: name Times New Roman, color white, bold on;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;")
        bold_border_total = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                  "font: name Times New Roman, color black, bold on;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;")
        bold_border_right_thin_avoid = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                  "font: name Times New Roman, color black, bold on;"
                                  "align: horiz right, vert center; "
                                  "borders: left thin, top thin, bottom medium;")
        bold_border_left_thin_avoid = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                                   "font: name Times New Roman, color black, bold on;"
                                                   "align: horiz center, vert center; "
                                                   "borders: top thin, bottom medium;")
        bold_no_border_center = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                  "font: name Times New Roman, color black;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;"
                                  , num_format_str='#,##0.00')
        bold_no_border_center_bold = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                  "font: name Times New Roman, bold on, color black;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;"
                                  , num_format_str='#,##0.00')
        bold_no_border_right = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                     "font: name Times New Roman, color black;"
                                     "align: horiz right, vert center; "
                                     "borders: left thin, right thin, top thin, bottom medium;")
        bold_no_border_left = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, color black;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;"
                                          , num_format_str='#,##0.00')
        bold_no_border_left_bold = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, bold on, color black;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;"
                                          , num_format_str='#,##0.00')
        worksheet.write(r, c, company_name, title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 3
        worksheet.write(r, c, 'SALES REPORT SUMMARY', title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 2
        c = 0
        start_date = (datetime.strptime(self.period_start, '%Y-%m-%d'))
        start_date = start_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        end_date = (datetime.strptime(self.period_stop, '%Y-%m-%d'))
        end_date = end_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        output_header = ['From:', start_date, ' ',' ',' ','To:', end_date]
        for item in output_header:
            if item == 'From:' or item == 'To:':
                worksheet.write(r, c, item, bold_teal)
            else:
                worksheet.write(r, c, item, bold_main)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 1
        c = 0
        output_header = ['Based on:', date_type, ' ',' ', ' ','Doctor:', doctor]
        for item in output_header:
            if item == 'Based on:' or item == 'Doctor:':
                worksheet.write(r, c, item, bold_teal)
            elif item == doctor and not self.doctor: 
                worksheet.write(r, c, 'All', bold_main)
            elif item == doctor and self.doctor:
                worksheet.write(r, c, doctor[1], bold_main)
            else:
                worksheet.write(r, c, item, bold_main)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 1
        c = 0
        output_header = ['Insurance Company:', insurance_company, ' ',' ',' ','Patient:', patient]
        for item in output_header:
            if item == 'Insurance Company:' or item == 'Patient:':
                worksheet.write(r, c, item, bold_teal)
            elif (item == insurance_company and not self.insurance_company) or (item == patient and not self.patient): 
                worksheet.write(r, c, 'All', bold_main)
            elif item == insurance_company and self.insurance_company:
                worksheet.write(r, c, insurance_company[1], bold_main) 
            elif item == patient and self.patient:
                worksheet.write(r, c, patient[1], bold_main)
            else:
                worksheet.write(r, c, item, bold_main)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 1
        c = 0
        output_header = ['Cashier:', self.cashier, ' ',  ' ' ,' ','Payment Mode:', self.payment_mode]
        for item in output_header:
            if item == 'Cashier:':
                worksheet.write(r, c, item, bold_teal)
            elif date_type != 'Invoice Date' and item == 'Payment Mode:':
                 worksheet.write(r, c, item, bold_teal)
            elif date_type != 'Invoice Date' and item == self.payment_mode and not self.payment_mode:
                worksheet.write(r, c, 'All', bold_main)
            elif not self.cashier and item == self.cashier:
                worksheet.write(r, c, 'All', bold_main)
            elif item == self.cashier and self.cashier:
                worksheet.write(r, c, cashier[1], bold_main)
            elif date_type != 'Invoice Date' and item == self.payment_mode and self.payment_mode:
                worksheet.write(r, c, payment_mode[1], bold_main)
            elif item == ' ':
                worksheet.write(r, c, item, bold_main)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 2
        c = 0
        res = {}
        period_start = self.period_start
        period_stop = self.period_stop
        res = self.get_sale_details(date_type,patient_type,self.period_start,self.period_stop,doctor,patient,insurance_company,payment_mode,cashier,company_id=[self.company_id.id, self.company_id.name])
        if date_type == 'Invoice Date':
            output_header = ['Sl No.', 'Bill Ref', 'Patient', 'Doctor', 'Insurance Company', 'Bill Amount', 'Insurance Company Payment', 'Treatment Group Discount', 'Clinic Discount', 'Total Amount', 'Pay By ', 'Due Amount']
            for item in output_header:
                if not self.doctor and item == 'Doctor':
                    worksheet.write_merge(r, r+1, c, c, 'Doctor', bold_border)
                    c += 1
                if not self.patient and item == 'Patient':
                    worksheet.write_merge(r, r+1, c, c, 'Patient', bold_border)
                    c += 1
                if not self.insurance_company and item == 'Insurance Company':
                    worksheet.write_merge(r, r+1, c, c, 'Insurance Company', bold_border)
                    c += 1
                elif item == 'Pay By ':
                    for j in res['jrnl_data']:
                        worksheet.write_merge(r, r+1, c, c, item + res['jrnl_data'][j]['name'], bold_border)
                        c += 1
                elif item == 'Due Amount':
                    worksheet.write_merge(r, r+1, c, c, item, bold_border)
                    c += 1
                elif item == 'Sl No.' or item == 'Bill Ref' or item == 'Bill Amount' or item == 'Insurance Company Payment' or item == 'Treatment Group Discount' or item == 'Clinic Discount' or item == 'Total Amount':
                    worksheet.write_merge(r, r+1, c, c, item, bold_border)
                    c += 1
                if item == 'Sl No.':
                    col.width = 100 * 4
                elif item in ('Patient'):
                    col.width = 2500 * 4
                elif item in ('Doctor'):
                    col.width = 2000 * 4
                else:
                    col.width = 850 * 4
                col = worksheet.col(c)
            r += 1
            c = 0
            i = 1
            initial_sum = 0
            due_sum = 0
            insurance_sum = 0
            treatment_sum = 0
            disc_sum = 0
            amount_sum = 0
            for l in res['orders']:
                if l['type'] == 'out_refund':
                    r += 1
                    worksheet.write(r, c, str(i), bold_red)
                    i += 1
                    c += 1
                    worksheet.write(r, c, l['number'], bold_red)
                    c += 1
                    if not self.patient:
                        worksheet.write(r, c, l['patient'], bold_red)
                        c += 1
                    if not self.doctor:
                        if l['doctor']:
                            worksheet.write(r, c, l['doctor'], bold_red)
                        else:
                            worksheet.write(r, c, '', bold_red)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_company']:
                            worksheet.write(r, c, l['insurance_company'], bold_red)
                        else:
                            worksheet.write(r, c, '', bold_red)
                        c += 1
                    if l['initial_amt']:
                        worksheet.write(r, c, l['initial_amt'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal_red)
                    c += 1
                    initial_sum = initial_sum+l['initial_amt']
                    if l['insurance_total']:
                        worksheet.write(r, c, l['insurance_total'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, l['insurance_total'], bold_2_decimal_red)
                    c += 1
                    insurance_sum = insurance_sum+l['insurance_total']
                    if l['treatment_group_disc_total']:
                        worksheet.write(r, c, l['treatment_group_disc_total'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal_red)
                    c += 1
                    treatment_sum = treatment_sum+l['treatment_group_disc_total']
                    if l['disc_total']:
                        worksheet.write(r, c, l['disc_total'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal_red)
                    c += 1
                    disc_sum = disc_sum+l['disc_total']
                    if l['amount_total']:
                        worksheet.write(r, c, l['amount_total'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal_red)
                    c += 1
                    amount_sum = amount_sum+l['amount_total']
                    for j in res['jrnl_data']:
                        if l['jrnls'][j]:
                            worksheet.write(r, c, l['jrnls'][j], bold_2_decimal_red)
                        else:
                            worksheet.write(r, c, '', bold_2_decimal_red)
                        c += 1
                    if l['due']:
                        worksheet.write(r, c, l['due'], bold_2_decimal_red)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal_red)
                    c += 1
                    due_sum = due_sum+l['due']
                else:
                    r+=1
                    worksheet.write(r, c, str(i), bold)
                    i += 1
                    c += 1
                    worksheet.write(r, c, l['number'], bold)
                    c += 1
                    if not self.patient:
                        worksheet.write(r, c, l['patient'], bold)
                        c += 1
                    if not self.doctor:
                        if l['doctor']:
                            worksheet.write(r, c, l['doctor'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_company']:
                            worksheet.write(r, c, l['insurance_company'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if l['initial_amt']:
                        worksheet.write(r, c, l['initial_amt'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    c += 1
                    initial_sum = initial_sum+l['initial_amt']
                    if l['insurance_total']:
                        worksheet.write(r, c, l['insurance_total'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    c += 1
                    insurance_sum = insurance_sum+l['insurance_total']
                    if  l['treatment_group_disc_total']:
                        worksheet.write(r, c, l['treatment_group_disc_total'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    c += 1
                    treatment_sum = treatment_sum+l['treatment_group_disc_total']
                    if l['disc_total']:
                        worksheet.write(r, c, l['disc_total'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    c += 1
                    disc_sum = disc_sum+l['disc_total']
                    if l['amount_total']:
                        worksheet.write(r, c, l['amount_total'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    c += 1
                    amount_sum = amount_sum+l['amount_total']
                    for j in res['jrnl_data']:
                        if l['jrnls'][j]:
                            worksheet.write(r, c, l['jrnls'][j], bold_2_decimal)
                        else:
                            worksheet.write(r, c, '', bold_2_decimal)
                        c += 1
                    if l['due']:
                        worksheet.write(r, c, l['due'], bold_2_decimal)
                    else:
                        worksheet.write(r, c, '', bold_2_decimal)
                    due_sum = due_sum+l['due']
                # r += 1
                c = 0
            r += 1
            c = 0
            if not self.doctor:
                c += 1
            if not self.patient:
                c  += 1
            if not self.insurance_company:
                c += 1
            worksheet.write_merge(r, r, 0, c+1, 'Total :', bold_border_total)
            worksheet.write(r, c+2, initial_sum, bold_no_border_left_bold)
            worksheet.write(r, c+3, insurance_sum, bold_no_border_left_bold)
            worksheet.write(r, c+4, treatment_sum, bold_no_border_left_bold)
            worksheet.write(r, c+5, disc_sum, bold_no_border_left_bold)
            worksheet.write(r, c+6, amount_sum, bold_no_border_left_bold)
            c += 7
            for j in res['jrnl_data']:
                worksheet.write(r, c, res['jrnl_data'][j]['sum'], bold_2_decimal_red_center)
                c += 1
            worksheet.write(r, c, due_sum, bold_no_border_left_bold)
            r += 2
            c = 2
            worksheet.write(r, c,'Payment mode Summary', title_black)
            col = worksheet.col(c)
            # col.width = 900 * 3
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 3
            r += 2
            c = 1
            output_header=['Name','Amount']
            for item in output_header:
                worksheet.write(r, c, item, bold_no_border_left_bold)
                col = worksheet.col(c)
                # col.width = 850 * 4
                c += 1
            r += 1
            c = 1
            amount_sum = 0
            for j in res['jrnl_data']:
                worksheet.write(r, c, res['jrnl_data'][j]['name'], bold_no_border_left)
                worksheet.write(r, c+1, res['jrnl_data'][j]['sum'], bold_no_border_left)
                amount_sum = amount_sum + res['jrnl_data'][j]['sum']
                r += 1
                c = 1
            # r += 1
            c = 1
            if patient_type != 'Self Pay':
                worksheet.write(r, c, 'Insurance', bold_no_border_left)
                worksheet.write(r, c+1, insurance_sum, bold_no_border_left)
                amount_sum = amount_sum + insurance_sum
                r += 1
            c = 1
            worksheet.write(r, c, 'Total :', bold_no_border_left)
            worksheet.write(r, c+1, amount_sum, bold_no_border_left)
            r += 2
            c = 2
            if patient_type != 'Self Pay':
                worksheet.write(r, c, 'Insurance Company Summary', title_black)
                col = worksheet.col(c)
                # col.width = 900 * 3
                worksheet.row(r).height_mismatch = True
                worksheet.row(r).height = 200 * 3
                sum_patient_share = 0.0
                sum_insurance_share = 0.0
                sum_total_share = 0.0
                r += 2
                c = 1
                output_header = ['Company Name', 'Patient Share', 'Insurance Share', 'Total']
                for item in output_header:
                    worksheet.write(r, c, item, bold_no_border_left_bold)
                    c += 1
                r += 1
                c = 1
                for key,insurance_com_value in res['insurance_company_dict'].items():
                    worksheet.write(r, c, insurance_com_value['name'], bold_no_border_left)
                    c += 1
                    worksheet.write(r, c, insurance_com_value['patient_share'], bold_no_border_left)
                    c += 1
                    sum_patient_share = sum_patient_share+insurance_com_value['patient_share']
                    worksheet.write(r, c, insurance_com_value['insurance_share'], bold_no_border_left)
                    c += 1
                    sum_insurance_share = sum_insurance_share+insurance_com_value['insurance_share']
                    worksheet.write(r, c, insurance_com_value['total'], bold_no_border_left)
                    c += 1
                    sum_total_share = sum_total_share+insurance_com_value['total']
                    r += 1
                    c = 1
                worksheet.write(r, c, 'Total :', bold_no_border_left)
                worksheet.write(r, c+1, sum_patient_share, bold_no_border_left)
                worksheet.write(r, c+2, sum_insurance_share, bold_no_border_left)
                worksheet.write(r, c+3, sum_total_share, bold_no_border_left)
        else:
            r += 2
            c = 0
            count = 0
            output_header=['Sl No','Bill Ref','Bill Date','Payment Date','Patient','Doctor','Cashier','Insurance Company','Insurance Total','Pay By ']
            for item in output_header:
                if item == 'Sl No':
                    col.width = 100 * 4
                elif item == 'Patient':
                    col.width = 2500 * 4
                elif item in ('Doctor','Cashier'):
                    col.width = 1500 * 4
                else:
                    col.width = 850 * 4
                if not self.doctor and item == 'Doctor':
                    worksheet.write_merge(r, r+1, c, c, 'Doctor', bold_border)
                    c += 1
                elif not self.patient and item == 'Patient':
                    worksheet.write_merge(r, r+1, c, c, 'Patient', bold_border)
                    c += 1
                elif not self.cashier and item == 'Cashier':
                    worksheet.write_merge(r, r+1, c, c, 'Cashier', bold_border)
                    c += 1
                elif not self.insurance_company and item == 'Insurance Company':
                    worksheet.write_merge(r, r+1, c, c, 'Insurance Company', bold_border)
                    c += 1
                elif not self.insurance_company and item == 'Insurance Total':
                    worksheet.write_merge(r, r+1, c, c, 'Insurance Total', bold_border)
                    c += 1
                elif item == 'Pay By ':
                    for j in res['jrnl_data']:
                        worksheet.write_merge(r, r+1, c, c, item + res['jrnl_data'][j]['name'], bold_border)
                        c += 1
                elif item == 'Sl No' or item == 'Bill Ref' or item == 'Bill Date' or item == 'Payment Date':
                    worksheet.write_merge(r, r+1, c, c, item, bold_border)
                    c += 1
                col = worksheet.col(c)

                # c += 1
            c = 0
            r += 2
            i = 1
            total = 0
            insurance_total = 0
            for l in res['orders']:
                c = 0
                if l['type'] == 'out_refund':
                    worksheet.write(r, c, str(i), bold)
                    c += 1
                    i += 1
                    worksheet.write(r, c, l['number'], bold)
                    c += 1
                    worksheet.write(r, c, l['bill_date'], bold)
                    c += 1
                    worksheet.write(r, c, l['payment_date'], bold)
                    c += 1
                    if not self.patient:
                        worksheet.write(r, c, l['patient'], bold)
                        c += 1
                    if not self.doctor:
                        if l['doctor']:
                            worksheet.write(r, c, l['doctor'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if not self.cashier:
                        worksheet.write(r, c, l['cashier'], bold)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_company']:
                            worksheet.write(r, c, l['insurance_company'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_total']:
                            worksheet.write(r, c, l['insurance_total'], bold)
                            insurance_total+=l['insurance_total']
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    for j in res['jrnl_data']:
                        if l['journal'] == j:
                            worksheet.write(r, c, l['amount'], bold_2_decimal)
                        else:
                            worksheet.write(r, c, '', bold_2_decimal)
                        c += 1
                else:
                    worksheet.write(r, c, str(i), bold)
                    c += 1
                    i += 1
                    worksheet.write(r, c, l['number'], bold)
                    c += 1
                    worksheet.write(r, c, l['bill_date'], bold)
                    c += 1
                    worksheet.write(r, c, l['payment_date'], bold)
                    c += 1
                    if not self.patient:
                        worksheet.write(r, c, l['patient'], bold)
                        c += 1
                    if not self.doctor:
                        if l['doctor']:
                            worksheet.write(r, c, l['doctor'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if not self.cashier:
                        worksheet.write(r, c, l['cashier'], bold)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_company']:
                            worksheet.write(r, c, l['insurance_company'], bold)
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    if not self.insurance_company:
                        if l['insurance_total']:
                            worksheet.write(r, c, l['insurance_total'], bold)
                            insurance_total+=l['insurance_total']
                        else:
                            worksheet.write(r, c, '', bold)
                        c += 1
                    for j in res['jrnl_data']:
                        if l['journal'] == j:
                            worksheet.write(r, c, l['amount'], bold_2_decimal)
                        else:
                            worksheet.write(r, c, '', bold_2_decimal)
                        c += 1
                r += 1
            c = 0
            if not self.patient:
                c += 1
            if not self.doctor:
                c += 1
            if not self.cashier:
                c += 1
            if not self.insurance_company:
                c += 1
            worksheet.write_merge(r, r+2, 0, c+3, 'Total :', bold_border_total)
            c += 4
            m = c
            count = 0
            worksheet.write_merge(r,r+2, c,c, insurance_total, bold_no_border_center_bold)
            c+=1
            for j in res['jrnl_data']:
                worksheet.write(r, c, res['jrnl_data'][j]['sum'], bold_no_border_center_bold)
                total = total+res['jrnl_data'][j]['sum']
                count += 1
                c += 1
            r += 1
            if total :
                worksheet.write_merge(r, r+1, m+1, c-1, total, bold_no_border_center_bold)

            r += 2
            worksheet.write(r, 4, "Payment Summary", bold)
            r += 1
            worksheet.write(r, 4, "Method", bold)
            worksheet.write(r, 5, "Amount", bold)


            for j in res['jrnl_data']:
                r+=1
                worksheet.write(r, 4, res['jrnl_data'][j]['name'], bold)
                worksheet.write(r, 5, res['jrnl_data'][j]['sum'], bold_2_decimal)

            for i in res['insurance_company_dict']:
                r+=1
                worksheet.write(r, 4, i, bold)
                worksheet.write(r, 5, res['insurance_company_dict'][i], bold_2_decimal)




        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "SALES REPORT.xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class ReportSale(models.AbstractModel):
    _name = 'report.sales_report.sales_report_pdf'

    @api.model
    def get_sale_details(self, date_type=False, patient_type=False, period_start=False, period_stop=False, doctor=False,
                         patient=False,
                         insurance_company=False, payment_mode=False, cashier=False, company_id=False):
        journal_obj = self.env['account.journal']
        journal_ids = journal_obj.search([('invoice_journal', '=', True), ('company_id', '=', company_id[0])])
        jrnl_data = {}
        for j in journal_ids:
            jrnl_data[j.id] = {'name': j.name, 'sum': 0}
        if date_type == 'Invoice Date':
            dom = [
                ('date_invoice', '>=', period_start),
                ('date_invoice', '<=', period_stop),
                ('company_id', '=', company_id[0]),
                ('type', 'in', ('out_invoice', 'out_refund')),
                ('is_patient', '=', True),
                ('state', 'in', ('open', 'paid'))
            ]
            if doctor:
                dom.append(('dentist', '=', doctor[0]))
            if patient:
                dom.append(('patient', '=', patient[0]))
            if patient_type == 'Self Pay':
                dom.append(('insurance_card', '=', False))
            elif patient_type == 'Insurance':
                dom.append(('insurance_card', '!=', False))
                if insurance_company:
                    dom.append(('insurance_company', '=', insurance_company[0]))
            orders_new = self.env['account.invoice'].search(dom)
            order_list = []
            for order in orders_new:
                jrnls = {}
                for j in journal_ids:
                    jrnls[j.id] = 0
                patient_name = False
                if order.patient:
                    nam = order.patient.name.name
                    patient_name = '[' + order.patient.patient_id + ']' + nam
                result = order._get_payments_vals()
                disc_total = 0.0
                for line in order.invoice_line_ids:
                    if line.discount_value:
                        disc_total += line.discount_value
                    if line.discount:
                        disc_total += (
                                              line.price_unit * line.quantity * line.discount * line.amt_paid_by_patient) / 10000
                if order.discount_value:
                    disc_total += order.discount_value
                if order.discount:
                    order_amount_total = order.amount_untaxed + order.amount_tax
                    disc_total += (order_amount_total * order.discount or 0.0) / 100.0
                move_lin_obj = self.env['account.move.line']
                for pay in result:
                    payment_obj = move_lin_obj.browse(pay['payment_id'])
                    amt = pay['amount']
                    if payment_obj.journal_id.id in jrnl_data.keys() and payment_obj.journal_id.id in jrnls.keys():
                        if order.type == 'out_invoice':
                            jrnls[payment_obj.journal_id.id] += amt
                            jrnl_data[payment_obj.journal_id.id]['sum'] += amt
                        else:
                            jrnls[payment_obj.journal_id.id] += -1 * amt
                            jrnl_data[payment_obj.journal_id.id]['sum'] += -1 * amt

                if order.type == 'out_invoice':
                    order_data = {
                        'number': order.number,
                        'bill_date': order.appt_id.appointment_sdate if order.appt_id else " ",
                        'patient': patient_name,
                        'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                        'insurance_company': order.insurance_company and order.insurance_company.name or False,
                        'insurance_company_id': order.insurance_company or False,
                        'date_invoice': order.date_invoice,
                        'insurance_total': order.insurance_total,
                        'amount_total': order.amount_total,
                        'type': order.type,
                        'jrnls': jrnls,
                        'disc_total': disc_total,
                        'due': order.residual_signed,
                        'initial_amt': order.amount_total + disc_total + order.insurance_total + order.treatment_group_disc_total,
                        'treatment_group_disc_total': order.treatment_group_disc_total
                    }
                else:
                    insurance_total = amount_total = treatment_group_disc_total = 0.0
                    if order.insurance_total:
                        insurance_total = -1 * order.insurance_total
                    if order.amount_total:
                        amount_total = -1 * order.amount_total
                    if disc_total:
                        disc_total = -disc_total
                    if order.treatment_group_disc_total:
                        treatment_group_disc_total = -1 * order.treatment_group_disc_total
                    order_data = {
                        'number': order.number,
                        'bill_date': order.appt_id.appointment_sdate if order.appt_id else " ",
                        'patient': patient_name,
                        'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                        'insurance_company': order.insurance_company and order.insurance_company.name or False,
                        'insurance_company_id': order.insurance_company or False,
                        'date_invoice': order.date_invoice,
                        'insurance_total': insurance_total,
                        'amount_total': amount_total,
                        'type': order.type,
                        'jrnls': jrnls,
                        'disc_total': disc_total,
                        'due': order.residual_signed,
                        'initial_amt': amount_total + disc_total + insurance_total + treatment_group_disc_total,
                        'treatment_group_disc_total': treatment_group_disc_total
                    }

                order_list.append(order_data)
        else:
            dom = [
                ('payment_date', '>=', period_start),
                ('payment_date', '<=', period_stop),
                ('partner_type', '=', 'customer'),
                ('company_id', '=', company_id[0]),
                ('state', 'in', ('posted', 'reconciled'))
            ]
            if payment_mode:
                dom.append(('journal_id', '=', payment_mode[0]))
            if cashier:
                dom.append(('create_uid', '=', cashier[0]))
            payment_records = self.env['account.payment'].search(dom)
            order_list = []
            for payment in payment_records:
                if payment.journal_id.id in jrnl_data.keys():
                    order_data = {}
                    if payment.advance:
                        flag = 0
                        if patient and payment.partner_id.id != patient[0]:
                            flag = 1
                        if doctor and payment.doctor_id.id != doctor[0]:
                            flag = 1
                        if flag == 0:
                            if payment.payment_type == 'inbound':
                                jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_invoice',
                                    'journal': payment.journal_id.id,
                                    'amount': payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False,
                                    'payment_id':payment.id 
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_refund',
                                    'journal': payment.journal_id.id,
                                    'amount': -1 * payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False,
                                    'payment_id':payment.id 
                                }
                    elif len(payment.invoice_ids) == 1:
                        order = payment.invoice_ids
                        flag = 0
                        if not order.is_patient:
                            flag = 1
                        if doctor and order.dentist.id != doctor[0]:
                            flag = 1
                        if patient and order.patient.id != patient[0]:
                            flag = 1
                        if patient_type == 'Self Pay':
                            if order.insurance_company:
                                flag = 1
                        elif patient_type == 'Insurance':
                            if not order.insurance_company:
                                flag = 1
                            if insurance_company and order.insurance_company.id != insurance_company[0]:
                                flag = 1
                        order_data = {}
                        if flag == 0:
                            patient_name = False
                            if order.patient:
                                nam = order.patient.name.name
                                patient_name = '[' + order.patient.patient_id + ']' + nam
                            if order.type == 'out_invoice':
                                jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                                order_data = {
                                    'number': order.number,
                                    'bill_date': order.date_invoice,
                                    'payment_date': payment.payment_date,
                                    'patient': patient_name,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'amount': payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': order.number,
                                    'bill_date': order.date_invoice,
                                    'payment_date': payment.payment_date,
                                    'patient': patient_name,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'amount': -1 * payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }

                    else:
                        
                        flag = 0
                        if doctor:
                            if not payment.doctor_id:
                                flag = 1
                            if payment.doctor_id and payment.doctor_id != doctor[0]:
                                flag = 1
                        if flag == 0:
                            if payment.payment_type == 'inbound':
                                jrnl_data[payment.journal_id.id]['sum'] += payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_invoice',
                                    'journal': payment.journal_id.id,
                                    'amount': payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_refund',
                                    'journal': payment.journal_id.id,
                                    'amount': -1 * payment.amount,
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                    if order_data:
                        order_list.append(order_data)
        insurance_company_list = []
        insurance_company_dict = {}
        if date_type == 'Invoice Date':
            for orders in order_list:
                if orders['insurance_company_id'] and orders['insurance_company_id'] not in insurance_company_list:
                    insurance_company_list.append(orders['insurance_company_id'])
                    insurance_company_dict[orders['insurance_company_id'].id] = {
                                                                         'name': orders['insurance_company_id'].name,
                                                                         'id': orders['insurance_company_id'].id,
                                                                         'patient_share': 0.0,
                                                                         'insurance_share': 0.0,
                                                                         'total': 0.0 }
            for insur in insurance_company_dict:
                for orders in order_list:
                    if orders['insurance_company_id'] and insur == orders['insurance_company_id'].id:
                        insurance_company_dict[insur]['patient_share'] += orders['amount_total']
                        insurance_company_dict[insur]['insurance_share'] += orders['insurance_total']
                        # total = orders['amount_total'] + orders['insurance_total']
                        total = orders['initial_amt']
                        insurance_company_dict[insur]['total'] += orders['amount_total'] + orders['insurance_total']
        # else:
        #     for order in order_list:
        #         if order.get('insurance_company') and order.get('insurance_company') not in insurance_company_dict:
        #             insurance_company_dict.update({order.get('insurance_company'):order.get('insurance_total') if order.get('type') == 'out_invoice' else -1*order.get('insurance_total')})
        #         else:
        #             if order.get('insurance_company',False):
        #                 if order.get('type') == 'out_invoice':
        #                     insurance_company_dict[order.get('insurance_company')] += order.get('insurance_total')
        #                 elif order.get('type') == 'out_refund':
        #                     insurance_company_dict[order.get('insurance_company')] -= order.get('insurance_total')
        return {
            'insurance_company_dict': insurance_company_dict,
            'orders': sorted(order_list, key=lambda l: l['number']),
            'jrnl_data': jrnl_data,
            'flag': 4
        }

    @api.multi
    def get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_sale_details(data['date_type'],
                                          data['patient_type'],
                                          data['period_start'],
                                          data['period_stop'],
                                          data['doctor'], data['patient'],
                                          data['insurance_company'],
                                          data['payment_mode'],
                                          data['cashier'],
                                          data['company_id']))
        # data['period_start'] = datetime.strptime(data['period_start'], '%Y-%m-%d')
        # data['period_stop'] = datetime.strptime(data['period_stop'], '%Y-%m-%d')
        return data