# -*- coding: utf-8 -*-
import base64
import io
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt


class IncomeByProcedureWizard(models.TransientModel):
    _name = 'income.by.procedure.wizard'
    _description = 'Income By Procedure Wizard'

    def _get_doctor_id(self):
        domain = []
        doc_ids = None
        group_dental_doc_menu = self.env.user.has_group('pragtech_dental_management.group_dental_doc_menu')
        group_dental_user_menu = self.env.user.has_group('pragtech_dental_management.group_dental_user_menu')
        group_dental_mng_menu = self.env.user.has_group('pragtech_dental_management.group_dental_mng_menu')
        if group_dental_doc_menu and not group_dental_user_menu and not group_dental_mng_menu:
            partner_ids = [x.id for x in
                           self.env['res.partner'].search(
                               [('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
                                ('company_id', '=', self.company_id.id)])]
            if partner_ids:
                doc_ids = [x.id for x in self.env['medical.physician'].search([
                    ('name', 'in', partner_ids), ('company_id', '=', self.company_id.id)])]
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

    def _get_treatment_ids(self):
        # group_multi_company = self.env.user.has_group('base.group_multi_company')
        # company_id = self.company_id or self.env.user.company_id
        # if group_multi_company:
        #     domain = [('is_treatment', '=', True), ('company_id', '=', company_id.id)]
        # else:
        #     domain = [('is_treatment', '=', True)]
        # domain = [('is_treatment', '=', True), ('company_id', '=', self.company_id.id)]
        domain = [('is_treatment', '=', True)]
        return domain

    company_id = fields.Many2one('res.company', "Company", domain=_get_company_id, required=True,
                                 default=lambda self: self.env.user.company_id.id)
    is_only_doctor = fields.Boolean()
    detailed = fields.Boolean('Detailed')
    date_start = fields.Date('From Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('To Date', required=True, default=fields.Date.context_today)
    based_on = fields.Selection([('category', 'Treatment Category'),
                                 ('treatment', 'Treatment')], default='category', string="Based on", required=True)
    treatment_categ_ids = fields.Many2many('product.category', string='Treatment Category')
    treatment_ids = fields.Many2many('product.product', string='Treatment', domain=_get_treatment_ids)
    doctor = fields.Many2one('medical.physician', "Doctor", domain=_get_doctor_id)
    data = fields.Binary('File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose language
                              ('get', 'get')], default='choose')
    name = fields.Char('File Name', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(IncomeByProcedureWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        res['is_only_doctor'] = False
        self._get_doctor_id()
        self._get_treatment_ids()
        doc_ids = None
        group_dental_doc_menu = self.env.user.has_group('pragtech_dental_management.group_dental_doc_menu')
        group_dental_user_menu = self.env.user.has_group('pragtech_dental_management.group_dental_user_menu')
        group_dental_mng_menu = self.env.user.has_group('pragtech_dental_management.group_dental_mng_menu')
        if group_dental_doc_menu and not group_dental_user_menu and not group_dental_mng_menu:
            res['is_only_doctor'] = True
            partner_ids = [x.id for x in
                           self.env['res.partner'].search(
                               [('user_id', '=', self.env.user.id), ('is_doctor', '=', True),
                                ('company_id', '=', self.env.user.company_id.id)])]
            if partner_ids:
                doc_ids = [x.id for x in self.env['medical.physician'].search([('name', 'in', partner_ids)])]
        if doc_ids:
            res['doctor'] = doc_ids[0]
        return res

    @api.onchange('based_on')
    def onchange_based_on(self):
        if self.based_on == 'category':
            self.treatment_ids = []
        else:
            self.treatment_categ_ids = []

    @api.multi
    def print_report(self):
        doctor = False
        category = ''
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        list_treatment = []
        if self.based_on == 'treatment':
            for treatment in self.treatment_ids:
                list_treatment.append(treatment.id)
        else:
            categories = []
            for categ in self.treatment_categ_ids:
                categories.append(categ.id)
                if category == '':
                    category = categ.name
                else:
                    category = category + ', ' + categ.name
            pdts = self.env['product.product'].search([('categ_id', 'child_of', categories)])
            for pdt in pdts:
                list_treatment.append(pdt.id)
        datas = {'active_ids': self.env.context.get('active_ids', []),
                 'form': self.read(['date_start', 'date_end', 'detailed'])[0],
                 'treatment_ids': list_treatment,
                 'categories': category,
                 'based_on': self.based_on,
                 'doctor': doctor,
                 'company_id': [self.company_id.id, self.company_id.name]}
        values = self.env.ref('pragtech_dental_management.income_by_procedure_qweb').report_action(self, data=datas)
        return values

    def get_income_procedure(self, start_date, end_date, treatment_ids, doctor, detailed, company_id):
        dom = [('date_invoice', '>=', start_date),
               ('date_invoice', '<=', end_date),
               ('dentist', '!=', False),
               ('company_id', '=', company_id.id),
               ('is_patient', '=', True),
               ('state', 'in', ['open', 'paid']),
               ('type', 'in', ('out_invoice','out_refund'))]
        if doctor:
            dom.append(('dentist', '=', doctor.id))
        history_ids = self.env['account.invoice'].search(dom)
        detailed_list = []
        detailed_dict = {}
        total_count = 0
        total = 0
        prod_dict = {}
        for income in history_ids:
            if income:
                for line in income.invoice_line_ids:
                    if treatment_ids:
                        contition_here = line.product_id.is_treatment and line.product_id.id in treatment_ids
                    else:
                        contition_here = line.product_id.is_treatment
                    if contition_here:
                        price_subtotal = line.price_subtotal
                        if income.type == 'out_refund':
                            price_subtotal = -1*line.price_subtotal
                        total += price_subtotal
                        total_count += 1
                        patient_name = income.patient.name.name
                        if income.patient.patient_id:
                            patient_name = '[' + income.patient.patient_id + ']' + patient_name
                        detailed_dict = {'name': income.number, 'count': 1, 'price_unit': price_subtotal,
                                         'product': line.product_id.id, 'patient': patient_name,'mobile':income.patient.mobile or ' '}
                        detailed_list.append(detailed_dict)
                        if line.product_id.id in prod_dict:
                            prod_dict[line.product_id.id][1] += 1
                            prod_dict[line.product_id.id][2] += price_subtotal
                        else:
                            prod_dict[line.product_id.id] = [line.product_id.name, 1, price_subtotal,
                                                             line.product_id.id]
        return [prod_dict], detailed_list, total_count, total

    @api.multi
    def generate_backlog_excel_report(self):
        wiz_date_start = self.date_start
        wiz_date_end = self.date_end
        if not wiz_date_start:
            raise UserError(_('Please enter From date'))
        if not wiz_date_end:
            raise UserError(_('Please enter To date'))
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('INCOME BY PROCEDURE REPORT SUMMARY')
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
        bold_border_left = xlwt.easyxf("pattern: pattern solid, fore-colour white; "
                                          "font: name Times New Roman, color black,bold on;"
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
        worksheet.write(r, c, 'INCOME BY PROCEDURE REPORT SUMMARY', title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 2
        c = 0
        start_date = (datetime.strptime(self.date_start, '%Y-%m-%d'))
        start_date = start_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        end_date = (datetime.strptime(self.date_end, '%Y-%m-%d'))
        end_date = end_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        output_header = ['From:', start_date, ' ', 'To:', end_date, ' ', 'Doctor:', self.doctor.name.name]
        for item in output_header:
            if item == 'From:' or item == 'To:' or item == 'Doctor:':
                worksheet.write(r, c, item, bold_teal)
            elif not self.doctor.name.name and item == output_header[-1]:
                worksheet.write(r, c, 'All', bold)
            else:
                worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 850 * 4
            c += 1
        r += 1
        c = 0
        if self.based_on == 'category':
            worksheet.write(r, c, 'Treatment Categories:', bold_teal)
            c += 1
            if self.treatment_categ_ids:
                for categ in self.treatment_categ_ids:
                    worksheet.write(r, c, categ.name, bold)
                    c += 1
            else:
                worksheet.write(r, c, 'All', bold)
        else:
            worksheet.write(r, c, 'Treatments:', bold_teal)
            c += 1
            if self.treatment_ids:
                for treatment in self.treatment_ids:
                    worksheet.write(r, c, treatment.name, bold)
                    c += 1
            else:
                worksheet.write(r, c, 'All', bold)
        r += 2
        c = 0
        if self.detailed == True:
            worksheet.write(r, c, 'Patient Name', bold_border)
            col = worksheet.col(c)
            col.width =2500 * 4
            c += 1
            worksheet.write(r, c, 'Patient Phone', bold_border)
            col = worksheet.col(c)
            col.width =2500 * 4
            c += 1
        output_header = ['Treatment Name', 'Count', 'Price']
        for item in output_header:
            worksheet.write(r, c, item, bold_border)
            col = worksheet.col(c)
            col.width =2500 * 4
            c += 1
        r += 1
        c = 0
        final_records, detailed_list, total_count, total = self.get_income_procedure(self.date_start, self.date_end,
                                                                                     self.treatment_ids, self.doctor,
                                                                                     self.detailed, self.company_id)
        for rec in final_records:
            for mdata in rec:
                if self.detailed == True:
                    c = 0
                    worksheet.write(r, c , '', bold_border_left)
                    worksheet.write(r, c + 1, '', bold_border_left)
                    worksheet.write(r, c + 2, rec[mdata][0], bold_border_left)
                    worksheet.write(r, c + 3, rec[mdata][1], bold_border_left)
                    worksheet.write(r, c + 4, rec[mdata][2], bold_border_left)
                    r += 1
                    for details in detailed_list:
                        if details['product'] == rec[mdata][3]:
                            c = 0
                            worksheet.write(r, c, details['patient'], bold_no_border_left)
                            worksheet.write(r, c + 1, details['mobile'], bold_no_border_left)
                            worksheet.write(r, c + 2, details['name'], bold_no_border_left)
                            worksheet.write(r, c + 3, details['count'], bold_no_border_left)
                            worksheet.write(r, c + 4, details['price_unit'], bold_no_border_left)
                            r += 1
                    r += 0
                else:
                    c = 0
                    worksheet.write(r, c, rec[mdata][0], bold_no_border_left)
                    worksheet.write(r, c + 1, rec[mdata][1], bold_no_border_left)
                    worksheet.write(r, c + 2, rec[mdata][2], bold_no_border_left)
                    r += 1
        c = 0
        if self.detailed == True:
            worksheet.write_merge(r, r, c, c + 2, 'Total', bold_border_total)
            worksheet.write(r, c + 3, total_count, bold_border_left)
            worksheet.write(r, c + 4, total, bold_border_left)
        else:
            worksheet.write(r, c, 'Total', bold_border_total)
            worksheet.write(r, c + 1, total_count, bold_border_left)
            worksheet.write(r, c + 2, total, bold_border_left)
        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "INCOME BY PROCEDURE REPORT.xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'income.by.procedure.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
