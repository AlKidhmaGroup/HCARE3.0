# -*- coding: utf-8 -*-

from odoo import api, models


class ReportRescheduledAppt(models.AbstractModel):
    _name = 'report.calendar_scheduler.report_rescheduled'

    def get_report_data(self, data):
        s_domain = [('reschedule_count', '>', 0)]
        if data.get('appointment_sdate'):
            s_domain += [('appointment_sdate', '>=', data['appointment_sdate'])]
        if data.get('appointment_edate'):
            s_domain += [('appointment_edate', '<=', data['appointment_edate'])]
        if data.get('doctor_ids'):
            s_domain += [('doctor', 'in', data['doctor_ids'])]
        if data.get('patient_ids'):
            s_domain += [('patient', 'in', data['patient_ids'])]
        return self.env['medical.appointment'].search(s_domain)

    @api.model
    def get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        form = data.get('form', {})
        report_data = self.get_report_data(form)

        def name_get(val):
            res = val.name_get()
            return len(res) > 0 and res[0][1] or val

        def name_string(val):
            res = [i.name_get()[0][1] for i in val]
            return ", ".join(res)

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': form,
            'docs': docs,
            'appointments': report_data,
            'name_get': name_get,
            'name_string': name_string
        }
