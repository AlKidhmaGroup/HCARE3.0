# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from odoo import fields, models, api
from odoo.osv import expression


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_journal = fields.Boolean('Use in Invoice Payment')

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     extra_domain = []
    #     if self._context.get('journal_type') == 'sale':
    #         extra_domain = [('invoice_journal', '=', True)]
    #     args = expression.AND([args and args or [], extra_domain])
    #     return super(AccountJournal, self).search(
    #         args=args, offset=offset, limit=limit, order=order, count=count)
