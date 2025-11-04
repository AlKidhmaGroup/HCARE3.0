from odoo import models, fields, api, tools,_
from odoo.tools.misc import xlwt,DEFAULT_SERVER_DATETIME_FORMAT


import io
import pytz
import base64

class NewModule(models.TransientModel):
    _inherit = 'doctor.appointment.report'

    def doctor_appointment_excel_report(self):
        dom = [
            ('appointment_sdate', '>=', self.period_start),
            ('appointment_edate', '<=', self.period_stop),
            ('company_id', '=', self.company_id.id),
        ]
        if self.doctor:
            dom.append(('doctor', '=', self.doctor.id))
        if self.state:
            dom.append(('state', '=', self.state))
        if self.patient_type == 'self':
            dom.append(('insurance_id', '=', False))
        elif self.patient_type == 'insurance':
            dom.append(('insurance_id', '!=', False))

        doctors = self.env['medical.physician'].search([('company_id', '=', self.company_id.id)])
        doctrs = []
        doctrs_list = []
        appts = {}
        for i in doctors:
            doctrs.append(i.id)
            appts[i.id] = []
        appointments = self.env['medical.appointment'].search(dom, order="appointment_sdate asc")
        for app in appointments:
            appts[app.doctor.id].append(app)
        for each in doctrs:
            appts[each] = appts.pop(each)
            doctrs_list.append(each)
        period_start = fields.datetime.strptime(self.period_start, '%Y-%m-%d %H:%M:%S')
        period_stop = fields.datetime.strptime(self.period_stop, '%Y-%m-%d %H:%M:%S')


        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Appointment Book Report')

        title = xlwt.easyxf("font: name Times New Roman,height 400, color black, bold True, name Arial;"
                            " align: horiz center, vert center;")
        bold = xlwt.easyxf("font: name Times New Roman, color-index black, bold on;align: horiz center, vert center;")
        date_Style = xlwt.easyxf(
            "font: name Times New Roman, color-index black, bold on;align: horiz center, vert center;")
        date_Style.num_format_str = 'dd/mm/yyyy'
        bold_border = xlwt.easyxf("pattern: pattern solid, fore-colour teal_ega; "
                                  "font: name Times New Roman, color white, bold on;"
                                  "align: horiz center, vert center; "
                                  "borders: left thin, right thin, top thin, bottom medium;")
        no_border = xlwt.easyxf("font: name Times New Roman, bold on;")
        normal_no_border = xlwt.easyxf("pattern: pattern solid, fore-colour teal_ega; "
                                       "font: name Times New Roman, color white, bold on;")
        normal = xlwt.easyxf(
            "font: name Times New Roman,color black, bold True, name Arial;"
            "align: wrap on, horiz center, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        normal_green = xlwt.easyxf(
            "font: name Times New Roman,color green, bold True, name Arial;"
            "align: wrap on, horiz center, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        normal_red = xlwt.easyxf(
            "font: name Times New Roman,color red, bold True, name Arial;"
            "align: wrap on, horiz center, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        normal_colored = xlwt.easyxf(
            "font: name Times New Roman, color black;"
            "align: horiz center, vert center; "
            "borders: left thin, right thin, top thin, bottom medium;")
        normal_date = xlwt.easyxf(
            "align: wrap on, horiz center, vert center;"
            "borders: left thin, right thin, top thin, bottom thin;")
        normal_date.num_format_str = 'dd/mm/yyyy'

        normal2 = xlwt.easyxf("align: wrap on, horiz center, vert center;"
                              "borders: left thin, right thin, top thin, bottom thin;")
        r = 0
        c = 1
        worksheet.write_merge(r, r, 0,3, self.env.user.company_id.name, no_border)


        col = worksheet.col(c)
        col.width = 1250 * 4
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 2
        r += 2
        c = 4
        tz = self.env.user.tz

        worksheet.write(r, c, 'Appointment Report' , title)
        col = worksheet.col(c)
        col.width = 1250 * 4
        worksheet.row(r).height_mismatch = True
        worksheet.row(r).height = 200 * 2
        r += 1
        c= 0

        period_start = fields.datetime.strptime(self.period_start, DEFAULT_SERVER_DATETIME_FORMAT)
        period_start = fields.Datetime.context_timestamp(self.with_context(tz=tz), timestamp=period_start).replace(tzinfo=None)

        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)

        date_format = lang_id.date_format
        time_format = lang_id.time_format
        date_time_format = date_format +' '+time_format

        worksheet.write_merge(r,r, c,c+2, 'Period From : '+str(period_start.strftime(date_time_format)) , no_border)
        c= 5
        date_now = fields.datetime.strptime(str(fields.datetime.now().replace(microsecond=False,tzinfo=None)), DEFAULT_SERVER_DATETIME_FORMAT)
        date_now = fields.Datetime.context_timestamp(self.with_context(tz=tz), timestamp=date_now).replace(tzinfo=None)
        worksheet.write_merge(r,r, c,c+2, 'Report Date : '+str(date_now.strftime(date_time_format)) , no_border)

        r += 1
        c= 0
        period_to = fields.datetime.strptime(self.period_stop, DEFAULT_SERVER_DATETIME_FORMAT)
        period_to = fields.Datetime.context_timestamp(self.with_context(tz=tz), timestamp=period_to).replace(tzinfo=None)
        worksheet.write_merge(r,r, c,c+2, 'Period To : '+str(period_to.strftime(date_time_format)) , no_border)

        c= 5
        doctor = 'ALL'
        if self.doctor :
            doctor = self.doctor.name.name
        worksheet.write_merge(r,r, c,c+2, 'Doctor : '+doctor , no_border)

        r += 1
        c= 0

        worksheet.write_merge(r,r, c,c+2, 'Patient Type : '+dict(self._fields['patient_type'].selection).get(self.patient_type) , no_border)

        r += 1
        sl_no = 1
        output_header = ['Sl.No.','Visit Number','Date','Time','Patient','File No', 'Phone',   'Created by','Status','Remarks' ]

        r += 1
        c = 0
        worksheet.row(r).height = 200 * 3
        for item in output_header:
            worksheet.write(r, c, item, bold_border)
            c += 1

        col = worksheet.col(1)
        col.width = 1250 * 3
        col = worksheet.col(2)
        col.width = 1250 *4
        col = worksheet.col(3)
        col.width = 1250 * 4
        col = worksheet.col(4)
        col.width = 1250 * 7

        server_format = tools.DEFAULT_SERVER_DATETIME_FORMAT

        c = 0
        # r += 1

        sl_no = 1
        for items in doctrs:
            if appts[items] :
                c = 0
                r += 1
                doctor_name = self.env['medical.physician']. search([('id', '=', items)])
                worksheet.write_merge(r, r, 0,9, doctor_name.name.name, normal_no_border)
                for app in appts[items]:
                    r += 1
                    worksheet.write(r, c, sl_no, normal)
                    sl_no += 1
                    c += 1
                    worksheet.write(r, c, app.name, normal)
                    c += 1
                    appt_date = fields.datetime.strptime(app.appointment_sdate, "%Y-%m-%d %H:%M:%S")
                    appt_date = fields.Datetime.context_timestamp(self.with_context(tz=tz), timestamp=appt_date).replace(tzinfo=None)
                    worksheet.write(r, c, str(appt_date.strftime(date_format)), normal)
                    c += 1
                    worksheet.write(r, c, str(appt_date.strftime(time_format)), normal)
                    c += 1
                    worksheet.write(r, c, app.patient_name, normal)
                    c += 1
                    worksheet.write(r, c, app.patient.patient_id, normal)
                    c += 1
                    worksheet.write(r, c, app.patient_phone, normal)
                    c += 1
                    worksheet.write(r, c, app.create_uid.name, normal)
                    c += 1
                    state = ''
                    if app.state=='draft':
                        state = 'Booked'
                    if app.state=='confirmed':
                        state = 'Confirmed'
                    if app.state=='missed':
                        state = 'Missed'
                    if app.state=='checkin':
                        state = 'Checked In'
                    if app.state=='ready':
                        state = 'In Chair'
                    if app.state=='done':
                        state = 'Completed'
                    if app.state=='visit_closed':
                        state = 'Visit closed'
                    if app.state=='cancel':
                        state = 'cancel'

                    worksheet.write(r, c, state, normal)
                    c += 1
                    worksheet.write(r, c, '', normal)
                    c = 0
                    worksheet.row(r).height = 200 * 2

        c += 1




        buf = io.BytesIO()
        workbook.save(buf)
        out = base64.encodestring(buf.getvalue())
        self.write({'file': out, })

        return {
            'type': 'ir.actions.act_url',
            'name': 'Appointment Report',
            'url': '/web/content/doctor.appointment.report/%s/file/Appointment_Report.xls?download=true' % (self.id),}