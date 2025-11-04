# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from mock import DEFAULT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import hashlib
import time
from odoo.exceptions import Warning
import json
from odoo.exceptions import RedirectWarning


class Complaints(models.Model):
    _name = 'complaints'
    _rec_name = 'code'

    def _get_default_category_id(self):
        category = False
        if self._context.get('default_appt_id'):
            department_complaints_id = self.env['medical.appointment'].browse(self._context.get('default_appt_id')).doctor.department_complaints_id
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

    # @api.multi
    # @api.depends('code', 'description')
    # def name_get(self):
    #     result = []
    #     for rcd in self:
    #         name = rcd.code or ''
    #         if rcd.description:
    #             name += '' + rcd.description
    #         result.append((rcd.id, name))
    #     return result
    #
    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = [('description', operator, name)]
    #     pos = self.search(domain + args, limit=limit)
    #     return pos.name_get()
