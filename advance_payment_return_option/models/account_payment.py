# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    advance_return = fields.Boolean('Is Advance Return Payment?')
    return_payment_id = fields.Many2one('account.payment','Advance Return From')
    return_payment_ids = fields.One2many('account.payment','return_payment_id',string='Return Payment')
    amount_complete = fields.Boolean(compute="get_amount_complete",store=True,string='Done')
    
    @api.depends('return_payment_ids','return_payment_ids.state','invoice_ids','invoice_ids.state','state')
    def get_amount_complete(self):
        for rec in self:
            rec.amount_complete = False
            if rec.advance and rec.payment_type == 'inbound':
                amount = sum([payment.amount for payment in rec.return_payment_ids if payment.state not in ('draft','cancelled')])
                amount += sum([(invoice.amount_total-invoice.residual) for invoice in rec.invoice_ids if invoice.state=='paid'])
                rec.amount_complete = True
                if not float_compare(rec.amount, amount, precision_digits=2):
                    rec.amount_complete = False
    
    @api.multi
    def cancel(self):
        for rec in self:
            if rec.advance and rec.return_payment_ids:
                for payment in rec.return_payment_ids:
                    payment_entries = self.env['account.move.line'].search(['|',('payment_id','=',rec.id),
                                                     ('payment_id','=',payment.id),
                                                     ('account_id','=',payment.partner_id.property_account_receivable_id and payment.partner_id.property_account_receivable_id.id or False)])
                    payment_entries.remove_move_reconcile()
                    payment.cancel()
            return super(AccountPayment, self).cancel()
        
    @api.multi
    def action_draft(self): 
        for rec in self:
            res = super(AccountPayment, self).action_draft() 
            if rec.advance:
                rec.advance_return = False
            return res
        
    @api.multi    
    def view_advance_patient(self):
        for rec in self:
            if rec.partner_id:
                patient_id = self.env['medical.patient'].search([('name','=',rec.partner_id.id)])
                if patient_id:
                    action_id = self.env.ref('pragtech_dental_management.medical_patient_action_tree').read()[0]
                    action_id['views'] = [(self.env.ref('pragtech_dental_management.medical_patient_view').id, 'form')]
                    action_id['res_id'] = patient_id.id
                    return action_id 
                raise ValidationError('Patient Not Found,Please check')

class MedicalPatient(models.Model):
    _inherit = "medical.patient"
    
    @api.multi
    def show_advance(self):
        for rec in self:
            if rec.name:
                action_id = self.env.ref('advance_payment_option.action_advance_payments').read()[0]
                action_id['domain'] = [('partner_id', '=', rec.name.id),('advance','=',1), ('partner_type', '=', 'customer')]
                action_id['target'] = 'current'
                action_id['context'] = {'create':0,'edit':0,'delete':0}
                return action_id
        pass
    
class MedicalAppointment(models.Model):
    _inherit = "medical.appointment"
    
      
    @api.multi
    def show_advance(self):
        for rec in self:
            if rec.patient and rec.patient.name:
                action_id = self.env.ref('advance_payment_option.action_advance_payments').read()[0]
                action_id['domain'] = [('partner_id', '=', rec.patient.name.id),('advance','=',1), ('partner_type', '=', 'customer')]
                action_id['target'] = 'current'
                action_id['context'] = {'create':0,'edit':0,'delete':0}
                return action_id
        pass
