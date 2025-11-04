# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt


class IncomeByDoctorReportWizard(models.TransientModel):
    _name = 'income.by.doctor.report.wizard'

    start_date = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=True, default=fields.Date.context_today)
    date_type = fields.Selection([('invoice', 'Invoice Date'),
                                  ('payment', 'Payment Date')],
                                 string='Based on', required=True, default='payment')
    data = fields.Binary('File', readonly=True)
    doctor_ids = fields.Many2many(comodel_name="medical.physician",  string="Doctors", )
    hide_advance= fields.Boolean(string="Hide Advance ?",  )
    state = fields.Selection([('choose', 'choose'),  # choose language
                              ('get', 'get')], default='choose')
    name = fields.Char('File Name', readonly=True)

    @api.multi
    def income_by_doctor_report(self):
        data = {'ids': self.env.context.get('active_ids', [])}
        date_type = 'Invoice Date'
        if self.date_type == 'payment':
            date_type = 'Payment Date'
        res = self.read()
        res = res and res[0] or {}
        data.update({'form': res})
        data['form']['date_type'] = date_type
        return self.env.ref('pragtech_dental_management.income_byreport_report12333').report_action(self, data=data)

    def fetch_record(self, start_date, end_date, date_type,doctor_ids,hide_advance):
        if date_type == 'invoice':
            dom_invoice = [('date_invoice', '>=', start_date),
                           ('date_invoice', '<=', end_date),
                           ('dentist', '!=', False),
                           ('is_patient', '=', True),
                           ('state', 'in', ['open', 'paid']),
                           ('type', '=', 'out_invoice')]
            invoice_ids = self.env['account.invoice'].search(dom_invoice)
            if doctor_ids :
                doctors = self.env['medical.physician'].search([('id','in',doctor_ids.ids )])
                invoice_ids = self.env['account.invoice'].search([('dentist', 'in', doctors.ids)])

            res = []
            for each_record in invoice_ids:
                result = each_record._get_payments_vals()
                cash1 = 0.0
                credit1 = 0.0
                cash = 0.0
                credit = 0.0
                insurance = 0.0
                disc_total = 0.0
                for line in each_record.invoice_line_ids:
                    if line.discount_value:
                        disc_total += line.discount_value
                    if line.discount:
                        disc_total += (
                                                  line.price_unit * line.quantity * line.discount * line.amt_paid_by_patient) / 10000
                if each_record.discount_value:
                    disc_total += each_record.discount_value
                if each_record.discount:
                    order_amount_total = each_record.amount_untaxed + each_record.amount_tax
                    disc_total += (order_amount_total * each_record.discount or 0.0) / 100.0
                move_lin_obj = self.env['account.move.line']
                journal_obj = self.env['account.journal']
                cash_journals = journal_obj.search([('type', '=', 'cash'), ('name', '=', 'Cash')]).ids
                bank_journals = journal_obj.search([('type', '=', 'bank')]).ids
                insurance_journals = journal_obj.search([('name', '=', 'Insurance'), ('code', '=', 'ins')]).ids
                for pay in result:
                    move_line_obj = move_lin_obj.browse(pay['payment_id'])
                    if move_line_obj.journal_id.id in cash_journals:
                        cash1 += pay['amount']
                        cash = round(cash1)
                    if move_line_obj.journal_id.id in bank_journals:
                        credit1 += pay['amount']
                        credit = round(credit1)
                    if move_line_obj.journal_id.id in insurance_journals:
                        insurance += pay['amount']
                due = each_record.amount_total - cash - credit - insurance
                if not res:
                    res.append({'dentist_id': each_record.dentist.id,
                                'dentist_name': each_record.dentist.name.name,
                                'customer_count': 1,
                                'cash': round(cash),
                                'credit': round(credit),
                                'insurance': insurance,
                                'total_amount': each_record.amount_total,
                                'due': due})
                else:
                    flag = 0
                    for each_res in res:
                        if each_record.dentist.id == each_res['dentist_id']:
                            each_res['customer_count'] += 1
                            each_res['total_amount'] += each_record.amount_total
                            each_res['cash'] += round(cash)
                            each_res['credit'] += round(credit)
                            each_res['insurance'] += insurance
                            each_res['due'] += due
                            flag = 1
                            break
                    if flag == 0:
                        res.append({'dentist_id': each_record.dentist.id,
                                    'dentist_name': each_record.dentist.name.name,
                                    'customer_count': 1,
                                    'cash': round(cash),
                                    'credit': round(credit),
                                    'insurance': insurance,
                                    'due': due,
                                    'total_amount': each_record.amount_total})
        else:
            dom_payment = [('payment_date', '>=', start_date),
                           ('payment_date', '<=', end_date),
                           ('partner_type', '=', 'customer'),
                           # ('dentist', '!=', False),
                           # ('is_patient', '=', True),
                           ('state', 'in', ('posted', 'reconciled'))]
            # if doctor_ids :
            #     dom_payment.append(('doctor_id', 'in', doctor_ids.ids),)
            #     print("DDDDDDDD")
            payment_records = self.env['account.payment'].search(dom_payment)
            res = []
            journal_obj = self.env['account.journal']
            cash_journals = journal_obj.search([('type', '=', 'cash'), ('name', '=', 'Cash')]).ids
            bank_journals = journal_obj.search([('type', '=', 'bank')]).ids
            for payment in payment_records:
                doctor_payment = False
                sign = 1
                if payment.advance:
                    doctor_payment = payment.doctor_id
                    if payment.payment_type == 'inbound':
                        sign = 1
                    else:
                        sign = -1
                elif len(payment.invoice_ids) == 1:
                    order = payment.invoice_ids
                    doctor_payment = order.dentist
                    if order.type == 'out_invoice':
                        sign = 1
                    else:
                        sign = -1
                else:
                    doctor_payment = payment.doctor_id
                    inv_rec = self.env['account.invoice'].search([('number', '=', payment.communication)])
                    if inv_rec and not doctor_payment:
                        doctor_payment = inv_rec[0].dentist
                    if payment.payment_type == 'inbound':
                        sign = 1
                    else:
                        sign = -1
                cash1 = 0.0
                credit1 = 0.0
                cash = 0.0
                credit = 0.0
                if payment.journal_id.id in cash_journals:
                    cash1 += (payment.amount * sign)
                    cash = round(cash1)
                if payment.journal_id.id in bank_journals:
                    credit1 += (payment.amount * sign)
                    credit = round(credit1)
                if not res:
                    res.append({'dentist_id': doctor_payment.id,
                                'dentist_name': doctor_payment.name.name,
                                'cash': round(cash),
                                'credit': round(credit),
                                'total_income': round(cash) + round(credit)})
                else:
                    flag = 0
                    for each_res in res:
                        if doctor_payment.id == each_res['dentist_id']:
                            each_res['cash'] += round(cash)
                            each_res['credit'] += round(credit)
                            total_income = round(cash) + round(credit)
                            each_res['total_income'] += total_income
                            flag = 1
                            break
                    if flag == 0:
                        total_income = round(cash) + round(credit)
                        res.append({'dentist_id': doctor_payment.id,
                                    'dentist_name': doctor_payment.name.name,
                                    'cash': round(cash),
                                    'credit': round(credit),
                                    'total_income': total_income, })
        res_new = []
        if doctor_ids:
            for record in res :
                if record['dentist_id'] in doctor_ids.ids :
                    res_new.append(record)

                if not record['dentist_id'] :
                    if not hide_advance :
                        res_new.append(record)
            return res_new
        return res

    @api.multi
    def generate_backlog_excel_report(self):
        wiz_date_start = self.start_date
        wiz_date_end = self.end_date
        if not wiz_date_start:
            raise UserError(_('Please enter From date'))
        if not wiz_date_end:
            raise UserError(_('Please enter To date'))
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('INCOME BY DOCTOR REPORT SUMMARY')
        bold_teal = xlwt.easyxf("font: bold on, color teal_ega;")
        bold = xlwt.easyxf("font: bold on;")
        r = 0
        c = 3
        company_name = self.env.user.company_id.name
        title = xlwt.easyxf("font: name Times New Roman,height 300, color teal_ega, bold True, name Arial;"
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
        bold_no_border_right = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                           "font: name Times New Roman, color black;"
                                           "align: horiz right, vert center; "
                                           "borders: left thin, right thin, top thin, bottom medium;")
        bold_no_border_left = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, color black;"
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
        worksheet.write(r, c, 'INCOME BY DOCTOR REPORT SUMMARY', title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 2
        c = 0
        start_date = (datetime.strptime(self.start_date, '%Y-%m-%d'))
        start_date = start_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        end_date = (datetime.strptime(self.end_date, '%Y-%m-%d'))
        end_date = end_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        output_header = ['From:', start_date, ' ', ' ', ' ', 'To:', end_date]
        for item in output_header:
            if item == 'From:' or item == 'To:':
                worksheet.write(r, c, item, bold_teal)
            else:
                worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 1
        c = 0
        doctor_list = ''
        if self.doctor_ids:
            for doc in self.doctor_ids:
                doctor_list+= doc.name.name+", "
        if doctor_list == '':
            doctor_list = 'All'

        output_header = ['Based on:', self.date_type,' ',' ',' ','Doctors: ',doctor_list]
        for item in output_header:
            if item == 'invoice':
                worksheet.write(r, c, "Invoice Date", bold)
            elif item == 'payment':
                worksheet.write(r, c, "Payment Date", bold)
            else:
                worksheet.write(r, c, item, bold_teal)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 2
        c = 0
        if self.date_type == 'payment':
            output_header = ['Name of Doctors', 'Cash Income', 'Credit Income', 'Total Income']
            for item in output_header:
                worksheet.write(r, c, item, bold_border)
                c += 1
        else:
            output_header = ['Doctor', 'No. of Patients', 'Total Amount', 'Cash', 'Card', 'Insurance', 'Due']
            for item in output_header:
                worksheet.write(r, c, item, bold_border)
                c += 1
        data_list = self.fetch_record(self.start_date, self.end_date, self.date_type,self.doctor_ids,self.hide_advance)
        normal = xlwt.easyxf()
        c = 0
        total_cash = 0.0
        total_credit = 0.0
        total_total_income = 0.0
        total_inv_customer_count = 0.0
        total_inv_total_amount = 0.0
        total_inv_cash = 0.0
        total_inv_credit = 0.0
        total_inv_insurance = 0.0
        total_inv_due = 0.0
        if self.date_type == 'payment':
            for value in data_list:
                data = []
                data.append(value['dentist_name'])
                data.append(value['cash'])
                data.append(value['credit'])
                data.append(value['total_income'])
                total_cash += value['cash']
                total_credit += value['credit']
                total_total_income += value['total_income']
                r += 1
                c = 0
                for item in data:
                    if c == 0:
                        worksheet.write(r, c, item, bold_no_border_center)
                    elif c == 1:
                        worksheet.write(r, c, item, bold_no_border_left)
                    else:
                        if item == 0:
                            worksheet.write(r, c, '', bold_no_border_center)
                        else:
                            worksheet.write(r, c, item, bold_no_border_center)
                    c += 1
        else:
            for value in data_list:
                data = []
                total_inv_customer_count += value['customer_count']
                total_inv_total_amount += value['total_amount']
                total_inv_cash += value['cash']
                total_inv_credit += value['credit']
                total_inv_insurance += value['insurance']
                total_inv_due += value['due']
                data.append(value['dentist_name'])
                data.append(value['customer_count'])
                data.append(value['total_amount'])
                data.append(value['cash'])
                data.append(value['credit'])
                data.append(value['insurance'])
                data.append(value['due'])
                # data_list.append(data)
                r += 1
                c = 0
                for item in data:
                    if c == 0:
                        worksheet.write(r, c, item, bold_no_border_center)
                    elif c == 1:
                        worksheet.write(r, c, item, bold_no_border_center)
                    else:
                        if item == 0:
                            worksheet.write(r, c, '', bold_no_border_center)
                        else:
                            worksheet.write(r, c, item, bold_no_border_center)
                    c += 1
        r += 1
        c = 0
        if self.date_type == 'payment':
            worksheet.write(r, c, "TOTAL", bold_border_total)
            total_list = [total_cash, total_credit, total_total_income]
            for t in total_list:
                c += 1
                worksheet.write(r, c, t, bold_no_border_left)
        else:
            worksheet.write(r, c, "TOTAL", bold_border_total)
            total_list = [total_inv_customer_count, total_inv_total_amount,
                          total_inv_cash, total_inv_credit, total_inv_insurance, total_inv_due]
            for t in total_list:
                c += 1
                worksheet.write(r, c, t, bold_border_total)
        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "INCOME BY DOCTOR REPORT.xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'income.by.doctor.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class PatientDoctorReportWizard(models.TransientModel):
    _name = 'patient.by.doctor.report.wizard'

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
    start_date = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=True, default=fields.Date.context_today)
    doctor_id = fields.Many2one('medical.physician', 'Doctor')

    @api.model
    def default_get(self, fields):
        res = super(PatientDoctorReportWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        return res

    @api.multi
    def patient_by_doctor_report(self):
        datas = {'active_ids': self.env.context.get('active_ids', []),
                 'form': self.read(['start_date', 'end_date'])[0]}
        datas['form']['company_id'] = [self.company_id.id, self.company_id.name]
        datas['form']['doctor_id'] = [self.doctor_id.id, self.doctor_id.name]
        values = self.env.ref('pragtech_dental_management.patient_byreport_report12333').report_action(self, data=datas)
        return values
