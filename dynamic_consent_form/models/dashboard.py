from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import time

class ConsentDashboard(models.Model):
    _name = "consent.dashboard"
