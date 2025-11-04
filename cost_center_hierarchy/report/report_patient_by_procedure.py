# -*- coding: utf-8 -*-

from odoo import api, models, _


class ReportPatientByProcedure(models.AbstractModel):
    _inherit = 'report.pragtech_dental_management.report_patient_by_procedure'

    def fetch_invoice_domain(self, form):
        s_domain = super(ReportPatientByProcedure, self).fetch_invoice_domain(form)
        if 'department_ids' in form:
            cr = self._cr
            cr.execute("select id from medical_physician where department_id in "
                       "%s ", (tuple(form['department_ids']),))
            doctor_ids = [i[0] for i in cr.fetchall()]
            if doctor_ids:
                s_domain += [('dentist', 'in', doctor_ids)]
        return s_domain
