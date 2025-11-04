# -*- coding: utf-8 -*-
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ReportIncomeByDoctor(models.AbstractModel):
    _name = 'report.pragtech_dental_management.report_income_by_doctor'

    def fetch_record(self, start_date, end_date, date_type,doctor_ids,hide_advance):
        if date_type == 'Invoice Date':
            dom_invoice = [('date_invoice', '>=', start_date),
                          ('date_invoice', '<=', end_date),
                          ('dentist', '!=', False),
                          ('is_patient', '=', True),
                          ('state', 'in', ['open', 'paid']),
                          ('type', '=', 'out_invoice')]
            invoice_ids = self.env['account.invoice'].search(dom_invoice)
            res = []
            for each_record in invoice_ids:
                result = each_record._get_payments_vals()
                cash1=0.0
                credit1=0.0
                cash = 0.0
                credit = 0.0
                insurance=0.0
                disc_total = 0.0
                for line in each_record.invoice_line_ids:
                    if line.discount_value:
                        disc_total += line.discount_value
                    if line.discount:
                        disc_total += (line.price_unit * line.quantity * line.discount * line.amt_paid_by_patient) / 10000
                if each_record.discount_value:
                    disc_total += each_record.discount_value
                if each_record.discount:
                    order_amount_total = each_record.amount_untaxed + each_record.amount_tax
                    disc_total += (order_amount_total * each_record.discount or 0.0) / 100.0
                move_lin_obj = self.env['account.move.line']
                journal_obj = self.env['account.journal']
                cash_journals = journal_obj.search([('type', '=', 'cash'),('name', '=', 'Cash')]).ids
                bank_journals = journal_obj.search([('type', '=', 'bank')]).ids
                insurance_journals = journal_obj.search([('name', '=', 'Insurance'),('code', '=', 'ins')]).ids
                for pay in result:
                    move_line_obj = move_lin_obj.browse(pay['payment_id'])
                    if move_line_obj.journal_id.id in cash_journals:
                        cash1 += pay['amount']
                        cash = round(cash1)
                    if move_line_obj.journal_id.id in bank_journals:
                        credit1 += pay['amount']
                        credit=round(credit1)
                    if move_line_obj.journal_id.id in insurance_journals:
                        insurance += pay['amount']
                due = each_record.amount_total - cash - credit - insurance
                if not res:
                    res.append({'dentist_id': each_record.dentist.id,
                                'dentist_name': each_record.dentist.name.name,
                                'customer_count': 1,
                                'cash': round(cash),
                                'credit': round(credit),
                                'insurance':insurance,
                                'total_amount': each_record.amount_total,
                                'due': due})
                else:
                    flag = 0
                    for each_res in res:
                        if each_record.dentist.id == each_res['dentist_id']:
                            each_res['customer_count'] += 1
                            each_res['total_amount'] += each_record.amount_total
                            each_res['cash']+=round(cash)
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
                                    'credit':round(credit),
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
            payment_records = self.env['account.payment'].search(dom_payment)
            res = []
            journal_obj = self.env['account.journal']
            cash_journals = journal_obj.search([('type', '=', 'cash'),('name', '=', 'Cash')]).ids
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
                cash1=0.0
                credit1=0.0
                cash = 0.0
                credit = 0.0
                if payment.journal_id.id in cash_journals:
                    cash1 += (payment.amount * sign)
                    cash = round(cash1)
                if payment.journal_id.id in bank_journals:
                    credit1 += (payment.amount * sign)
                    credit=round(credit1)
                if not res:
                    res.append({'dentist_id': doctor_payment.id,
                                'dentist_name': doctor_payment.name.name,
                                'cash': round(cash),
                                'credit': round(credit),
                                'total_income':round(cash) + round(credit)})
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
                                    'credit':round(credit),
                                    'total_income': total_income,})
        res_new = []
        if doctor_ids:
            for record in res :
                if record['dentist_id'] in doctor_ids :
                    res_new.append(record)

                if not record['dentist_id'] :
                    if not hide_advance :
                        res_new.append(record)
            return res_new
        return res


    @api.multi
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        data_type = data['form']['date_type']
        doctors = data['form']['doctor_ids']
        hide_advance = data['form']['hide_advance']
        final_records = self.fetch_record(start_date, end_date, data_type,doctors,hide_advance)
        period_start = datetime.strptime(start_date, '%Y-%m-%d')
        period_stop = datetime.strptime(end_date, '%Y-%m-%d')
        doctor_list = ''
        if doctors :
            doctor_ids = self.env['medical.physician'].search([('id','in',doctors)])
            for record in doctor_ids :
                doctor_list += record.name.name+", "
        if doctor_list == '':
            doctor_list = 'All'

        return {
            'date_type': data_type,
            'doctor_list': doctor_list,
            'period_start': period_start,
            'period_stop': period_stop,
            'doc_ids': self.ids,
            'doc_model': 'income.by.doctor.report.wizard',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_income_by_dentist_info': final_records,
        }
    
    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False,
                   currency_obj=False, lang=False):
        if lang:
            self.env.context['lang'] = lang
        return super(ReportIncomeByDoctor, self).formatLang(value, digits=digits, date=date, date_time=date_time,
                                                            grouping=grouping, monetary=monetary, dp=dp,
                                                            currency_obj=currency_obj)

    
class ReportPatientByDoctor(models.AbstractModel):
    _name = 'report.pragtech_dental_management.report_patient_by_doctor'
    
    def fetch_record(self, start_date, end_date, company_id=False,doctor_id=False):
        if doctor_id[0]:
            invoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', start_date),
                                                              ('date_invoice', '<=', end_date),
                                                              ('dentist', '=', doctor_id[0]),
                                                              ('is_patient', '=', True),
                                                              ('state', 'in', ['open', 'paid']),
                                                              ('type', '=', 'out_invoice'),
                                                              ('company_id', '=', company_id[0])])

        else:
            invoice_ids = self.env['account.invoice'].search([('date_invoice', '>=', start_date),
                                                              ('date_invoice', '<=', end_date),
                                                              ('dentist', '!=', False),
                                                              ('is_patient', '=', True),
                                                              ('state', 'in', ['open', 'paid']),
                                                              ('type', '=', 'out_invoice'),
                                                              ('company_id', '=', company_id[0])])
        res = []
        for each_record in invoice_ids:
            if not res:
                res.append({'dentist_id': each_record.dentist.id,
                            'dentist_name': each_record.dentist.name.name,
                            'customer_count': 1})
            else: 
                flag = 0
                for each_res in res:
                    if each_record.dentist.id == each_res['dentist_id']:
                        each_res['customer_count'] += 1
                        flag = 1
                        break
                if flag == 0:
                    res.append({'dentist_id': each_record.dentist.id,
                                'dentist_name': each_record.dentist.name.name,
                                'customer_count': 1})
        return res

    @api.multi
    def get_report_values(self, docids, data=None):

        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        company_id = data['form']['company_id']
        doctor_id = data['form']['doctor_id']
        final_records = self.fetch_record(start_date, end_date, company_id,doctor_id)
        period_start = datetime.strptime(start_date, '%Y-%m-%d')
        period_stop = datetime.strptime(end_date, '%Y-%m-%d')
        return {
            'period_start': period_start,
            'period_stop': period_stop,
            'doc_ids': self.ids,
            'doc_model': 'patient.by.doctor.report.wizard',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_income_by_dentist_info': final_records,
            'company_id': [company_id[0], company_id[1]],
            'doctor_id': [doctor_id[0], doctor_id[1]]
        }
    
    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False,
                   currency_obj=False, lang=False):
        if lang:
            self.env.context['lang'] = lang
        return super(ReportPatientByDoctor, self).formatLang(value, digits=digits, date=date, date_time=date_time,
                                                            grouping=grouping, monetary=monetary, dp=dp,
                                                            currency_obj=currency_obj)
