from odoo import models, fields, api, _
import base64
from odoo.tools.misc import xlwt
import io
from odoo.exceptions import UserError
from datetime import datetime


class ClaimWizard(models.TransientModel):
    _name = 'dental.claim.wizard'

    def _get_insurance_company_id(self):
        domain = [('is_insurance_company', '=', True), ('company_id', '=', self.company_id.id)]
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

    def _get_from_date(self):
        todayy = datetime.now().replace(day=1)
        return todayy

    company_id = fields.Many2one('res.company', "Company", domain=_get_company_id, required=True)
    company = fields.Many2one('res.partner', string='Insurance Company', domain=_get_insurance_company_id,
                              required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.today)
    from_date = fields.Date(string='From Date', default=_get_from_date)
    data = fields.Binary('File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose language
                              ('get', 'get')], default='choose')
    name = fields.Char('File Name', readonly=True)

    @api.onchange('company_id')
    def onchange_company_id(self):
        ins_company_domain = self._get_insurance_company_id()
        return {
            'domain': {'company': ins_company_domain}
        }

    @api.model
    def default_get(self, fields):
        res = super(ClaimWizard, self).default_get(fields)
        self._get_company_id()
        res['company_id'] = self.env.user.company_id.id
        self._get_insurance_company_id()
        return res

    @api.multi
    def print_report(self):
        datas = {'active_ids': self.env.context.get('active_ids', []),
                 'form': self.read(['to_date', 'from_date'])[0],
                 }
        values = self.env.ref('basic_insurance.claim_report_qweb').report_action(self, data=datas)
        return values

    @api.multi
    def generate_qlm_coverletter(self, workbook):
        worksheet = workbook.add_sheet('COVER LETTER')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                           "align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                                  "align: wrap on, horiz center, vert center;font: bold on;"
                                  "borders: left medium, right medium, top medium, bottom medium;"
                                  "font: name Verdana, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "borders: left thin, right thin, top thin, bottom thin;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        data_list = []
        c = 0
        r = 4
        output_header = ['No.', 'Name', 'INVOICE NO.', 'MEM NO.', 'REF NO.', 'Total Amt', 'Agreed discount',
                         'Net Amount', 'Pt share', 'QLM Share', 'TT DATE']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 5
            c += 1
        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        sl_no = 0
        gross_total = 0
        disc_total = 0
        net_total = 0
        coshare_total = 0
        ins_amt_total = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                data = []
                sl_no += 1
                data.append(str(sl_no))
                data.append(inv.patient.name.name)
                data.append(inv.number or '')
                if inv.insurance_card.insurance_id_no:
                    data.append(inv.insurance_card.insurance_id_no)
                else:
                    data.append('')
                data.append('')
                gross = 0
                disc = 0
                coshare = inv.amount_total
                for line in inv.invoice_line_ids:
                    gross += line.quantity * line.price_unit
                if inv.is_special_case:
                    if inv.share_based_on == 'Global':
                        disc = gross - inv.after_treatment_grp_disc
                    else:
                        for line in inv.invoice_line_ids:
                            disc += (line.quantity * line.price_unit) - line.after_treatment_grp_disc
                else:
                    disc = inv.treatment_group_disc_total
                ins_amt = gross - disc - coshare
                net = gross - disc
                data.append(gross)
                data.append(disc)
                data.append(net)
                data.append(coshare)
                data.append(ins_amt)
                gross_total += gross
                disc_total += disc
                net_total += net
                coshare_total += coshare
                ins_amt_total += ins_amt
                if apt.appointment_sdate:
                    apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                    apt_date = apt_date.strftime('%d/%m/%Y')
                    data.append(apt_date)
                else:
                    data.append(' ')
                data_list.append(data)
        r += 1
        for data in data_list:
            c = 0
            for item in data:
                if c == 1:
                    worksheet.write(r, c, item, normal_left)
                else:
                    worksheet.write(r, c, item, normal)
                c += 1
            r += 1
        total_list = ['Subtotal :', gross_total, disc_total, net_total, coshare_total, ins_amt_total, '']
        c = 0
        for item in total_list:
            if c == 0:
                worksheet.write_merge(r, r, 0, 4, item, bold_border)
                c = 5
            else:
                worksheet.write(r, c, item, bold_border)
                c += 1
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2

    @api.multi
    def generate_metlife_coverletter(self, workbook):
        worksheet = workbook.add_sheet('COVER LETTER')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                           "align: wrap off, horiz left, vert center;font: bold on;"
                           "font: name Verdana, height 230, color black;", num_format_str='#,##0.00')
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                                  "align: wrap on, horiz center, vert center;font: bold on;"
                                  "borders: left medium, right medium, top medium, bottom medium;"
                                  "font: name Verdana, height 280, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: wrap on, horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        c = 0
        r = 3
        to_date = datetime.strptime(self.to_date, '%Y-%m-%d')
        to_date = to_date.strftime('%B - %Y')
        todayy = fields.Date.context_today(self)
        todayy = datetime.strptime(todayy, '%Y-%m-%d')
        todayy = todayy.strftime('%d-%b-%Y')
        worksheet.write_merge(r, r, c, 4, todayy, bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'Ref No.:', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'To, ', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'The Manager', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, self.company.name, bold)
        r += 1
        if self.company.street or self.company.street2:
            street = self.company.street
            if self.company.street2:
                if street == '':
                    street = self.company.street2
                else:
                    street = street + ', ' + self.company.street2
            worksheet.write_merge(r, r, c, 4, street, bold)
            r += 1

        if self.company.city or self.company.zip:
            zip = self.company.city
            if self.company.zip:
                if zip == '':
                    zip = self.company.zip
                else:
                    zip = zip + ', ' + self.company.zip
            worksheet.write_merge(r, r, c, 4, zip, bold)
            r += 1
        if self.company.phone or self.company.mobile:
            mobile = 'Phone : ' + self.company.phone
            if self.company.zip:
                if mobile == '':
                    mobile = self.company.mobile
                else:
                    mobile = mobile + ', ' + self.company.mobile
            worksheet.write_merge(r, r, c, 4, mobile, bold)
            r += 1
        if self.company.state_id or self.company.country_id:
            state = ''
            if self.company.country_id:
                state = self.company.country_id.name
            if self.company.state_id:
                if state == '':
                    state = self.company.state_id.name
                else:
                    state = state + ', ' + self.company.state_id.name
            worksheet.write_merge(r, r, c, 4, state, bold)
            r += 1

        email = ''
        if self.company.email:
            email = self.company.email
        worksheet.write_merge(r, r+2, c, 4, 'Email :' + email, bold)
        r += 5
        c = 0
        worksheet.write(r, c, 'Dear Sir,', bold)
        r += 2
        worksheet.write_merge(r, r+2, c, 8, 'Sub: Medical Bills of ' + self.company.name + ' ' + to_date, bold_border)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 2
        r += 4

        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        sum = 0
        for inv in inv_data:
            if inv.insurance_invoice and inv.insurance_invoice.state in ('open', 'paid'):
                sum += inv.insurance_invoice.amount_total
        sum_format = "{:.2f}".format(sum)
        sum_words = self.env.user.company_id.currency_id.amount_to_text(sum)
        body = 'Attached are the Medical Bills of  ' + self.company.name + ' for the Month of  ' + to_date +\
               ' with a total amount of ' + self.env.user.company_id.currency_id.name + ' ' + sum_format + ' (' \
               + sum_words + '). Kindly quote the above mentioned reference number when making the payment details.'
        worksheet.write_merge(r, r, c, 8, body, normal)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 300 * 4
        r += 4
        worksheet.write(r, c, 'We would appreciate receiving your payment at the earliest possible time.', normal_left)
        r += 2
        worksheet.write(r, c, 'Thank you.', normal_left)
        r += 2
        worksheet.write(r, c, 'Very truly yours,', normal_left)
        r += 2
        company_name = self.company_id.name
        if self.company_id.state_id:
            company_name = company_name + ', ' + self.company_id.state_id.name
        if self.company_id.country_id:
            company_name = company_name + ', ' + self.company_id.country_id.name
        worksheet.write(r, c, company_name, bold)
        r += 2
        worksheet.write(r, c, 'Prepared by:', bold)
        worksheet.write(r, 7, 'Noted By:', bold)
        r += 2
        worksheet.write(r, c, 'Insurance Coordinator', bold)
        worksheet.write(r, 7, 'MANAGEMENT', bold)
        r += 1
        worksheet.write(r, c, self.company_id.name, bold)
        worksheet.write(r, 7, self.company_id.name, bold)
        r += 1
        worksheet.write(r, c, self.company_id.email, bold)
        r += 1

    @api.multi
    def generate_allianz_coverletter(self, workbook):
        worksheet = workbook.add_sheet('COVER LETTER')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                           "align: wrap off, horiz left, vert center;font: bold on;"
                           "font: name Verdana, height 230, color black;", num_format_str='#,##0.00')
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                                  "align: wrap on, horiz center, vert center;font: bold on;"
                                  "borders: left medium, right medium, top medium, bottom medium;"
                                  "font: name Verdana, height 280, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: wrap on, horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        c = 0
        r = 3
        to_date = datetime.strptime(self.to_date, '%Y-%m-%d')
        to_date = to_date.strftime('%B - %Y')
        todayy = fields.Date.context_today(self)
        todayy = datetime.strptime(todayy, '%Y-%m-%d')
        todayy = todayy.strftime('%d-%b-%Y')
        worksheet.write_merge(r, r, c, 4, todayy, bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'Ref No.:', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'To, ', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, 'The Manager', bold)
        r += 1
        worksheet.write_merge(r, r, c, 4, self.company.name, bold)
        r += 1
        if self.company.street or self.company.street2:
            street = self.company.street
            if self.company.street2:
                if street == '':
                    street = self.company.street2
                else:
                    street = street + ', ' + self.company.street2
            worksheet.write_merge(r, r, c, 4, street, bold)
            r += 1

        if self.company.city or self.company.zip:
            zip = self.company.city
            if self.company.zip:
                if zip == '':
                    zip = self.company.zip
                else:
                    zip = zip + ', ' + self.company.zip
            worksheet.write_merge(r, r, c, 4, zip, bold)
            r += 1
        if self.company.phone or self.company.mobile:
            mobile = 'Phone : ' + self.company.phone
            if self.company.zip:
                if mobile == '':
                    mobile = self.company.mobile
                else:
                    mobile = mobile + ', ' + self.company.mobile
            worksheet.write_merge(r, r, c, 4, mobile, bold)
            r += 1
        if self.company.state_id or self.company.country_id:
            state = ''
            if self.company.country_id:
                state = self.company.country_id.name
            if self.company.state_id:
                if state == '':
                    state = self.company.state_id.name
                else:
                    state = state + ', ' + self.company.state_id.name
            worksheet.write_merge(r, r, c, 4, state, bold)
            r += 1

        worksheet.write_merge(r, r+2, c, 4, 'Email :' + self.company.email, bold)
        r += 5
        c = 0
        worksheet.write(r, c, 'Dear Sir,', bold)
        r += 2
        worksheet.write_merge(r, r+2, c, 8, 'Sub: Medical Bills of ' + self.company.name + ' ' + to_date, bold_border)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 2
        r += 4

        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        sum = 0
        for inv in inv_data:
            if inv.insurance_invoice and inv.insurance_invoice.state in ('open', 'paid'):
                sum += inv.insurance_invoice.amount_total
        sum_format = "{:.2f}".format(sum)
        sum_words = self.env.user.company_id.currency_id.amount_to_text(sum)
        body = 'Attached are the Medical Bills of  ' + self.company.name + ' for the Month of  ' + to_date +\
               ' with a total amount of ' + self.env.user.company_id.currency_id.name + ' ' + sum_format + ' (' \
               + sum_words + '). Kindly quote the above mentioned reference number when making the payment details.'
        worksheet.write_merge(r, r, c, 8, body, normal)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 300 * 4
        r += 4
        worksheet.write(r, c, 'We would appreciate receiving your payment at the earliest possible time.', normal_left)
        r += 2
        worksheet.write(r, c, 'Thank you.', normal_left)
        r += 2
        worksheet.write(r, c, 'Very truly yours,', normal_left)
        r += 2
        company_name = self.company_id.name
        if self.company_id.state_id:
            company_name = company_name + ', ' + self.company_id.state_id.name
        if self.company_id.country_id:
            company_name = company_name + ', ' + self.company_id.country_id.name
        worksheet.write(r, c, company_name, bold)
        r += 2
        worksheet.write(r, c, 'Prepared by:', bold)
        worksheet.write(r, 7, 'Noted By:', bold)
        r += 2
        worksheet.write(r, c, 'Insurance Coordinator', bold)
        worksheet.write(r, 7, 'MANAGEMENT', bold)
        r += 1
        worksheet.write(r, c, self.company_id.name, bold)
        worksheet.write(r, 7, self.company_id.name, bold)
        r += 1
        worksheet.write(r, c, self.company_id.email, bold)
        r += 1

    @api.multi
    def generate_axa_coverletter(self, workbook):
        worksheet = workbook.add_sheet('COVER LETTER')
        bold_title = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                                 "align: wrap on, horiz center, vert center;font: bold on;"
                                 "borders: left medium, right medium, top medium, bottom medium;"
                                 "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                           "align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                                  "align: wrap on, horiz center, vert center;font: bold on;"
                                  "borders: left medium, right medium, top medium, bottom medium;"
                                  "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold_right = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                                 "align: wrap on, horiz right, vert center;font: bold on;"
                                 "borders: left medium, right medium, top medium, bottom medium;"
                                 "font: name Verdana, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "borders: left thin, right thin, top thin, bottom thin;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        normal_right = xlwt.easyxf("align: horiz right, vert center;"
                                   "borders: left thin, right thin, top thin, bottom thin;"
                                   "font: name Verdana;", num_format_str='#,##0.00')
        r = 2
        worksheet.write_merge(r, r, 0, 9, 'SUMMARY OF CLAIMS', bold_title)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 5
        data_list = []
        c = 0
        r = 4
        output_header = ['S/N', 'INVOICE DATE', 'INVOICE NO.', 'POLICY #', 'NAME', 'GROSS AMOUNT', 'DISCOUNT',
                         'EXCESS/ PATIENT PAID', 'NET CLAIM', 'DR. NO.']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 5
            c += 1
        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        sl_no = 0
        gross_total = 0
        disc_total = 0
        coshare_total = 0
        ins_amt_total = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                data = []
                sl_no += 1
                data.append(str(sl_no))
                if apt.appointment_sdate:
                    apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                    apt_date = apt_date.strftime('%d/%m/%Y')
                    data.append(apt_date)
                else:
                    data.append(' ')
                data.append(inv.number or '')
                data.append(inv.insurance_card.number or '')
                data.append(inv.patient.name.name)
                gross = 0
                disc = 0
                coshare = inv.amount_total
                for line in inv.invoice_line_ids:
                    gross += line.quantity * line.price_unit
                if inv.is_special_case:
                    if inv.share_based_on == 'Global':
                        disc = gross - inv.after_treatment_grp_disc
                    else:
                        for line in inv.invoice_line_ids:
                            disc += (line.quantity * line.price_unit) - line.after_treatment_grp_disc
                else:
                    disc = inv.treatment_group_disc_total
                ins_amt = gross - disc - coshare
                data.append(gross)
                data.append(disc)
                data.append(coshare)
                data.append(ins_amt)
                data.append(inv.dentist.code or '')
                gross_total += gross
                disc_total += disc
                coshare_total += coshare
                ins_amt_total += ins_amt
                data_list.append(data)
        r += 1
        for data in data_list:
            c = 0
            for item in data:
                if c == 4:
                    worksheet.write(r, c, item, normal_left)
                    col = worksheet.col(c)
                    col.width = 900 * 9
                else:
                    if c < 4 or c == 9:
                        worksheet.write(r, c, item, normal)
                    else:
                        worksheet.write(r, c, item, normal_right)
                c += 1
            r += 1
        total_list = ['NO. OF CLAIMS: ', str(int(sl_no)), '', 'Subtotal :', gross_total, disc_total, coshare_total,
                      ins_amt_total, '']
        c = 0
        for item in total_list:
            if c == 2:
                worksheet.write_merge(r, r, 2, 3, item, bold_border)
                c = 4
            else:
                if c in (0, 1, 4):
                    worksheet.write(r, c, item, bold_border)
                else:
                    worksheet.write(r, c, item, bold_right)
                c += 1
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 2

    @api.multi
    def generate_qlm_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                           "align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        c = 0

        data_list = []
        output_header = ['Patient Name', 'MEM ID', 'Date of Birth', 'Nationality', 'Country of Residence', 'Sex',
                         'Mobile', 'Invoice Number',
                         'Healthcare Professional', 'Healthcare Professional ID', 'Healthcare Professional Type',
                         'Episode Number', 'Doctor', 'Appointment Start',
                         'Appointment End', 'State', 'Treatment', 'Treatment Code', 'Treatment price',
                         'Treatment group discount(%)', 'Co-payment', 'Amount paid by patient']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 5
            c += 1
        inv_data = self.env['account.invoice'].search(
            [('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
             ('patient', '!=', False), ('insurance_company', '=', self.company.id),
             ('state', 'in', ('open', 'paid')),
             ('company_id', '=', self.company_id.id)])
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    data.append(inv.patient.name.name)
                    if inv.insurance_card.insurance_id_no:
                        data.append(inv.insurance_card.insurance_id_no)
                    else:
                        data.append('')
                    if inv.patient.dob:
                        apt_date = datetime.strptime(inv.patient.dob, '%Y-%m-%d').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append(' ')
                    if inv.patient.nationality_id:
                        data.append(inv.patient.nationality_id.name)
                    else:
                        data.append('')
                    if inv.patient.name.country_id:
                        data.append(inv.patient.name.country_id.name)
                    else:
                        data.append('')
                    if inv.patient.sex:
                        if inv.patient.sex == 'm':
                            data.append('Male')
                        else:
                            data.append('Female')
                    else:
                        data.append('')
                    data.append(inv.patient.mobile or '')
                    data.append(inv.number or '')
                    if inv.dentist:
                        data.append(inv.dentist.name.name)
                    else:
                        data.append('')
                    data.append(inv.dentist.code or '')
                    if inv.dentist.speciality:
                        data.append(inv.dentist.speciality.name)
                    else:
                        data.append('')
                    if apt:
                        data.append(apt.name)
                        if apt.doctor:
                            data.append(apt.doctor.name.name)
                        else:
                            data.append(' ')
                        if apt.appointment_sdate:
                            apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                            apt_date = apt_date.strftime('%d/%m/%Y')
                            data.append(apt_date)
                        else:
                            data.append(' ')
                        if apt.appointment_edate:
                            appointment_edate = datetime.strptime(apt.appointment_edate, '%Y-%m-%d %H:%M:%S').date()
                            appointment_edate = appointment_edate.strftime('%d/%m/%Y')
                            data.append(appointment_edate)
                        else:
                            data.append(' ')
                        data.append(apt.state or '')
                    else:
                        data.append('')
                        data.append('')
                        data.append('')
                        data.append('')
                        data.append('')
                    data.append(line.product_id.name or '')
                    data.append(line.product_id.default_code or '')
                    data.append(line.price_unit)
                    data.append(line.discount_amt)
                    data.append(line.amt_paid_by_patient)
                    data.append(line.price_subtotal)
                    data_list.append(data)

        r += 1
        for data in data_list:
            c = 0
            for item in data:
                worksheet.write(r, c, item, normal)
                c += 1
            r += 1

    @api.multi
    def generate_nextcare_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("font: bold on;", num_format_str='#,##0.00')
        r = 0
        c = 3
        output_header = ['INSURANCE CLAIM SHEET']
        for item in output_header:
            worksheet.write(r, c, item, bold)
        r += 2
        c = 0
        from_date = (datetime.strptime(self.from_date, '%Y-%m-%d'))
        from_date = from_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        to_date = (datetime.strptime(self.to_date, '%Y-%m-%d'))
        to_date = to_date.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
        output_header = ['Period From:', from_date, 'Period To:', to_date]
        for item in output_header:
            worksheet.write(r, c, item, bold)
            c += 2
        r += 1
        c = 0
        output_header = ['Insurance Company:', self.company.name,
                         'Report Date:', datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                         'Company:', self.company_id.name,
                         ]
        for item in output_header:
            worksheet.write(r, c, item, bold)
            c += 2
        normal = xlwt.easyxf(num_format_str='#,##0.00')
        r += 2
        c = 0
        data_list = []
        Amt_company = 'Amount(' + self.company.name + ')'
        output_header = ['SN', 'TRT DATE', 'FILE NO.', 'INV. NO.', 'Policy Number', 'Patient Name',
                         'Service Code', 'Service Description',
                         'GROSS', 'Discount (00%)', 'NET',
                         'Paid by Member', Amt_company, 'Approval Code', 'Approved amount', 'Insurance total']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            c += 1
        inv_data = self.env['account.invoice'].search \
            ([('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
              ('patient', '!=', False), ('insurance_company', '=', self.company.id),
              ('state', 'in', ('open', 'paid')), ('company_id', '=', self.company_id.id)])
        sl_no = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if count:
                for line in inv.invoice_line_ids:
                    if line.apply_insurance:
                        data = []
                        sl_no += 1
                        data.append(sl_no)
                        date_inv = ''
                        if inv.date_invoice:
                            date_inv = (datetime.strptime(inv.date_invoice, '%Y-%m-%d'))
                            date_inv = date_inv.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
                        data.append(date_inv)
                        data.append(inv.patient.patient_id)
                        data.append(inv.number)
                        data.append(inv.insurance_card.number)
                        data.append(inv.patient.name.name)
                        data.append(line.product_id.default_code or '')
                        data.append(line.product_id.name or '')
                        gross = line.quantity * line.price_unit
                        data.append(gross)
                        data.append(line.discount_amt)
                        ins_total = 0
                        treatment_total = 0
                        if line.insurance_cases == 'case_1':
                            treatment_total += (line.price_unit * line.quantity * line.discount_amt) / 100
                            ins_total += (line.price_unit * line.quantity * line.amt_paid_by_insurance) / 100
                        if line.insurance_cases in ('case_3', 'case_2'):
                            treatment_total += (line.price_unit * line.quantity * line.discount_amt) / 100
                            total_payable = line.price_unit * line.quantity - treatment_total
                            ins_total += (total_payable * line.amt_paid_by_insurance) / 100
                        data.append(gross - treatment_total)
                        data.append(line.price_initial_copay)
                        data.append(ins_total)
                        data.append(inv.ins_approval_code)
                        data.append(inv.ins_approved_amt)
                        data.append(inv.insurance_total)
                        data_list.append(data)
                    else:
                        consultation_companies = [ins_company.id for ins_company in
                                                  line.product_id.consultation_insurance_company_ids]
                        if inv.insurance_company.id == inv.insurance_card.company_id.id and \
                                        inv.insurance_company.id in consultation_companies:
                            data = []
                            sl_no += 1
                            data.append(sl_no)
                            date_inv = ''
                            if inv.date_invoice:
                                date_inv = (datetime.strptime(inv.date_invoice, '%Y-%m-%d'))
                                date_inv = date_inv.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
                            data.append(date_inv)
                            data.append(inv.patient.patient_id)
                            data.append(inv.number)
                            data.append(inv.insurance_card.number)
                            data.append(inv.patient.name.name)
                            data.append(line.product_id.default_code or '')
                            data.append(line.product_id.name or '')
                            gross = line.quantity * line.price_unit
                            data.append(gross)
                            data.append(line.discount_amt)
                            data.append(gross)
                            if inv.insurance_card.deductible:
                                check_consultation_amt = inv.insurance_card.deductible
                            else:
                                check_consultation_amt = line.price_unit
                            data.append(check_consultation_amt)
                            data.append(gross - check_consultation_amt)
                            data.append(inv.ins_approval_code)
                            data.append(inv.consult_approved_amt)
                            data.append(inv.insurance_total)
                            data_list.append(data)
        r += 1
        for data in data_list:
            c = 0
            for item in data:
                worksheet.write(r, c, item, normal)
                c += 1
            r += 1

    @api.multi
    def generate_alkoot_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color red;")
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        c = 0

        data_list = []
        output_header = ['', 'INVOICE NO.', 'MEMBER NAME', 'MEMBER ID', 'PreApproval No.',
                         'DATE OF TREATMENT /ADMISSION', 'DATE OF DISCHARGE', 'SYSTEM OF MEDICINE', 'BENEFIT TYPE',
                         'ENCOUNTER TYPE', 'CLINICIAN ID', 'CLINICIAN NAME', 'SYMPTOMS', 'PRINCIPAL ICD CODE',
                         'ICD DESCRIPTION', 'SECONDARY ICD CODE 1', 'SECONDARY ICD CODE 2', 'SECONDARY ICD CODE 3',
                         'SECONDARY ICD CDOE 4', 'SECONDARY ICD CODE 5', 'FIRST  INCIDENT DATE', 'FIRST REPORTED DATE',
                         'SERVICE DATE', 'Activity Type', 'INTERNAL  SERVICE CODE', 'SERVICE DESCRIPTION',
                         'CPT CODE', 'AMOUNT CLAIMED (GROSS AMOUNT)', 'QUANTITY', 'Tooth Number (For Dental Only)',
                         'Date of LMP (For Maternity Only)', 'Nature Of Conception(For Maternity Only)',
                         'OBSERVATION', 'Event Reference Number']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1
        inv_data = self.env['account.invoice'].search \
            ([('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
              ('patient', '!=', False), ('insurance_company', '=', self.company.id),
              ('state', 'in', ('open', 'paid')),
              ('company_id', '=', self.company_id.id)])
        sl_no = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                sl_no += 1
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    data.append(str(sl_no))
                    if inv.insurance_invoice:
                        data.append(inv.insurance_invoice.number)
                    else:
                        data.append('')
                    data.append(inv.patient.name.name)
                    if inv.insurance_card.insurance_id_no:
                        data.append(inv.insurance_card.insurance_id_no)
                    else:
                        data.append('')
                    if inv.pre_approval_code:
                        data.append(inv.pre_approval_code)
                    else:
                        data.append('')
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append(' ')
                    data.append(' ')
                    data.append('Allopathy')
                    if apt.benefit_type:
                        data.append(apt.benefit_type)
                    else:
                        data.append('')
                    data.append('OP No-Emergency')
                    data.append(inv.dentist.code or '')
                    if inv.dentist:
                        data.append(inv.dentist.name.name)
                    else:
                        data.append('')
                    data.append('')
                    if line.diagnosis_id:
                        data.append(line.diagnosis_id.code)
                        data.append(line.diagnosis_id.description)
                    else:
                        data.append('')
                        data.append('')
                    data.append('')
                    data.append('')
                    data.append('')
                    data.append('')
                    data.append('')
                    data.append('')
                    data.append('')
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append(' ')
                    data.append('Activity')
                    data.append(line.product_id.default_code or '')
                    data.append(line.product_id.name or '')
                    data.append('')
                    data.append(line.price_unit)
                    data.append(str(int(line.quantity)))
                    tooth = ''
                    for i in line.teeth_code_rel:
                        tooth = tooth + i.name_get()[0][1] + ', '
                    data.append(tooth)
                    data.append('')
                    data.append('')
                    data.append('OBSERVATION')
                    data.append('')
                    data_list.append(data)

        r += 1
        for data in data_list:
            c = 0
            for item in data:
                worksheet.write(r, c, item, normal)
                c += 1
            r += 1

    @api.multi
    def generate_axa_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour light_green;"
                           "align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color black;")
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        c = 0

        data_list = []
        output_header = ['SERIAL NO.', 'POLICY NO', 'INSURED CODE', 'INSURED NAME', 'GENDER',
                         'DATE OF BIRTH', 'HOSPITAL CODE', 'CLAIM DATE', 'CLAIM FORM NO',
                         'APPROVAL CODE', 'SYMPTOMS', 'DIAGNOSIS-ICD', 'DIAGNOSIS DESCRIPTION',
                         'FIRST INCIDENT DATE', 'FIRST REPORTED DATE', 'MAIN TREATMENT CODE',
                         'SUBCOVER', 'DOCTOR', 'LIC. NO.', 'REFERRAL', 'REFERRAL PROVIDER',
                         'SERVICE DATE', 'SERVICE CODE', 'SERVICE DESCRIPTION', 'GROSS', 'DISCOUNT',
                         'BILL NO.', 'TOOTH NUMBER', 'INPATIENT START DATE', 'INPATIENT END DATE',
                         'CLAIM COMMENTS', 'OPERATION COMMENTS']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1
        inv_data = self.env['account.invoice'].search \
            ([('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
              ('patient', '!=', False), ('insurance_company', '=', self.company.id),
              ('state', 'in', ('open', 'paid')),
              ('company_id', '=', self.company_id.id)])
        #         data = []
        sl_no = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                sl_no += 1
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    data.append(str(sl_no))
                    data.append(inv.insurance_card.number or '')
                    if inv.insurance_card.insurance_id_no:
                        data.append(inv.insurance_card.insurance_id_no)
                    else:
                        data.append('')
                    data.append(inv.patient.name.name)
                    if inv.patient.sex:
                        if inv.patient.sex == 'm':
                            data.append('MALE')
                        else:
                            data.append('FEMALE')
                    else:
                        data.append('')
                    if inv.patient.dob:
                        data.append(inv.patient.dob)
                    else:
                        data.append('')
                    data.append('2236')
                    date_inv = ''
                    if inv.date_invoice:
                        date_inv = (datetime.strptime(inv.date_invoice, '%Y-%m-%d'))
                        date_inv = date_inv.strftime('%d/%m/%Y %H:%M:%S').split(' ')[0]
                    data.append(date_inv)
                    if inv.claim_form_num:
                        data.append(inv.claim_form_num)
                    else:
                        data.append('')
                    if inv.pre_approval_code:
                        data.append(inv.pre_approval_code)
                    else:
                        data.append('')
                    data.append('')
                    if line.diagnosis_id:
                        data.append(line.diagnosis_id.code)
                        data.append(line.diagnosis_id.description)
                    else:
                        data.append('')
                        data.append('')
                    data.append('')
                    data.append('')
                    data.append('DENTAL')
                    data.append('')
                    if inv.dentist:
                        data.append(inv.dentist.name.name)
                    else:
                        data.append('')
                    if inv.dentist.code:
                        data.append(inv.dentist.code)
                    else:
                        data.append('')
                    data.append('')
                    if apt.referral_dr_id:
                        data.append(apt.referral_dr_id.name)
                    else:
                        data.append('')
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append('')
                    data.append(line.product_id.default_code or '')
                    data.append(line.product_id.name or '')
                    gross = line.price_unit * line.quantity
                    if inv.is_special_case:
                        if inv.share_based_on == 'Global':
                            disc = 0
                            copay = 0
                        else:
                            disc = gross - line.after_treatment_grp_disc
                            copay = line.patient_share
                    else:
                        disc = (gross * line.discount_amt) / 100
                        copay = line.price_initial_case_3_copay
                    data.append(gross)
                    data.append(disc)
                    if inv.insurance_invoice:
                        data.append(inv.insurance_invoice.number)
                    else:
                        data.append('')
                    tooth = ''
                    for i in line.teeth_code_rel:
                        tooth = tooth + i.name_get()[0][1] + ', '
                    data.append(tooth)
                    data.append('')
                    data.append('')
                    if copay:
                        copay = str(copay)
                    else:
                        copay = 'NIL'
                    claim = 'APPROVED AMOUNT ' + str(gross - disc) + '/ ' + 'COINSURANCE- ' + copay
                    data.append(claim)
                    data.append('')
                    data_list.append(data)
        r += 1
        for data in data_list:
            c = 0
            for item in data:
                worksheet.write(r, c, item, normal)
                c += 1
            r += 1

    @api.multi
    def generate_globemed_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color red;")
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        c = 0

        data_list = []
        output_header = ['S/Nmmm', 'Invoice / Bill Date', 'Invoice No.', 'File No.', 'Insurance Card #', 'Patient Name',
                         'Bill Amount / Gross Amount', 'Discount', 'Excess / Patient Paid', 'Net Claim', 'Doctor No.']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1
        inv_data = self.env['account.invoice'].search \
            ([('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
              ('patient', '!=', False), ('insurance_company', '=', self.company.id),
              ('state', 'in', ('open', 'paid')),
              ('company_id', '=', self.company_id.id)])
        sl_no = 0
        c = 0
        r += 1
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                sl_no += 1
                data = []
                data.append(str(sl_no))
                date_inv = ''
                if inv.date_invoice:
                    date_inv = datetime.strptime(inv.date_invoice, '%Y-%m-%d')
                    date_inv = date_inv.strftime('%d/%b/%Y')
                data.append(date_inv)
                if inv.insurance_invoice:
                    data.append(inv.insurance_invoice.number)
                else:
                    data.append('')
                data.append(inv.patient.patient_id)
                if inv.insurance_card.number:
                    data.append(inv.insurance_card.number)
                else:
                    data.append('')
                data.append(inv.patient.name.name)
                gross = 0
                disc = 0
                coshare = inv.amount_total
                for line in inv.invoice_line_ids:
                    gross += line.quantity * line.price_unit
                if inv.is_special_case:
                    if inv.share_based_on == 'Global':
                        disc = gross - inv.after_treatment_grp_disc
                    else:
                        for line in inv.invoice_line_ids:
                            disc += (line.quantity * line.price_unit) - line.after_treatment_grp_disc
                else:
                    disc = inv.treatment_group_disc_total
                ins_amt = gross - disc - coshare
                data.append(gross)
                data.append(disc)
                data.append(coshare)
                data.append(ins_amt)
                if inv.dentist.code:
                    data.append(inv.dentist.code)
                else:
                    data.append('')
                data_list.append(data)
        for dat in data_list:
            for item in dat:
                worksheet.write(r, c, item, normal)
                c += 1
            c = 0
            r += 1

    @api.multi
    def generate_allianz_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold_black = xlwt.easyxf("align: wrap on, horiz center, vert center;font: bold on;"
                                 "borders: left medium, right medium, top medium, bottom medium;"
                                 "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold = xlwt.easyxf("align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color red;")
        normal_right = xlwt.easyxf("align: horiz right, vert center;"
                                   "borders: left thin, right thin, top thin, bottom thin;"
                                   "font: name Verdana;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "borders: left thin, right thin, top thin, bottom thin;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        sl_no = 0
        ins_total = 0
        for insu in inv_data:
            sl_no += 1
            if insu.insurance_invoice:
                ins_total += insu.insurance_invoice.amount_total
        r = 0
        c = 0
        worksheet.write(r, c, 'Submitter', bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        c += 1
        worksheet.write(r, c, self.company_id.name, bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 0
        worksheet.write(r, c, 'Submitter Batch Reference', bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        c += 1
        worksheet.write(r, c, '', bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 0
        worksheet.write(r, c, 'Total Number of Invoices', bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        c += 1
        worksheet.write(r, c, str(sl_no), bold_black)
        r += 1
        c = 0
        worksheet.write(r, c, 'Total Amount to be Paid', bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        c += 1
        worksheet.write(r, c, ins_total, bold_black)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        r += 1
        c = 0

        data_list = []
        output_header = ['Policy Number', 'Patient Date of Birth', 'Surname', 'First Name', 'Localised Surname',
                         'Localised First Name', 'Provider Invoice Number', 'Provider Name', 'Localised Provider Name',
                         'Country of Treatment', 'Gross Invoice Amount', 'Invoice Currency', 'Invoice Date', 'Discount',
                         'Patient Fee', 'Treatment From Date', 'Treatment To Date', 'Net Invoice Amount', 'Cover',
                         'Sub-Cover', 'Treatment', 'Diagnosis Code (ICD) Required Field', 'Diagnosis Required Field',
                         'Procedure Code',
                         'Procedure Description', 'Claim type', 'Emergency', 'Date of Onset of Symptoms',
                         'Physician Specialty',
                         'APPROVAL CODE', 'COMPANY', 'DOCTORS NAME']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1

        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    data.append(inv.insurance_card.number or '')
                    if inv.patient.dob:
                        dob = datetime.strptime(inv.patient.dob, '%Y-%m-%d')
                        dob = dob.strftime('%d-%B-%Y')
                        data.append(dob)
                    else:
                        data.append('')
                    data.append('')
                    data.append(inv.patient.name.name)
                    data.append('')
                    data.append('')
                    if inv.insurance_invoice:
                        data.append(inv.insurance_invoice.number)
                    else:
                        data.append('')
                    data.append(self.company_id.name)
                    data.append('')
                    data.append('QAT')
                    gross = line.price_unit * line.quantity
                    disc = 0
                    copay = 0
                    if inv.is_special_case:
                        if inv.share_based_on == 'Global':
                            disc = 0
                            copay = 0
                        else:
                            disc = gross - line.after_treatment_grp_disc
                            copay = line.patient_share
                    else:
                        disc = (gross * line.discount_amt) / 100
                        copay = line.price_initial_case_3_copay
                    data.append(gross)
                    data.append('QAR')
                    date_inv = ''
                    if inv.date_invoice:
                        date_inv = datetime.strptime(inv.date_invoice, '%Y-%m-%d')
                        date_inv = date_inv.strftime('%d/%b/%Y')
                    data.append(date_inv)
                    data.append(disc)
                    data.append(copay)
                    apt_date = ''
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%b/%Y')
                    data.append(apt_date)
                    data.append(apt_date)
                    ins_amt = gross - disc - copay
                    data.append(ins_amt)
                    data.append('')
                    data.append('')
                    data.append('')
                    if line.diagnosis_id:
                        data.append(line.diagnosis_id.code)
                        data.append(line.diagnosis_id.description)
                    else:
                        data.append('')
                        data.append('')
                    data.append(line.product_id.default_code or '')
                    data.append(line.product_id.name or '')
                    data.append('Outpatient')
                    if apt.urgency:
                        data.append('Yes')
                    else:
                        data.append('No')
                    data.append(apt_date)
                    speciality = ''
                    if inv.dentist.speciality:
                        speciality = inv.dentist.speciality.name
                    data.append(speciality)
                    if inv.pre_approval_code:
                        data.append(inv.pre_approval_code)
                    else:
                        data.append('')
                    if inv.insurance_card.group_name:
                        data.append(inv.insurance_card.group_name)
                    else:
                        data.append('')
                    if inv.dentist:
                        data.append(inv.dentist.name.name)
                    else:
                        data.append('')
                    data_list.append(data)

        r += 1
        for data in data_list:
            c = 0
            for item in data:
                if c in (10, 13, 14, 17):
                    worksheet.write(r, c, item, normal_right)
                elif c in (2, 3, 24, 25, 28, 29, 30, 31):
                    worksheet.write(r, c, item, normal_left)
                else:
                    worksheet.write(r, c, item, normal)
                c += 1
            r += 1

    @api.multi
    def generate_mednet_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold_red = xlwt.easyxf("pattern: pattern solid, fore-colour dark_purple;"
                               "align: wrap on, horiz center, vert center;font: bold on;"
                               "borders: left medium, right medium, top medium, bottom medium;"
                               "font: name Verdana, color white;", num_format_str='#,##0.00')
        bold = xlwt.easyxf("pattern: pattern solid, fore-colour grey25;"
                           "align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana, color black;", num_format_str='#,##0.00')
        bold_nocolor = xlwt.easyxf("pattern: pattern solid, fore-colour white;"
                                   "align: wrap on, horiz center, vert center;font: bold on;"
                                   "borders: left medium, right medium, top medium, bottom medium;"
                                   "font: name Verdana, color black;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        worksheet.write_merge(0, 0, 0, 10, 'STATEMENT OF ACCOUNT', bold_red)
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 3
        worksheet.write_merge(2, 2, 0, 5, 'Provider Name: ' + self.company_id.name, bold_nocolor)
        worksheet.write_merge(2, 2, 6, 10, 'Billing Month: ', bold_nocolor)
        worksheet.write_merge(3, 3, 0, 5, 'Provider Code: E16', bold_nocolor)
        worksheet.write_merge(3, 3, 6, 10, 'Claim Type: DENTAL', bold_nocolor)
        c = 0
        r = 5
        data_list = []
        output_header = ['SN', 'FILE NO.', 'Mednet Card No', 'Patient Name', 'Service Date', 'Invoice No',
                         'Gross Amount', 'Discount', 'Co-Payment/ Deductible', 'Net Amount', 'Dr. No.']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1
        inv_data = self.env['account.invoice'].search \
            ([('date_invoice', '>=', self.from_date), ('date_invoice', '<=', self.to_date),
              ('patient', '!=', False), ('insurance_company', '=', self.company.id),
              ('state', 'in', ('open', 'paid')),
              ('company_id', '=', self.company_id.id)])
        #         data = []
        sl_no = 0
        gross_total = 0
        disc_total = 0
        coshare_total = 0
        ins_amt_total = 0
        inv_len = len(inv_data.ids)
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    sl_no += 1
                    data.append(str(sl_no))
                    data.append(inv.patient.patient_id)
                    if inv.insurance_card.insurance_id_no:
                        data.append(inv.insurance_card.insurance_id_no)
                    else:
                        data.append('')
                    data.append(inv.patient.name.name)
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append(' ')
                    if inv.insurance_invoice:
                        data.append(inv.insurance_invoice.number)
                    else:
                        data.append('')
                    gross = line.price_unit * line.quantity
                    if inv.is_special_case:
                        if inv.share_based_on == 'Global':
                            disc = 0
                            copay = 0
                        else:
                            disc = gross - line.after_treatment_grp_disc
                            copay = line.patient_share
                    else:
                        disc = (gross * line.discount_amt) / 100
                        copay = line.price_initial_case_3_copay
                    data.append(gross)
                    data.append(disc)
                    data.append(copay)
                    ins_amt = gross - disc - copay
                    data.append(ins_amt)
                    gross_total += gross
                    disc_total += disc
                    coshare_total += copay
                    ins_amt_total += ins_amt
                    if inv.dentist.code:
                        data.append(inv.dentist.code)
                    else:
                        data.append('')
                    data_list.append(data)

        r += 1
        for data in data_list:
            c = 0
            for item in data:
                worksheet.write(r, c, item, normal)
                c += 1
            r += 1
        c = 0
        total_list = ['TOTAL CLAIMS :', str(int(inv_len)), '', '', '', 'TOTAL', gross_total, disc_total, coshare_total,
                      ins_amt_total, '']
        for item in total_list:
            worksheet.write(r, c, item, bold)
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 4
            c += 1

    @api.multi
    def generate_metlife_report(self, workbook):
        worksheet = workbook.add_sheet('Claim Report')
        bold = xlwt.easyxf("align: wrap on, horiz center, vert center;font: bold on;"
                           "borders: left medium, right medium, top medium, bottom medium;"
                           "font: name Verdana;", num_format_str='#,##0.00')
        bold_right = xlwt.easyxf("align: wrap on, horiz right, vert center;font: bold on;"
                                 "borders: left medium, right medium, top medium, bottom medium;"
                                 "font: name Verdana;", num_format_str='#,##0.00')
        normal = xlwt.easyxf("align: horiz center, vert center;"
                             "borders: left thin, right thin, top thin, bottom thin;"
                             "font: name Verdana;", num_format_str='#,##0.00')
        normal_left = xlwt.easyxf("align: horiz left, vert center;"
                                  "borders: left thin, right thin, top thin, bottom thin;"
                                  "font: name Verdana;", num_format_str='#,##0.00')
        normal_right = xlwt.easyxf("align: horiz right, vert center;"
                                   "borders: left thin, right thin, top thin, bottom thin;"
                                   "font: name Verdana;", num_format_str='#,##0.00')
        no_border = xlwt.easyxf("align: horiz center, vert center;"
                                "font: name Verdana;", num_format_str='#,##0.00')
        r = 0
        c = 0

        data_list = []
        output_header = ['Claim Form No', 'File No', 'Visit Date', 'Bill No', 'Policy No', 'Membership ID',
                         'Activity Code', 'Activity name', 'Encounter start date', 'Encounter end date', 'Quantity',
                         'Gross Amount', 'Discount', 'Co-pay', 'Net Amount']
        for item in output_header:
            worksheet.write(r, c, item, bold)
            col = worksheet.col(c)
            col.width = 900 * 6
            worksheet.row(r).height_mismatch = True
            worksheet.row(r).height = 200 * 6
            c += 1
        inv_data = self.env['account.invoice'].search([('date_invoice', '>=', self.from_date),
                                                       ('date_invoice', '<=', self.to_date),
                                                       ('patient', '!=', False),
                                                       ('insurance_company', '=', self.company.id),
                                                       ('state', 'in', ('open', 'paid')),
                                                       ('company_id', '=', self.company_id.id)])
        gross_total = 0
        disc_total = 0
        copay_total = 0
        ins_total = 0
        for inv in inv_data:
            count = 0
            if inv.insurance_invoice:
                if inv.insurance_invoice.state in ('open', 'paid'):
                    count = 1
            if inv.appt_id and count:
                apt = inv.appt_id
                for line in inv.invoice_line_ids:
                    data = []
                    if inv.claim_form_num:
                        data.append(inv.claim_form_num)
                    else:
                        data.append('')
                    data.append(inv.patient.patient_id)
                    apt_date = ''
                    if apt.appointment_sdate:
                        apt_date = datetime.strptime(apt.appointment_sdate, '%Y-%m-%d %H:%M:%S').date()
                        apt_date = apt_date.strftime('%d/%m/%Y')
                        data.append(apt_date)
                    else:
                        data.append(' ')
                    if inv.insurance_invoice:
                        data.append(inv.insurance_invoice.number)
                    else:
                        data.append('')
                    if inv.insurance_card.number:
                        data.append(inv.insurance_card.number)
                    else:
                        data.append('')
                    if inv.insurance_card.insurance_id_no:
                        data.append(inv.insurance_card.insurance_id_no)
                    else:
                        data.append('')
                    data.append(line.product_id.default_code or '')
                    data.append(line.product_id.name or '')
                    data.append(apt_date)
                    data.append(apt_date)
                    data.append(str(int(line.quantity)))
                    gross = line.price_unit * line.quantity
                    if inv.is_special_case:
                        if inv.share_based_on == 'Global':
                            disc = 0
                            copay = 0
                        else:
                            disc = gross - line.after_treatment_grp_disc
                            copay = line.patient_share
                    else:
                        disc = (gross * line.discount_amt) / 100
                        copay = line.price_initial_case_3_copay
                    data.append(gross)
                    data.append(disc)
                    data.append(copay)
                    ins_amount = gross - disc - copay
                    data.append(ins_amount)
                    gross_total += gross
                    disc_total += disc
                    copay_total += copay
                    ins_total += ins_amount
                    data_list.append(data)

        r += 1
        for data in data_list:
            c = 0
            for item in data:
                if c in (11, 12, 13, 14):
                    worksheet.write(r, c, item, normal_right)
                else:
                    worksheet.write(r, c, item, normal)
                c += 1
            r += 1
        r += 1
        c = 0
        total_list = ['', '', '', '', '', '', '', '', '', '']
        for item in total_list:
            worksheet.write(r, c, item, no_border)
            c += 1
        total_list = ['TOTAL :  ', gross_total, disc_total, copay_total, ins_total]
        for item in total_list:
            worksheet.write(r, c, item, bold_right)
            c += 1
        worksheet.write(r, c, '', no_border)
        c += 1

    @api.multi
    def generate_backlog_excel_report(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        if not self.company.insur_report_format:
            raise UserError(_("Assign Report format for this Insurance Company"))
        if self.company.insur_report_format == 'qlm':
            self.generate_qlm_report(workbook)
            self.generate_qlm_coverletter(workbook)

        if self.company.insur_report_format == 'alkoot':
            self.generate_alkoot_report(workbook)

        if self.company.insur_report_format == 'nextcare_allianz':
            self.generate_nextcare_report(workbook)
            self.generate_allianz_coverletter(workbook)

        if self.company.insur_report_format == 'axa':
            self.generate_axa_report(workbook)
            self.generate_axa_coverletter(workbook)

        if self.company.insur_report_format == 'allianz':
            self.generate_allianz_report(workbook)
            self.generate_allianz_coverletter(workbook)

        if self.company.insur_report_format == 'globemed':
            self.generate_globemed_report(workbook)
            self.generate_metlife_coverletter(workbook)

        if self.company.insur_report_format == 'mednet':
            self.generate_mednet_report(workbook)
            self.generate_metlife_coverletter(workbook)

        if self.company.insur_report_format == 'metlife':
            self.generate_metlife_report(workbook)
            self.generate_metlife_coverletter(workbook)
        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        todayy = fields.Date.context_today(self)
        todayy = datetime.strptime(todayy, '%Y-%m-%d')
        todayy = todayy.strftime('%d-%m-%Y')
        name = self.company.name + "_claim_report_" + todayy + ".xls"
        self.write({'state': 'get', 'data': out, 'name': name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dental.claim.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
