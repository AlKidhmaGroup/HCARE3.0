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


class ComplaintsFindingsDepartment(models.Model):
    _name = 'complaints.findings.department'
    _rec_name = 'code'

    code = fields.Char('Name', required=True)
    description = fields.Text('Description')