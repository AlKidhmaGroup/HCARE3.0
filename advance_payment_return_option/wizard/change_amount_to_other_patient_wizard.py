from odoo import api, fields, models, SUPERUSER_ID,_
from odoo.exceptions import UserError

class ChangeAmountOtherPatient(models.TransientModel):
    _inherit = "change.amount.patient"

    def confirm_amount_transfer_patients(self):
        PaymentBrowse = self.env['account.payment']
        payment = PaymentBrowse.browse(self.env.context.get('active_ids'))
        if payment and payment.return_payment_ids and payment.return_payment_ids.filtered(lambda s: s.state not in ('cancelled','draft')):
            raise UserError("Once Returned Advance Payment can't transfer,Please do cancel")
        return super(ChangeAmountOtherPatient, self).confirm_amount_transfer_patients()

