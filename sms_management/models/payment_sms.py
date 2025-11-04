from odoo import fields, models, api, _,SUPERUSER_ID
import requests
import pytz
from odoo.exceptions import Warning as UserError

class Payment(models.Model):
    _inherit = 'account.payment'

    is_sms_send = fields.Boolean(string="SMS Send",  )



class InvoiceInherit(models.Model):
    _inherit = 'account.invoice'

    payment_sms_pending = fields.Boolean(string="Payment SMS pending", compute='payment_sms_pending_compute' )

    @api.depends('payment_ids')
    def payment_sms_pending_compute(self):
        payment_sms = self.env['ir.config_parameter'].sudo().get_param('send_payment_sms') or False
        # print payment_sms
        if payment_sms :
            if self.payment_ids:
                for payment in self.payment_ids:
                    if payment.is_sms_send == False :
                        self.payment_sms_pending = True
            else:
                self.payment_sms_pending = False
        else:
            self.payment_sms_pending = False

def send_payment_sms(self):

        payment_list = self.payment_ids.search([('is_sms_send', '!=',True)])
        payment_template = self.env.ref('sms_management.payment_template')


        gateway_obj = self.env['gateway.setup'].search([], limit=1)
        if gateway_obj:
            url = eval(gateway_obj.gateway_url)
            params = eval(gateway_obj.parameter)
            track_obj = self.env['sms.track']
            amount_paid = 0
            for payment in payment_list:
                payment.is_sms_send = True
                amount_paid += payment.amount

            user = self.env['res.users'].browse(SUPERUSER_ID)
            tz = pytz.timezone(user.partner_id.tz) or pytz.utc



            mobile = self.patient.mobile
            patient_name = self.patient.patient_name

            patient_name = patient_name.upper()
            message = payment_template.message
            message = message.replace('{patient}', patient_name).replace('{bill}', self.name)\
                .replace('{amount}', amount_paid)\
                .replace('{due}', self.residual)

            if len(mobile) == 8 or (len(mobile) == 11 and mobile[:3] == '974') and mobile.isdigit():
                if len(mobile) == 8:
                    mobile = '974' + mobile
                mobile = str(mobile)
                if gateway_obj.name == 'vodafone':
                    params['content'] = message
                    params['destination'] = mobile
                elif gateway_obj.name == 'smscountry':
                    params['message'] = message
                    params['mobilenumber'] = mobile
                elif gateway_obj.name == 'vodafoneapi':
                    params['sms'] = message
                    params['to'] = mobile
                else:
                    params['smsText'] = message
                    params['recipientPhone'] = mobile
                response = requests.get(url, params=params)
                status_code = response.status_code
                value = {
                    'model_id': 'account.invoice',
                    'res_id': self.id,
                    'mobile': mobile,
                    'message': message,
                    'response': status_code,
                    'gateway_id': gateway_obj.id,
                }
                track_obj.create(value)
            else:
                raise UserError("No mobile number found!!!")
        else:
            raise UserError("Please setup Gateway properly!!!")





