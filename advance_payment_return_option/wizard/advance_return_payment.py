from odoo import api, fields, models, SUPERUSER_ID,_
import base64
from odoo.exceptions import Warning
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

class ReturnPaymentPatient(models.TransientModel):
    _name = "return.payment.patient"
    _description = "Advance Payment Return"
    
    @api.model
    def default_get(self, fields):
        res = super(ReturnPaymentPatient, self).default_get(fields)
        payment = self.env['account.payment'].browse(self.env.context.get('active_id',False))
        if payment:
            res.update({'patient_id':payment.partner_id and payment.partner_id.id or False,
                        'journal_id':payment.journal_id and payment.journal_id.id or False})
        return res
    
    patient_id = fields.Many2one('res.partner', "Patient")
    amount = fields.Float('Amount', required=True)
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal',"Journal")
    
    @api.multi
    def confirm_advance_payment_return(self):
        for rec in self:
            payment = self.env['account.payment'].browse(self.env.context.get('active_id',False))
            if payment:
                query = """SELECT COALESCE(sum(ap.amount), 0.00) as amounts
                            from account_payment ap
                            where ap.return_payment_id =%s and ap.state='posted'"""%(payment.id)
                self.env.cr.execute(query)
                data = self.env.cr.dictfetchall()
                amount = sum([parent_payment['amounts'] for parent_payment in data])
                amount += sum([(invoice.amount_total-invoice.residual) for invoice in payment.invoice_ids if invoice.state=='paid'])
                if amount+ rec.amount > payment.amount:
                    raise UserError("Returning Amount Should be equal to Advance Payment,May be Returned before")
                return_payment = payment.copy({'communication': 'Retrun '+payment.name, 'payment_type': 'outbound','amount':rec.amount,
                                               'return_payment_id':payment.id,'advance_return':True,'journal_id':rec.journal_id and rec.journal_id.id or False,
                                               'payment_date':rec.date})
                return_payment.post()
                payment_entries = self.env['account.move.line'].search(['|',('payment_id','=',return_payment.id),
                                                     ('payment_id','=',payment.id),
                                                     ('account_id','=',payment.partner_id.property_account_receivable_id and payment.partner_id.property_account_receivable_id.id or False)])
                payment_entries.reconcile()
                if not float_compare(amount + rec.amount, payment.amount, precision_digits=2):
                    payment.advance_return = True
