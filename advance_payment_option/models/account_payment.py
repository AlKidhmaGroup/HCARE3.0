# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_doctor_id(self):
        company_id = self.company_id or self.env.user.company_id
        doc_ids = [x.id for x in self.env['medical.physician'].search([('company_id', '=', company_id.id)])]
        domain = [('id', 'in', doc_ids)]
        return domain

    # company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id.id,
    #                              required=True)
    advance = fields.Boolean('Is Advance Payment?')
    doctor_id = fields.Many2one('medical.physician', 'Doctor', domain=_get_doctor_id)
    treatment_ids = fields.Many2many('product.product', string='Treatments', domain=[('is_treatment', '=', True)])
    patient_name = fields.Char(string="Patient" )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            patient_id = self.env['medical.patient'].search([('name', '=', self.partner_id.id)])
            if patient_id:
                self.patient_name = patient_id[0].display_name
            else:
                self.patient_name = self.partner_id.display_name

    @api.multi
    def _cron_patient_names(self):
        for record in self.env['account.payment'].search([]) :
            if record.partner_id:
                patient_id = self.env['medical.patient'].search([('name','=',record.partner_id.id)])
                if patient_id:
                    record.write({'patient_name' :patient_id[0].display_name})
                else:
                    record.write({'patient_name':record.partner_id.display_name})

    # @api.onchange('company_id','doctor_id')
    # def onchange_compny(self):
    #     if self.company_id:
    #         domain = self._get_doctor_id()
    #         return {
    #             'domain': {'doctor_id': domain}
    #         }

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            id_to_remove = rec.invoice_ids.filtered(lambda r: r.state == 'cancel').ids
            for remove_cancel in id_to_remove:
                self.write({
                    'invoice_ids': [(3, remove_cancel, False)],
                })
            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            is_advance = 0
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        if rec.advance:
                            is_advance = 1
                            sequence_code = 'account.payment.advance.receipt'
                        else:
                            sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        if rec.advance:
                            is_advance = 1
                            sequence_code = 'account.payment.advance.payment'
                        else:
                            sequence_code = 'account.payment.supplier.invoice'
            if is_advance:
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code)
            else:
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
            if not rec.name and rec.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
