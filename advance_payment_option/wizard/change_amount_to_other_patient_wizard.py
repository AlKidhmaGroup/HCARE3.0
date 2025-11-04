from odoo import api, fields, models, SUPERUSER_ID,_
import base64
from odoo.exceptions import Warning
from datetime import datetime
from odoo.exceptions import UserError

class ChangeAmountOtherPatient(models.TransientModel):
    _name = "change.amount.patient"

    patient_id = fields.Many2one('res.partner', "Patient", domain=[('is_patient', '=', True)], required=True)
    amount = fields.Float('Amount', required=True)
    date = fields.Date('Date', required=True, default=fields.Date.context_today)

    def confirm_amount_transfer_patients(self):
        PaymentBrowse = self.env['account.payment']
        payment = PaymentBrowse.browse(self.env.context.get('active_ids'))
        med_patient = self.env['medical.patient'].search([('patient_id', '=', payment.partner_id.patient_id)])
        total_payment_amt = payment.amount
        used_payment_amt = payment.adv_pay_amount
        remaining_payment_amt = total_payment_amt - used_payment_amt
        if med_patient:
            if 0 < self.amount <= remaining_payment_amt:
                updated_total_payment_amt = payment.amount - self.amount
                if any(len(record.invoice_ids) > 1 for record in payment):
                    # For multiple invoices, there is account.register.payments wizard
                    raise UserError(_("This method should only be called to process a single invoice's payment"))
                journal = payment.journal_id
                if not journal.update_posted:
                    journal.write({'update_posted': True})
                payment.cancel()
                payment.action_draft()
                msg = "<b> Updated Payment %s: Transferred payment to %s </b><ul>" % (payment.name, self.patient_id.name)
                msg += "<li>" + _("Amount") + ": %s -> %s <br/>" % (payment.amount, payment.amount - self.amount)
                msg += "</ul>"
                if len(payment.invoice_ids) == 1:
                    payment.invoice_ids.message_post(body=msg)
                payment.message_post(body=msg)
                payment.write({'amount': updated_total_payment_amt})
                # payment.action_validate_invoice_payment()
                payment.post()

                patient_id = self.env['medical.patient'].search([('name', '=', self.patient_id.id)])
                if patient_id:
                    patient_name = patient_id[0].display_name
                else:
                    patient_name = self.patient_id.display_name
                new_payment_val  = {
                    'partner_id':self.patient_id.id,
                    'patient_name': patient_name,
                    'journal_id':payment.journal_id.id,
                    'amount':self.amount,
                    'doctor_id':payment.doctor_id and payment.doctor_id.id or False,
                    'payment_type':'inbound',
                    'payment_method_id':payment.payment_method_id.id,
                    'state':'draft',
                    'partner_type':'customer' if self.patient_id.customer else 'supplier',
                    'advance':True,
                    'communication':'Transfer from {} and sequence is {}'.format(payment.partner_id.name,
                                                                                 payment.name),
                    'payment_date':self.date
                            }
                new_patient_adv = PaymentBrowse.create(new_payment_val)
                # new_patient_adv.action_validate_invoice_payment()
                new_patient_adv.post()
            else:
                raise UserError(_('Please Enter Amount Between 1 and {}').format(remaining_payment_amt))

