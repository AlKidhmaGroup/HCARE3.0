# -*- coding: utf-8 -*-
import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPatientByProcedure(models.AbstractModel):
    _name = 'report.pragtech_dental_management.report_patient_by_procedure'

    def fetch_invoice_domain(self, form):
        s_domain = [
            ('date_invoice', '>=', form['date_start']),
            ('date_invoice', '<=', form['date_end']),
            ('company_id', '<=', form['company_id'][0]),
            ('is_patient', '=', True), ('state', 'in', ['open', 'paid'])]
        if 'doctor_ids' in form:
            s_domain += [('dentist', 'in', form['doctor_ids'])]
        if 'patient_ids' in form:
            s_domain += [('patient', 'in', form['patient_ids'])]
        if 'department_ids' in form:
            cr = self._cr
            cr.execute("select id from medical_physician where department_id in "
                       "%s ", (tuple(form['department_ids']),))
            doctor_ids = [i[0] for i in cr.fetchall()]
            if doctor_ids:
                s_domain += [('dentist', 'in', doctor_ids)]
        return s_domain

    def fetch_record(self, form):
        s_domain = self.fetch_invoice_domain(form)
        history_ids = self.env['account.invoice'].search(s_domain)
        prod_dict = {}
        for income in history_ids:
            if income:
                for line in income.invoice_line_ids:
                    if line.product_id.is_treatment:
                        if prod_dict.has_key(line.product_id.id):
                            prod_dict[line.product_id.id][1] += 1
                        else:
                            prod_dict[line.product_id.id] = [
                                line.product_id.name, 1]
        return [prod_dict]

    @api.multi
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get(
                'active_model') or not self.env.context.get('active_id'):
            raise UserError(_(
                "Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        company_id = data['form']['company_id']

        final_records = self.fetch_record(data['form'])
        return {
            'doc_ids': self.ids,
            'doc_model': 'patient.by.procedure.wizard',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_patient_procedure': final_records,
            'company_id': [company_id[0], company_id[1]]
        }

    def formatLang(self, value, digits=None, date=False, date_time=False, grouping=True, monetary=False, dp=False,
                   currency_obj=False, lang=False):
        if lang:
            self.env.context['lang'] = lang
        return super(ReportPatientByProcedure, self).formatLang(value, digits=digits, date=date, date_time=date_time,
                                                                grouping=grouping, monetary=monetary, dp=dp,
                                                                currency_obj=currency_obj)
