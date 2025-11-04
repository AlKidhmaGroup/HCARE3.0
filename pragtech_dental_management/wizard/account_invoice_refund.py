# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountInvoiceRefund(models.TransientModel):
    """Credit Notes"""

    _inherit = "account.invoice.refund"
    _description = "Credit Note"

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            if inv.number:
                return 'Credit note of ' + inv.number
            return inv.name
        return ''

    description = fields.Char(string='Reason', required=True, default=_get_reason)