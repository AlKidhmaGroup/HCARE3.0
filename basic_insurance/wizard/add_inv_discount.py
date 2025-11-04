from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from ast import literal_eval


class AddDiscountWizard(models.TransientModel):
    _inherit = 'add.discount'

    @api.multi
    def action_move_lines_create(self, invoice_id):
        for inv in invoice_id:
            if inv.insurance_invoice:
                if not inv.journal_id.sequence_id:
                    raise UserError(_('Please define sequence on the journal related to this invoice.'))
                if not inv.invoice_line_ids:
                    raise UserError(_('Please create some invoice lines.'))
                # if inv.move_id:
                #     continue

                ctx = dict(self._context, lang=inv.partner_id.lang)

                # if not inv.date_invoice:
                #     inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
                # if not inv.date_due:
                #     inv.with_context(ctx).write({'date_due': inv.date_invoice})
                company_currency = inv.company_id.currency_id

                # create move lines (one per invoice line + eventual taxes and analytic lines)
                iml = inv.invoice_line_move_line_get()
                if inv.consult_approved_amt and not inv.share_based_on:
                    for lines in iml:
                        product_id = self.env['product.product'].browse(lines['product_id'])
                        consultation_companies = [ins_company.id for ins_company in
                                                  product_id.consultation_insurance_company_ids]
                        if inv.insurance_company.id == inv.insurance_card.company_id.id and \
                                        inv.insurance_company.id in consultation_companies:
                            lines['price_unit'] = inv.consult_approved_amt
                            lines['price'] = inv.consult_approved_amt

                iml += inv.tax_line_move_line_get()
                # change
                # if inv.is_insurance_company:
                #     iml.clear()
                diff_currency = inv.currency_id != company_currency
                # create one move line for the total and possibly adjust the other lines amount
                total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

                name = inv.name or '/'
                disc_amount_final = 0.0
                total_disc_amount_final = total
                inv_bill_cred = ('out_invoice', 'in_refund')
                bill_inv_credit = ('in_invoice', 'out_refund')
                if inv.is_patient and inv.share_based_on == 'Global':
                    for line in inv.invoice_line_ids:
                        sale_account_id = line.account_id
                    if sale_account_id:
                        Insurance_treatment_dict = {
                            'type': 'dest',
                            'name': 'After Treatment Group Discount',
                            'price': -inv.after_treatment_grp_disc,
                            'account_id': sale_account_id.id,
                            'cost_center_id': inv.cost_center_id.id,
                            'company_id': inv.company_id.id,
                            'date_maturity': inv.date_due,
                            'amount_currency': diff_currency and total_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        }
                        iml.append(Insurance_treatment_dict)
                if inv.discount_fixed_percent:
                    if inv.discount_fixed_percent == 'Percent':
                        self_amount_total = inv.amount_untaxed + inv.amount_tax
                        disc_amount_final = self_amount_total * (inv.discount / 100.0)
                    if inv.discount_fixed_percent == 'Fixed':
                        disc_amount_final = inv.discount_value
                    default_discount_account = inv.company_id.default_discount_account.id
                    if not default_discount_account:
                        raise UserError(_('Please define Discount Account in Company Configuration.'))
                    company_currency = inv.company_id.currency_id
                    diff_currency = inv.currency_id != company_currency
                    if inv.type in inv_bill_cred:
                        type_here = 'dest'
                        total_disc_amount_final = total - disc_amount_final
                    if inv.type in bill_inv_credit:
                        type_here = 'src'
                        total_disc_amount_final = total + disc_amount_final
                        disc_amount_final = -disc_amount_final
                    iml.append({
                        'type': type_here,
                        'name': 'GLOBAL DISCOUNT',
                        'price': disc_amount_final,
                        'account_id': default_discount_account,
                        'date_maturity': inv.date_due,
                        'amount_currency': diff_currency and total_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id,
                        'partner_id': inv.partner_id.id,
                    })
                if inv.payment_term_id:
                    totlines = \
                        inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total,
                                                                                                                    inv.date_invoice)[
                            0]
                    res_amount_currency = total_currency
                    ctx['date'] = inv.date or inv.date_invoice
                    for i, t in enumerate(totlines):
                        if inv.currency_id != company_currency:
                            amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                        else:
                            amount_currency = False

                        # last line: add the diff
                        res_amount_currency -= amount_currency or 0
                        if i + 1 == len(totlines):
                            amount_currency += res_amount_currency
                        iml.append({
                            'type': 'dest',
                            'name': name,
                            'price': t[1],
                            'account_id': inv.account_id.id,
                            'date_maturity': t[0],
                            'amount_currency': diff_currency and amount_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        })
                else:
                    default_insurance_diff_account = inv.company_id.default_insurance_diff_account.id
                    if not default_insurance_diff_account:
                        raise UserError(_('Please define Insurance Difference Account in Company Configuration.'))
                    if inv.is_patient:
                        total_disc_amount_final -= inv.insurance_total
                        if inv.insurance_total:
                            Insurance_line_dict = {
                                'type': 'src',
                                'name': 'Insurance Difference',
                                'price': inv.insurance_total,
                                'account_id': default_insurance_diff_account,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            }
                            iml.append(Insurance_line_dict)
                    if inv.is_insurance_company:
                        patient_invoice = self.search([('insurance_invoice', '=', inv.id)], limit=1)
                        total_disc_amount_final += patient_invoice.insurance_total
                        if patient_invoice.insurance_total:
                            Insurance_line_dict = {
                                'type': 'src',
                                'name': 'Insurance Difference',
                                'price': -patient_invoice.insurance_total,
                                'account_id': default_insurance_diff_account,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            }
                            iml.append(Insurance_line_dict)
                    if inv.type in inv_bill_cred:
                        type_here = 'dest'
                        inv_amount_total = inv.amount_total
                    if inv.type in bill_inv_credit:
                        type_here = 'src'
                        inv_amount_total = -inv.amount_total
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': inv_amount_total,
                        'account_id': inv.account_id.id,
                        'date_maturity': inv.date_due,
                        'amount_currency': diff_currency and total_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
                part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
                line = [(0, 0, inv.line_get_convert(l, part.id)) for l in iml]
                line = inv.group_lines(iml, line)
                journal = inv.journal_id.with_context(ctx)
                line = inv.finalize_invoice_move_lines(line)
                date = inv.date or inv.date_invoice
            else:
                if not inv.journal_id.sequence_id:
                    raise UserError(_('Please define sequence on the journal related to this invoice.'))
                if not inv.invoice_line_ids:
                    raise UserError(_('Please create some invoice lines.'))
                ctx = dict(self._context, lang=inv.partner_id.lang)
                # if not inv.date_invoice:
                #     inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
                # if not inv.date_due:
                #     inv.with_context(ctx).write({'date_due': inv.date_invoice})
                company_currency = inv.company_id.currency_id
                # create move lines (one per invoice line + eventual taxes and analytic lines)
                iml = inv.invoice_line_move_line_get()
                iml += inv.tax_line_move_line_get()

                diff_currency = inv.currency_id != company_currency
                # create one move line for the total and possibly adjust the other lines amount
                total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

                name = inv.name or '/'
                disc_amount_final = 0.0
                if inv.discount_fixed_percent:
                    if inv.discount_fixed_percent == 'Percent':
                        self_amount_total = inv.amount_untaxed + inv.amount_tax
                        disc_amount_final = self_amount_total * (inv.discount / 100.0)
                    if inv.discount_fixed_percent == 'Fixed':
                        disc_amount_final = inv.discount_value
                    default_discount_account = inv.company_id.default_discount_account.id
                    if not default_discount_account:
                        raise UserError(_('Please define Discount Account in Company Configuration.'))
                    company_currency = inv.company_id.currency_id
                    diff_currency = inv.currency_id != company_currency
                    iml.append({
                        'type': 'dest',
                        'name': 'GLOBAL DISCOUNT',
                        'price': disc_amount_final,
                        'account_id': default_discount_account,
                        'date_maturity': inv.date_due,
                        'amount_currency': diff_currency and total_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id,
                        'partner_id': inv.partner_id.id,
                    })
                if inv.payment_term_id:
                    totlines = \
                        inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total,
                                                                                                                    inv.date_invoice)[
                            0]
                    res_amount_currency = total_currency
                    ctx['date'] = inv.date or inv.date_invoice
                    for i, t in enumerate(totlines):
                        if inv.currency_id != company_currency:
                            amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                        else:
                            amount_currency = False

                        # last line: add the diff
                        res_amount_currency -= amount_currency or 0
                        if i + 1 == len(totlines):
                            amount_currency += res_amount_currency

                        iml.append({
                            'type': 'dest',
                            'name': name,
                            'price': t[1],
                            'account_id': inv.account_id.id,
                            'date_maturity': t[0],
                            'amount_currency': diff_currency and amount_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        })
                else:
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': total - disc_amount_final,
                        'account_id': inv.account_id.id,
                        'date_maturity': inv.date_due,
                        'amount_currency': diff_currency and total_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
                part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
                line = [(0, 0, inv.line_get_convert(l, part.id)) for l in iml]
                line = inv.group_lines(iml, line)
                journal = inv.journal_id.with_context(ctx)
                line = inv.finalize_invoice_move_lines(line)
                date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                # 'date': date,
                'narration': inv.comment,
            }
            invoice_id.move_id.write(move_vals)
            # ctx['company_id'] = inv.company_id.id
            # ctx['invoice'] = inv
            # ctx_nolang = ctx.copy()
            # ctx_nolang.pop('lang', None)
            # move = account_move.with_context(ctx_nolang).create(move_vals)
            invoice_id.move_id.post()
            for payment in invoice_id.payment_ids:
                debit_line_a = payment.move_line_ids.filtered(lambda l: l.credit)
                invoice_id.assign_outstanding_credit(debit_line_a.id)

            # make the invoice point to that move
            vals = {
                # 'move_id': move.id,
                # 'date': date,
                'move_name': invoice_id.move_id.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.multi
    def action_confirm(self):
        wizard_vals = self.read()[0]
        if wizard_vals['invoice_id']:
            invoice_id = self.env['account.invoice'].browse(wizard_vals['invoice_id'][0])
            if self.discount_after_validation < 0:
                raise UserError(_("Discount amount should not be -ve"))
            if self.discount_after_validation > invoice_id.residual:
                raise UserError(_("Discount amount should not be greater than Due amount"))
            residual = invoice_id.residual
            if invoice_id.discount_fixed_percent == 'Percent':
                raise UserError(_("Already discount defined in Percentage for this invoice"))
            elif invoice_id.discount_fixed_percent == 'Fixed':
                new_discount =  self.discount_after_validation
                # new_discount =  invoice_id.discount_value +self.discount_after_validation
                invoice_id.write({'discount_fixed_percent': 'Fixed', 'discount_value': new_discount})
            else:
                invoice_id.write({'discount_fixed_percent': 'Fixed', 'discount_value': self.discount_after_validation})
            invoice_id.move_id.button_cancel()
            for m_lines in invoice_id.move_id.line_ids:
                if self.env['account.partial.reconcile'].search([('debit_move_id', '=', m_lines.id)]):
                    self.env['account.partial.reconcile'].search([('debit_move_id', '=', m_lines.id)]).unlink()
            invoice_id.move_id.line_ids.unlink()
            self.action_move_lines_create(invoice_id)
            if residual == self.discount_after_validation:
                invoice_id.write({'state': 'paid'})