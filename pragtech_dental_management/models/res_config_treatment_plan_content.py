# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    treatment_plan_content = fields.Html(string="Treatment Plan Content")

    @api.multi
    def get_values(self):
        treatment_plan_content = self.env["ir.config_parameter"].get_param(
            "treatment_plan_content", default=None)
        return {'treatment_plan_content': treatment_plan_content or False}

    @api.multi
    def set_values(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "treatment_plan_content", record.treatment_plan_content or '')