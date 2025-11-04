# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PolicyHolder(models.Model):
    _name = "policy.holder"

    name = fields.Char(required=True)
    policy_no = fields.Char('Policy No',required=True)
