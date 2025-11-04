# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import base64
from odoo.tools.misc import xlwt
import io
from odoo.exceptions import UserError
from datetime import date, datetime


class RevenueExcelReportWizard(models.TransientModel):
    _name = "revenue.excel.report.wizard"

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
            doc_ids = [x.id for x in self.env['medical.physician'].search([])]
        domain = [('id', 'in', doc_ids)]
        return domain

    def _get_insurance_company_id(self):
        if self.company_id:
            domain = [('is_insurance_company', '=', True), ('company_id', '=', self.company_id.id)]
        else:
            domain = [('is_insurance_company', '=', True), ('company_id', '=', self.env.user.company_id.id)]
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

    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id.id,
                                 domain=_get_company_id, required=True)
    date_start = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    date_end = fields.Date(string="End Date", required=True, default=fields.Date.today)
    data = fields.Binary('File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose language
                              ('get', 'get')], default='choose')
    name = fields.Char('File Name', readonly=True)
    referral_dr = fields.Char('Referral Doctor', readonly=True)
    doctor = fields.Many2one('medical.physician', "Doctor", domain=_get_doctor_id)
    patient = fields.Many2one('medical.patient', "Patient", domain=_get_patient_id)
    insurance_company = fields.Many2one('res.partner', 'Insurance Company', domain=_get_insurance_company_id)
    patient_type = fields.Selection([('self', 'Self Pay'),
                                     ('insurance', 'Insurance'),
                                     ('both', 'Self Pay & Insurance'), ],
                                    string='Patient Type', required=True, default='both')
    date_type = fields.Selection([('invoice', 'Invoice Date'),
                                  ('payment', 'Payment Date')],
                                 string='Based on', default='invoice')

    def convert_date(self, date_to_convert):
        if date_to_convert:
            date_converted = (datetime.strptime(date_to_convert, '%Y-%m-%d'))
            date_converted = date_converted.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
            return date_converted
        else:
            return False

    def generate_backlog_excel_report(self):
        wiz_date_start = self.date_start
        wiz_date_end = self.date_end
        if not wiz_date_start:
            raise UserError(_('Please enter From date'))
        if not wiz_date_end:
            raise UserError(_('Please enter To date'))
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('REVENUE REPORT')
        bold = xlwt.easyxf("font: bold on;")
        r = 0
        c = 4
        company_name = self.env.user.company_id.name
        title = xlwt.easyxf("font: name Verdana,height 300, color black, bold True, name Arial;"
                            " align: horiz center, vert center;")
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour blue; "
                                  "font: name Verdana, color white, bold on;"
                                  "align: wrap on, horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;", num_format_str='#,##0.00')
        bold_border_ash = xlwt.easyxf("pattern: pattern solid, fore-colour Yellow; "
                                      "font: name Verdana, color black, bold on;"
                                      "align: horiz center, vert center; "
                                      "borders: left thin, right thin, top thin, bottom medium;",
                                      num_format_str='#,##0.00')
        bold_border_white = xlwt.easyxf("pattern: pattern solid, fore-colour White; "
                                        "font: name Verdana, color black, bold on;"
                                        "align: wrap on,horiz center, vert center; "
                                        "borders: left medium, right medium, top medium, bottom medium;",
                                        num_format_str='#,##0.00')
        bold_border_white_right = xlwt.easyxf("pattern: pattern solid, fore-colour White; "
                                              "font: name Verdana, color black, bold on;"
                                              "align: wrap on,horiz right, vert center; "
                                              "borders: left medium, right medium, top medium, bottom medium;",
                                              num_format_str='#,##0.00')
        bold_no_border_currency = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                              "font: name Verdana, color black;"
                                              "align: horiz right, vert center; "
                                              "borders: left thin, right thin, top thin, bottom medium;",
                                              num_format_str='#,##0.00')
        bold_no_border_center = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                            "font: name Verdana, color black;"
                                            "align: horiz center, vert center; "
                                            "borders: left thin, right thin, top thin, bottom medium;",
                                            num_format_str='#,##0.00')
        bold_no_border_left = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Verdana, color black;"
                                          "align: horiz left, vert center; "
                                          "borders: left thin, right thin, top thin, bottom medium;",
                                          num_format_str='#,##0.00')
        worksheet.write(r, c, company_name, title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 4
        worksheet.write(r, c, 'REVENUE REPORT', title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 2
        c = 0
        date_start = (datetime.strptime(self.date_start, '%Y-%m-%d'))
        date_start = date_start.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        date_end = (datetime.strptime(self.date_end, '%Y-%m-%d'))
        date_end = date_end.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        output_header = ['From:', date_start, ' ', ' ', ' ', 'To:', date_end]
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 860 * 4
            c += 1
        r += 2
        c = 0
        output_header = ['SL NO.', 'DATE', 'FILE.NO', 'PATIENT NAME', 'SEX', 'NATIONALITY', 'D.O.B',
                         'INSURANCE/ CASH', 'CHARGE DESCRIPTION', 'GROSS AMOUNT', 'CLINIC DISCOUNT',
                         'TREATMENT GROUP DISCOUNT', 'NET AMOUNT',
                         'PATIENT PAID AMOUNT', 'CUSTOMER TYPE', 'TREATING DOCTOR', 'REFERRAL DOCTOR', 'CASH/ CREDIT',
                         'REMARKS',
                         'INSURANCE RECEIVABLE', 'CASH RECEIVABLE', 'INVOICE #', 'NEW PATIENTS']
        for item in output_header:
            worksheet.write(r, c, item, bold_border)
            if item == 'NATIONALITY' or item == 'TREATING DOCTOR' or item == 'REFERRAL DOCTOR':
                col = worksheet.col(c)
                col.width = 1600 * 4
            if item == 'PATIENT NAME' or item == 'REMARKS':
                col = worksheet.col(c)
                col.width = 2500 * 4
            if item == 'INVOICE #':
                col = worksheet.col(c)
                col.width = 1200 * 4
            if item == 'CHARGE DESCRIPTION':
                col = worksheet.col(c)
                col.width = 5000 * 4
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 220 * 4
            c += 1
        start_date = datetime.strptime(wiz_date_start, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
        stop_date = datetime.strptime(wiz_date_end, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')
        if self.date_type == 'invoice':
            dom = [
                ('date_invoice', '>=', start_date),
                ('date_invoice', '<=', stop_date),
                ('type', 'in', ('out_invoice', 'out_refund')),
                ('is_patient', '=', True),
                ('state', 'in', ('open', 'paid'))
            ]
            if self.patient_type == 'self':
                dom.append(('insurance_card', '=', False))
            elif self.patient_type == 'insurance':
                dom.append(('insurance_card', '!=', False))
                if self.insurance_company:
                    dom.append(('insurance_company', '=', self.insurance_company.id))
    
            if self.insurance_company:
                dom.append(('insurance_company', '=', self.insurance_company.id))
            if self.doctor:
                dom.append(('dentist', '=', self.doctor.id))
            if self.patient:
                dom.append(('patient', '=', self.patient.id))
            patient_invoice = self.env['account.invoice'].search(dom, order='date_invoice desc')
    
            return_dict = {}
            for pat_inv in patient_invoice:
                return_dict[pat_inv] = {'date_invoice': "", 'file_no': "", 'patient_name': "", 'sex': "",
                                        'dob': "", 'nationality': "", 'Insurance_Cash': "", 'gross_amt': 0.0,
                                        'discount': 0.0, 'ins_discount': 0.0, 'net_amount': 0.0, 'patient_paid_amount': 0.0,
                                        'Customer_type': '',
                                        'dentist': '', 'referral_dr': "", 'cash_card': '', 'remarks': '',
                                        'insu_receivable': 0.0, 'insu_paid_amount': 0.0, 'cash_receivable': 0.0,
                                        'invoice_no': '',
                                        'new_patient': ''}
            for pat_inv in patient_invoice:
                return_dict[pat_inv]['date_invoice'] = self.convert_date(pat_inv.date_invoice)
                return_dict[pat_inv]['file_no'] = pat_inv.patient.patient_id
                return_dict[pat_inv]['patient_name'] = pat_inv.patient.patient_name
                sex = ""
                if pat_inv.patient.sex == 'f':
                    sex = 'Female'
                if pat_inv.patient.sex == 'm':
                    sex = 'Male'
                return_dict[pat_inv]['sex'] = sex
                return_dict[pat_inv]['dob'] = self.convert_date(pat_inv.patient.dob) or ''
                return_dict[pat_inv]['nationality'] = pat_inv.patient.nationality_id.name or ''
    
                if pat_inv.insurance_card:
                    return_dict[pat_inv]['Insurance_Cash'] = pat_inv.insurance_card.company_id.name
                    return_dict[pat_inv]['Customer_type'] = 'Insurance'
                else:
                    return_dict[pat_inv]['Insurance_Cash'] = 'Cash'
                    return_dict[pat_inv]['Customer_type'] = 'Selfpay'
                charge_description = ""
                for inv_lines in pat_inv.invoice_line_ids:
                    if charge_description:
                        charge_description += ", "
                    charge_description += inv_lines.product_id.name
                return_dict[pat_inv]['charge_description'] = charge_description
                return_dict[pat_inv]['gross_amt'] = pat_inv.amount_subtotal
                disc_total = 0
                for i in pat_inv.invoice_line_ids:
                    if i.discount_fixed_percent == 'Percent':
                        disc_total += (i.quantity * i.price_unit * i.discount) / 100.0
                    if i.discount_fixed_percent == 'Fixed':
                        disc_total += i.discount_value
                if pat_inv.discount_fixed_percent == 'Percent':
                    disc_total += (pat_inv.amount_untaxed + pat_inv.amount_tax) * (pat_inv.discount or 0.0 / 100.0)
                if pat_inv.discount_fixed_percent == 'Fixed':
                    disc_total += pat_inv.discount_value
    
                return_dict[pat_inv]['discount'] = disc_total
                ins_discount = 0
                if pat_inv.insurance_card:
                    ins_discount = pat_inv.amount_subtotal - pat_inv.amount_total - pat_inv.insurance_total - disc_total
                return_dict[pat_inv]['ins_discount'] = ins_discount
                return_dict[pat_inv]['net_amount'] = pat_inv.amount_total + pat_inv.insurance_total
                return_dict[pat_inv]['patient_paid_amount'] = pat_inv.amount_total - pat_inv.residual
                return_dict[pat_inv]['dentist'] = pat_inv.dentist.name.name
                pat_apt = self.env['medical.appointment'].search(
                    [('patient', '=', pat_inv.patient.patient_name), ('id', '=', pat_inv.appt_id.id),
                     ('create_date', '>=', start_date),
                     ('create_date', '<=', stop_date)])
                referal_doctor = ''
                for result in pat_apt:
                    referal_doctor = result.referral_dr_id.name or ''
                return_dict[pat_inv]['referral_dr'] = referal_doctor
                cash_card = ""
                for pay_lines in pat_inv.payment_ids:
                    if cash_card:
                        cash_card += ", "
                    cash_card += pay_lines.journal_id.name
                return_dict[pat_inv]['cash_card'] = cash_card
                return_dict[pat_inv]['remarks'] = pat_inv.note_cashier
                insu_paid_amount = 0
                insu_receivable = 0
                if pat_inv.insurance_invoice:
                    insu_receivable = pat_inv.insurance_invoice.residual
                    insu_paid_amount = pat_inv.insurance_invoice.amount_total - insu_receivable
                return_dict[pat_inv]['insu_paid_amount'] = insu_paid_amount
                return_dict[pat_inv]['insu_receivable'] = insu_receivable
                return_dict[pat_inv]['cash_receivable'] = pat_inv.residual
                return_dict[pat_inv]['invoice_no'] = pat_inv.number
                return_dict[pat_inv]['additional_remark'] = pat_inv.note_cashier or ' '
                
                is_new = not pat_inv.appt_id.is_registered
                new_patient = ''
                if is_new:
                    new_patient = 'NEW'
                return_dict[pat_inv]['new_patient'] = new_patient
            data_list = []
            sl_no = 0
            gross_amt = 0.00
            discount = 0.00
            ins_discount = 0.00
            net_amount = 0.00
            patient_paid_amount = 0.00
            insu_paid_amount = 0.00
            insu_receivable = 0.00
            cash_receivable = 0.00
            for key, value in return_dict.items():
                data = []
                sl_no += 1
                gross_amt += value['gross_amt']
                discount += value['discount']
                ins_discount += value['ins_discount']
                net_amount += value['net_amount']
                patient_paid_amount += value['patient_paid_amount']
                insu_paid_amount += value['insu_paid_amount']
                insu_receivable += value['insu_receivable']
                cash_receivable += value['cash_receivable']
                data.append(str(int(sl_no)))
                data.append(value['date_invoice'])
                data.append(value['file_no'])
                data.append(value['patient_name'])
                data.append(value['sex'])
                data.append(value['nationality'])
                data.append(value['dob'])
                data.append(value['Insurance_Cash'])
                data.append(value['charge_description'])
                data.append(value['gross_amt'])
                data.append(value['discount'])
                data.append(value['ins_discount'])
                data.append(value['net_amount'])
                data.append(value['patient_paid_amount'])
                data.append(value['Customer_type'])
                data.append(value['dentist'])
                data.append(value['referral_dr'])
                data.append(value['cash_card'])
                data.append(value['remarks'])
                data.append(value['insu_receivable'])
                data.append(value['cash_receivable'])
                data.append(value['invoice_no'])
                data.append(value['new_patient'])
                data.append(value['additional_remark'])
    
                data_list.append(data)
                r += 1
                c = 0
                for item in data:
                    if c in [9, 10, 11, 12, 13, 19, 20]:
                        worksheet.write(r, c, item, bold_no_border_currency)
                    elif c in [0, 1, 2, 4, 5, 6, 7, 14, 15, 16, 17, 18, 21, 22]:
                        worksheet.write(r, c, item or '', bold_no_border_center)
                    elif c in [3, 8]:
                        worksheet.write(r, c, item, bold_no_border_left)
                    c += 1
            r += 1
            c = 0
            output_header = ['', '', '', '', '', '', '', '', '', gross_amt, discount, ins_discount, net_amount,
                             patient_paid_amount, '', '', '', '', '', insu_receivable, cash_receivable, '', '']
            for item in output_header:
                worksheet.write(r, c, item, bold_border_ash)
                c += 1
            r += 2
            c = 1
            worksheet.write_merge(r, r, 1, 4, 'Net Collection (Cash Paid + Debit card Collection)', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, patient_paid_amount, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Net Patient Receivables', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, cash_receivable, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Net Collection (Insurance)', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, insu_paid_amount, bold_border_white_right)
            r += 1
            c = 1
            worksheet.write_merge(r, r, 1, 4, 'Net Insurance Receivables', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, insu_receivable, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Total', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, patient_paid_amount + cash_receivable + insu_paid_amount + insu_receivable,
                            bold_border_white_right)
        else:
            dom = [
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', stop_date),
                ('partner_type', '=', 'customer'),
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ('posted', 'reconciled'))
            ]
            if self.patient and self.patient.name:
                dom.append(('partner_id', '=', self.patient.name))
            payment_records = self.env['account.payment'].search(dom)
            journal_obj = self.env['account.journal']
            journal_ids = journal_obj.search([('invoice_journal', '=', True)])
            jrnl_data = {}
            for j in journal_ids:
                jrnl_data[j.id] = {'name': j.name, 'sum': 0}
            order_list = []
            doctor = [self.doctor.id] if self.doctor else []
            patient = [self.patient.id] if self.patient else []
            patient_type = self.patient_type
            insurance_company = [self.insurance_company] if self.insurance_company else []
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
                                    'patient_id': payment.partner_id.id,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_invoice',
                                    'journal': payment.journal_id.id,
                                    'journal_name':payment.journal_id.name or '',
                                    'amount': payment.amount,
                                    'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': payment.name,
                                    'bill_date': "",
                                    'payment_date': payment.payment_date,
                                    'patient': payment.partner_id.name,
                                    'patient_id': payment.partner_id.id,
                                    'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                    'insurance_company': False,
                                    'insurance_total': 0,
                                    'insurance_company_id': False,
                                    'date_invoice': False,
                                    'type': 'out_refund',
                                    'journal': payment.journal_id.id,
                                    'journal_name':payment.journal_id.name or '',
                                    'amount': -1 * payment.amount,
                                    'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
                                    'cashier': payment.create_uid and payment.create_uid.name or False
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
                        if patient_type == 'self':
                            if order.insurance_company:
                                flag = 1
                        elif patient_type == 'insurance':
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
                                    'patient_id': payment.partner_id.id,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'journal_name':payment.journal_id.name or '',
                                    'amount': payment.amount,
                                    'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
                                    'cashier': payment.create_uid and payment.create_uid.name or False
                                }
                            else:
                                jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                                order_data = {
                                    'number': order.number,
                                    'bill_date': order.date_invoice,
                                    'payment_date': payment.payment_date,
                                    'patient': patient_name,
                                    'patient_id': payment.partner_id.id,
                                    'doctor': order.dentist and order.dentist.name and order.dentist.name.name or False,
                                    'insurance_company': order.insurance_company and order.insurance_company.name or False,
                                    'insurance_total': order.insurance_total or 0,
                                    'insurance_company_id': order.insurance_company or False,
                                    'date_invoice': order.date_invoice,
                                    'type': order.type,
                                    'journal': payment.journal_id.id,
                                    'journal_name':payment.journal_id.name or '',
                                    'amount': -1 * payment.amount,
                                    'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
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
                                'patient_id': payment.partner_id.id,
                                'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                'insurance_company': False,
                                'insurance_total': 0,
                                'insurance_company_id': False,
                                'date_invoice': False,
                                'type': 'out_invoice',
                                'journal': payment.journal_id.id,
                                'journal_name':payment.journal_id.name or '',
                                'amount': payment.amount,
                                'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
                                'cashier': payment.create_uid and payment.create_uid.name or False
                            }
                        else:
                            jrnl_data[payment.journal_id.id]['sum'] += -1 * payment.amount
                            order_data = {
                                'number': payment.name,
                                'bill_date': "",
                                'payment_date': payment.payment_date,
                                'patient': payment.partner_id.name,
                                'patient_id': payment.partner_id.id,
                                'doctor': payment.doctor_id and payment.doctor_id.name and payment.doctor_id.name.name or False,
                                'insurance_company': False,
                                'insurance_total': 0,
                                'insurance_company_id': False,
                                'date_invoice': False,
                                'type': 'out_refund',
                                'journal': payment.journal_id.id,
                                'journal_name':payment.journal_id.name or '',
                                'amount': -1 * payment.amount,
                                'treatment_ids':', '.join([treatment.name for treatment in payment.treatment_ids]),
                                'cashier': payment.create_uid and payment.create_uid.name or False
                            }
                    if order_data:
                        order_list.append(order_data)
            advance_payment = 0
            return_dict = {}
            for order in order_list:
                advance_payment += 1
                patient = self.env['medical.patient'].search([('name','=',order['patient_id'])])
                if patient:
                    return_dict['advance_payment_'+str(advance_payment)] = {'date_invoice': self.convert_date(order['payment_date']), 
                                                                        'file_no': patient.patient_id, 
                                                                        'patient_name': patient.patient_name, 
                                                                        'sex': 'Female' if patient.sex == 'f' else 'Male',
                                                                        'dob': self.convert_date(patient.dob) or '', 
                                                                        'nationality': patient.nationality_id.name or '', 
                                                                        'Insurance_Cash': order['journal_name'] or '', 
                                                                        'gross_amt': 0.0,
                                                                        'discount': 0.0, 
                                                                        'ins_discount': 0.0, 
                                                                        'net_amount': order['amount'], 
                                                                        'patient_paid_amount': order['amount'], 
                                                                        'Customer_type': '',
                                                                        'dentist': order['doctor'], 
                                                                        'referral_dr': "", 
                                                                        'cash_card': order['journal_name'] or '', 
                                                                        'remarks': 'Payment',
                                                                        'insu_receivable': 0.0, 
                                                                        'insu_paid_amount': 0.0, 
                                                                        'cash_receivable': 0.0,
                                                                        'invoice_no': order['number'],
                                                                        'new_patient': '',
                                                                        'charge_description':order['treatment_ids'],
                                                                        'additional_remark':''}
            
            data_list = []
            sl_no = 0
            gross_amt = 0.00
            discount = 0.00
            ins_discount = 0.00
            net_amount = 0.00
            patient_paid_amount = 0.00
            insu_paid_amount = 0.00
            insu_receivable = 0.00
            cash_receivable = 0.00
            
            for key, value in return_dict.items():
                data = []
                sl_no += 1
                gross_amt += value['gross_amt']
                discount += value['discount']
                ins_discount += value['ins_discount']
                net_amount += value['net_amount']
                patient_paid_amount += value['patient_paid_amount']
                insu_paid_amount += value['insu_paid_amount']
                insu_receivable += value['insu_receivable']
                cash_receivable += value['cash_receivable']
                data.append(str(int(sl_no)))
                data.append(value['date_invoice'])
                data.append(value['file_no'])
                data.append(value['patient_name'])
                data.append(value['sex'])
                data.append(value['nationality'])
                data.append(value['dob'])
                data.append(value['Insurance_Cash'])
                data.append(value['charge_description'])
                data.append(value['gross_amt'])
                data.append(value['discount'])
                data.append(value['ins_discount'])
                data.append(value['net_amount'])
                data.append(value['patient_paid_amount'])
                data.append(value['Customer_type'])
                data.append(value['dentist'])
                data.append(value['referral_dr'])
                data.append(value['cash_card'])
                data.append(value['remarks'])
                data.append(value['insu_receivable'])
                data.append(value['cash_receivable'])
                data.append(value['invoice_no'])
                data.append(value['new_patient'])
                data.append(value['additional_remark'])
                data_list.append(data)
                r += 1
                c = 0
                for item in data:
                    if c in [9, 10, 11, 12, 13, 19, 20]:
                        worksheet.write(r, c, item, bold_no_border_currency)
                    elif c in [0, 1, 2, 4, 5, 6, 7, 14, 15, 16, 17, 18, 21, 22]:
                        worksheet.write(r, c, item or '', bold_no_border_center)
                    elif c in [3, 8]:
                        worksheet.write(r, c, item, bold_no_border_left)
                    c += 1
            r += 1
            c = 0
            output_header = ['', '', '', '', '', '', '', '', '', gross_amt, discount, ins_discount, net_amount,
                             patient_paid_amount, '', '', '', '', '', insu_receivable, cash_receivable, '', '']
            for item in output_header:
                worksheet.write(r, c, item, bold_border_ash)
                c += 1
            r += 2
            c = 1
            worksheet.write_merge(r, r, 1, 4, 'Net Collection (Cash Paid + Debit card Collection)', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, patient_paid_amount, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Net Patient Receivables', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, cash_receivable, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Net Collection (Insurance)', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, insu_paid_amount, bold_border_white_right)
            r += 1
            c = 1
            worksheet.write_merge(r, r, 1, 4, 'Net Insurance Receivables', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, insu_receivable, bold_border_white_right)
            c = 1
            r += 1
            worksheet.write_merge(r, r, 1, 4, 'Total', bold_border_white)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2
            c += 1
            worksheet.write(r, 5, patient_paid_amount + cash_receivable + insu_paid_amount + insu_receivable,
                            bold_border_white_right)
            
        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "REVENUE REPORT.xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'revenue.excel.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
