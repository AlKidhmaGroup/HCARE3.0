# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning

class Procedure(models.Model):
    _name = 'procedure'
    _rec_name = 'code'

    def _get_default_category_id(self):
        category = False
        if self._context.get('default_appt_id'):
            department_complaints_id = self.env['medical.appointment'].browse(self._context.get('default_appt_id')).doctor.department_procedure_id
            if department_complaints_id:
                return department_complaints_id[0].id
        if not category:
            category = self.env['complaints.findings.department'].search([], limit=1)
        if category:
            return category.id
        else:
            err_msg = _('You must define at least one department in order to be able to create Complaints.')
            redir_msg = _('Go to Departments')
            dom = [('xml_id', '=', 'pragtech_dental_management.action_complaints_dr_department'),
                   ('res_model', '=', 'complaints.findings.department')]
            if self.env['ir.actions.act_window'].search(dom):
                raise RedirectWarning(err_msg,
                                      self.env.ref('pragtech_dental_management.action_complaints_dr_department').id,
                                      redir_msg)

    code = fields.Char('Name', required=True)
    description = fields.Text('Description')
    department_id = fields.Many2one('complaints.findings.department', string='Department',
                                    default=_get_default_category_id, required=True)
    detailed_description = fields.Html()

