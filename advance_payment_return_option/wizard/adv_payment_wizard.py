from odoo import api, fields, models, SUPERUSER_ID
import base64
from odoo.exceptions import Warning
from datetime import datetime


class ReportAdvPayment(models.AbstractModel):
    _inherit = 'report.advance_payment_option.advance_payment_report_pdf'

    @api.model
    def get_adv_payment_details(self, period_start=False, period_stop=False, patient_id=False, patient=False,
                                doctor=False, company_id=False):
        dom = [
            ('partner_type', '=', 'customer'),
            ('advance', '=', True),
            ('state', 'in', ('posted', 'reconciled')),
            ('company_id', '=', company_id[0]),
        ]
        if period_start:
            dom.append(('payment_date', '>=', period_start))
        if period_stop:
            dom.append(('payment_date', '<=', period_stop))
        if patient:
            dom.append(('partner_id', '=', patient_id))
        if doctor:
            dom.append(('doctor_id', '=', doctor[0]))
        payment_records = self.env['account.payment'].search(dom)
        order_list = []
        cash_count = 0
        card_count = 0
        for payment in payment_records:
            doctor = ''
            if payment.doctor_id:
                doctor = payment.doctor_id.name.name
            pay_mode = False
            cash = 0
            credit = 0
            journal_obj = self.env['account.journal']
            cash_journals = journal_obj.search([('type', '=', 'cash')]).ids
            bank_journals = journal_obj.search([('type', '=', 'bank')]).ids
            domain = [('account_id', '=', payment.partner_id.property_account_receivable_id.id),
                      ('partner_id', '=', payment.partner_id.id),
                      ('move_id.state', '=', 'posted'),
                      ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                      ('amount_residual_currency', '!=', 0.0),
                      ('credit', '>', 0), ('debit', '=', 0)]
            amount_to_show = 0
            lines = self.env['account.move.line'].search(domain)
            
            for line in lines:
                to_show = line.company_id.currency_id.with_context(date=line.date).compute(
                    abs(line.amount_residual), self.env.user.company_id.currency_id)
                amount_to_show += to_show

            if payment.journal_id.id in cash_journals:
                cash += payment.amount
                cash_count += 1
                pay_mode = 'cash'
            if payment.journal_id.id in bank_journals:
                credit += payment.amount
                card_count += 1
                pay_mode = 'card'
            order_data = {}
            if payment.payment_type == 'inbound':
                order_data = {
                    'name': payment.name,
                    'journal_id': payment.journal_id.name,
                    'payment_date': payment.payment_date,
                    'patient': payment.partner_id.name,
                    'type': 'out_invoice',
                    'doctor': doctor,
                    'cash': cash,
                    'credit': credit,
                    'pay_mode': pay_mode,
                    'amount': payment.amount - amount_to_show,
                    'amount_residual': amount_to_show,
                }
            else:
                if cash:
                    cash = -cash
                if credit:
                    credit = -credit
                order_data = {
                    'name': payment.name,
                    'journal_id': payment.journal_id.name,
                    'payment_date': payment.payment_date,
                    'patient': payment.partner_id.name,
                    'type': 'out_refund',
                    'doctor': doctor,
                    'cash': cash,
                    'credit': credit,
                    'pay_mode': pay_mode,
                    'amount': -1*payment.amount if payment.advance_return else (-payment.amount - amount_to_show),
                    'amount_residual': 0.00 if payment.advance_return else amount_to_show,
                }
            if order_data:
                order_list.append(order_data)
        return {
            'orders': sorted(order_list, key=lambda l: l['name']),
            'period_start': period_start,
            'period_stop': period_stop,
            'payment_mode': False,
            'cash': cash_count,
            'card': card_count,
        }

