# -*- coding: utf-8 -*-

import base64
import io
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt


class IncomeByComboWizard(models.TransientModel):
    _inherit = 'income.by.procedure.wizard'
    _name = 'income.by.combo.wizard'
    _description = 'Income By Combo Wizard'

    def _get_treatment_ids(self):
        return [('combo_pack', '=', True)]

    based_on = fields.Selection([
        ('category', 'Combo Pack Category'),
        ('combo', 'Combo Pack')], default='combo',
        string="Based on", required=True)
    treatment_categ_ids = fields.Many2many('product.category',
                                           string='Combo Pack Category')
    treatment_ids = fields.Many2many('product.product', string='Combo Pack',
                                     domain=_get_treatment_ids)

    @api.multi
    def print_report(self):
        doctor = False
        category = ''
        if self.doctor:
            doctor = [self.doctor.id, self.doctor.name.name]
        list_treatment = []
        if self.based_on == 'combo':
            for combo in self.treatment_ids:
                list_treatment.append(combo.id)
        else:
            categories = []
            for categ in self.treatment_categ_ids:
                categories.append(categ.id)
                if category == '':
                    category = categ.name
                else:
                    category = category + ', ' + categ.name
            pdts = self.env['product.product'].search(
                [('categ_id', 'child_of', categories)])
            for pdt in pdts:
                list_treatment.append(pdt.id)
        datas = {
            'active_ids': self.env.context.get('active_ids', []),
            'form': self.read(['date_start', 'date_end', 'detailed'])[0],
            'treatment_ids': list_treatment,
            'categories': category,
            'based_on': self.based_on,
            'doctor': doctor,
            'company_id': [self.company_id.id, self.company_id.name]
        }
        values = self.env.ref(
            'pragtech_dental_management.income_by_procedure_qweb'
        ).report_action(self, data=datas)
        return values

    @api.multi
    def generate_backlog_excel_report(self):
        wiz_date_start = self.date_start
        wiz_date_end = self.date_end
        if not wiz_date_start:
            raise UserError(_('Please enter From date'))
        if not wiz_date_end:
            raise UserError(_('Please enter To date'))
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('INCOME BY COMBO REPORT SUMMARY')
        bold_teal = xlwt.easyxf("font: bold on, color teal_ega;")
        bold = xlwt.easyxf("font: bold on;")
        r = 0
        c = 3
        company_name = self.env.user.company_id.name
        title = xlwt.easyxf(
            "font: name Times New Roman,height 300, color teal_ega, bold True,"
            " name Arial; align: horiz center, vert center;")
        bold_border = xlwt.easyxf(
            "pattern: pattern solid, fore-colour teal_ega;"
            "font: name Times New Roman, color white, bold on;"
            "align: horiz center, vert center; "
            "borders: left thin, right thin, top thin, bottom medium;")
        bold_border_total = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white; "
            "font: name Times New Roman, color black, bold on;"
            "align: horiz center, vert center; "
            "borders: left thin, right thin, top thin, bottom medium;")
        bold_no_border_left = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white; "
            "font: name Times New Roman, color black;"
            "align: horiz left, vert center; "
            "borders: left thin, right thin, top thin, bottom medium;"
            , num_format_str='#,##0.00')
        bold_border_left = xlwt.easyxf(
            "pattern: pattern solid, fore-colour white; "
            "font: name Times New Roman, color black,bold on;"
            "align: horiz left, vert center; "
            "borders: left thin, right thin, top thin, bottom medium;",
            num_format_str='#,##0.00')
        worksheet.write(r, c, company_name, title)
        col = worksheet.col(c)
        col.width = 900 * 3
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 3
        worksheet.write(r, c, 'INCOME BY COMBO REPORT SUMMARY', title)
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
        output_header = ['From:', start_date, ' ', 'To:', end_date, ' ',
                         'Doctor:', self.doctor.name.name]
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
            worksheet.write(r, c, 'Combo Categories:', bold_teal)
            c += 1
            if self.treatment_categ_ids:
                for categ in self.treatment_categ_ids:
                    worksheet.write(r, c, categ.name, bold)
                    c += 1
            else:
                worksheet.write(r, c, 'All', bold)
        else:
            worksheet.write(r, c, 'Combo Packs:', bold_teal)
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
            col.width = 2500 * 4
            c += 1
        output_header = ['Combo Pack Name', 'Count', 'Price']
        for item in output_header:
            worksheet.write(r, c, item, bold_border)
            col = worksheet.col(c)
            col.width = 2500 * 4
            c += 1
        r += 1
        c = 0
        final_records, detailed_list, total_count, total = self.get_income_procedure(
            self.date_start, self.date_end, self.treatment_ids, self.doctor,
            self.detailed, self.company_id)
        for rec in final_records:
            for mdata in rec:
                if self.detailed == True:
                    c = 0
                    worksheet.write(r, c , '', bold_border_left)
                    worksheet.write(r, c + 1, rec[mdata][0], bold_border_left)
                    worksheet.write(r, c + 2, rec[mdata][1], bold_border_left)
                    worksheet.write(r, c + 3, rec[mdata][2], bold_border_left)
                    r += 1
                    for details in detailed_list:
                        if details['product'] == rec[mdata][3]:
                            c = 0
                            worksheet.write(r, c, details['patient'],
                                            bold_no_border_left)
                            worksheet.write(r, c + 1, details['name'],
                                            bold_no_border_left)
                            worksheet.write(r, c + 2, details['count'],
                                            bold_no_border_left)
                            worksheet.write(r, c + 3, details['price_unit'],
                                            bold_no_border_left)
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
            worksheet.write_merge(r, r, c, c + 1, 'Total', bold_border_total)
            worksheet.write(r, c + 2, total_count, bold_border_left)
            worksheet.write(r, c + 3, total, bold_border_left)
        else:
            worksheet.write(r, c, 'Total', bold_border_total)
            worksheet.write(r, c + 1, total_count, bold_border_left)
            worksheet.write(r, c + 2, total, bold_border_left)
        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        name = "INCOME BY COMBO REPORT.xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'income.by.combo.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
