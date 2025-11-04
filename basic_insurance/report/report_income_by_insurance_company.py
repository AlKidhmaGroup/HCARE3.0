# -*- coding: utf-8 -*-

import base64
import io
import time
from odoo import api, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt


class ReportIncomByInsuranceExcel(models.TransientModel):
    _inherit = 'income.by.insurance.company.wizard'

    def get_record_names(self, rec):
        result = [i.name_get()[0][1] for i in rec]
        return result and ", ".join(result) or "All"

    def get_search_domain(self, form):
        d_val = []
        if form.get('date_start'):
            d_val += [('date_invoice', '>=', form['date_start'])]
        if form.get('date_end'):
            d_val += [('date_invoice', '<=', form['date_end'])]
        if form.get('insurance_company'):
            d_val += [('insurance_company', '=', form['insurance_company'][0])]
        if form.get('doctor_ids'):
            d_val += [('dentist', 'in', form['doctor_ids'])]
        elif form.get('department_ids'):
            d_ids = self.env['medical.physician'].search([(
                'department_id', 'in', form['department_ids'])]).ids
            d_val += [('dentist', 'in', d_ids)]
        return d_val

    def get_income_insurance_company(self, form={}):
        service_ids = form.get('service_ids')
        insurance_company = form['insurance_company']
        if isinstance(insurance_company, tuple):
            insurance_company = insurance_company[0]

        history_ids = self.env['account.invoice'].search(
            self.get_search_domain(form))
        prod_dict = {}
        for income in history_ids:
            to_include = False
            items = income.invoice_line_ids.mapped('product_id').ids
            for i in items:
                if i in service_ids:
                    to_include = True
            if not service_ids:
                to_include = True
            insurance = income.insurance_company
            if not to_include or not insurance:
                continue
            if insurance.id in prod_dict:
                prod_dict[insurance.id]['invoice_count'] += 1
                prod_dict[insurance.id]['total'] += income.amount_total
                if income.partner_id not in prod_dict[insurance.id]['partner_ids']:
                    prod_dict[insurance.id]['partner_ids'].append(income.partner_id)
            else:
                prod_dict[insurance.id] = {
                    'name': insurance.name,
                    'invoice_count': 1,
                    'total': income.amount_total,
                    'partner_ids' : [income.partner_id]
                }
        # print("prod_dict",prod_dict)
        return prod_dict

    def income_by_insurance_xlsx(self):
        final_records = self.get_income_insurance_company(self.read()[0])
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        period_start = datetime.strptime(self.date_start, '%Y-%m-%d').strftime(
            date_format)
        period_stop = datetime.strptime(self.date_end, '%Y-%m-%d').strftime(
            date_format)

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('APPOINTMENT ANALYSIS')

        def set_col_width(c_no, w_val):
            col_sel = worksheet.col(c_no)
            col_sel.width = 256 * w_val

        main_head = xlwt.easyxf(
            "font: name Times New Roman,height 300, color black, bold True, "
            "name Arial;align: horiz center, vert center;"
            "pattern: pattern solid, fore-colour teal_ega;")

        table_head = xlwt.easyxf(
            "pattern: pattern solid, fore-colour teal_ega;"
            "font: name Times New Roman, bold on, color black;"
            "align: horiz left, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        font_bold = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white;"
            "font: name Times New Roman, bold on, color black;"
            "align: horiz left, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        font_normal = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white;"
            "font: name Times New Roman, color black;"
            "align: horiz left, vert center;alignment: wrap True;"
            "borders: left thin, right thin, top thin, bottom thin;")
        bold_decimal = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white; "
            "font: name Times New Roman, bold on, color black;"
            "align: horiz left, vert center; borders: left thin, right thin, "
            "top thin, bottom medium;", num_format_str='#,##0.00')
        normal_decimal = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white; "
            "font: name Times New Roman, color black;"
            "align: horiz left, vert center; borders: left thin, right thin, "
            "top thin, bottom medium;", num_format_str='#,##0.00')

        r = 0
        c = 0
        set_col_width(0, 20)
        worksheet.write_merge(r, r + 1, c, c + 4, "Income By Insurance Company",
                              main_head)
        r += 2
        # filters
        worksheet.write(r, c, "From", font_bold)
        c += 1
        worksheet.write(r, c, period_start, font_bold)

        c += 2
        worksheet.write(r, c, "To", font_bold)
        c += 1
        worksheet.write(r, c, period_stop, font_bold)

        r += 1
        c = 0
        worksheet.write(r, c, "Department", font_bold)
        c += 1
        worksheet.write(r, c, self.get_record_names(self.department_ids),
                        font_bold)

        c += 2
        worksheet.write(r, c, "Doctor", font_bold)
        c += 1
        worksheet.write(r, c, self.get_record_names(self.doctor_ids), font_bold)

        r += 1
        c = 0
        worksheet.write(r, c, "Service", font_bold)
        c += 1
        worksheet.write(r, c, self.get_record_names(self.service_ids),
                        font_bold)

        c += 2
        worksheet.write(r, c, "Insurance Company", font_bold)
        c += 1
        worksheet.write(r, c, self.get_record_names(self.insurance_company),
                        font_bold)

        r += 2
        c = 0
        table_cols = [{
            'name': 'name',
            'label': 'Insurance Company'
        }, {
            'name': 'patient_count',
            'label': 'No. of Patients'
        },{
            'name': 'invoice_count',
            'label': 'No. of Invoices'
        }, {
            'name': 'total',
            'label': 'Total'
        }]
        for col in table_cols:
            worksheet.write(r, c, col['label'], table_head)
            c += 1
        r += 1
        for i in final_records:
            c = 0
            insurance = final_records[i]
            for col in table_cols:
                style_val = font_normal
                if col['name'] != 'patient_count':
                    if col['name'] == 'total':
                        style_val = normal_decimal
                    worksheet.write(r, c, insurance[col['name']], style_val)
                else:
                    worksheet.write(r, c, len(insurance['partner_ids']), style_val)
                c += 1
            r += 1

        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "Insurance by Company.xls"
        self.write({'data': out, 'name': name, 'state': 'get'})
        return {
            'type': "ir.actions.do_nothing"
        }


class ReportIncomeByInsurance(models.AbstractModel):

    _name = 'report.basic_insurance.income_by_insurance'

    @api.multi
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get(
                'active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, "
                              "this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        start_date = data['form']['date_start']
        end_date = data['form']['date_end']
        final_records = self.env[
            'income.by.insurance.company.wizard'].get_income_insurance_company(
            data['form'])
        period_start = datetime.strptime(start_date, '%Y-%m-%d')
        period_stop = datetime.strptime(end_date, '%Y-%m-%d')
        return {
            'period_start': period_start,
            'period_stop': period_stop,
            'doc_ids': self.ids,
            'doc_model': 'income.by.insurance.company.wizard',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_income_insurance_company': final_records,
        }

    def formatLang(self, value, digits=None, date=False, date_time=False,
                   grouping=True, monetary=False, dp=False, currency_obj=False,
                   lang=False):
        if lang:
            self.env.context['lang'] = lang
        return super(ReportIncomeByInsurance, self).formatLang(
            value, digits=digits, date=date, date_time=date_time,
            grouping=grouping, monetary=monetary, dp=dp,
            currency_obj=currency_obj)
