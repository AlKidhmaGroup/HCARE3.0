from odoo import api, fields, models, SUPERUSER_ID
from datetime import date
import base64


class MedicalInvoice(models.Model):
    _inherit = "account.invoice"

    note_cashier = fields.Text('Notes')