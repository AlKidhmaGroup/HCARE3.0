# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MedicalHospitalOpratingRoom(models.Model):
    _name = "medical.hospital.oprating.room"

    sequence = fields.Integer(default=1)
    name = fields.Char('Name', required=True)
    extra_info = fields.Text('Extra Info')

    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner') or self.env.user.company_id.id

    company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)
