# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval


class IrAttachment(models.Model):
    """
    Form for Attachment details
    """
    _inherit = "ir.attachment"
    _name = "ir.attachment"

    patient_id = fields.Many2one('medical.patient', 'Patient')
    appointment_id = fields.Many2one('medical.appointment', 'Appointment')

    @api.model
    def create(self, values):
        if (values.get('res_model') == 'medical.appointment' and
                not values.get('appointment_id')):
            values.update(self.update_appointment_info(values.get("res_id")))
        elif (values.get('res_model') == 'medical.patient' and
                not values.get('patient_id')):
            values.update(patient_id=values.get("res_id"))

        line = super(IrAttachment, self).create(values)
        msg = "<b> Created New Attachment:</b><ul>"
        if values.get('name'):
            msg += "<li>" + _("Name") + ": %s<br/>" % (line.name)
        msg += "</ul>"
        line.appointment_id.message_post(body=msg)
        return line

    @api.multi
    def write(self, values):
        appoints = self.mapped('appointment_id')
        for apps in appoints:
            order_lines = self.filtered(lambda x: x.appointment_id == apps)
            for line in order_lines:
                msg = "<b> Updated Attachment : </b><ul>"
                if values.get('name'):
                    msg += "<li>" + _("Name") + ": %s -> %s <br/>" % (line.name, values['name'],)
                if not values.get('name'):
                    msg = "<b> Updated File Content of Attachment : %s </b><ul>" % (line.name,)
                msg += "</ul>"
            apps.message_post(body=msg)
        result = super(IrAttachment, self).write(values)
        return result

    @api.multi
    def unlink(self):
        for rec in self:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            restrict_completion_treatment_plan = literal_eval(ICPSudo.get_param('restrict_completion_treatment_plan', default='False'))
            if rec.res_model in ['medical.appointment', 'medical.patient'] and \
                    not self.env.user.has_group('pragtech_dental_management.group_access_delete_attachments') \
                    and not restrict_completion_treatment_plan:
                raise ValidationError(_('You cannot delete Attachments.'))
            msg = "<b> Deleted Attachment with Values:</b><ul>"
            if rec.name:
                msg += "<li>" + _("Name") + ": %s <br/>" % (rec.name,)
            msg += "</ul>"
            rec.appointment_id.message_post(body=msg)
        return super(IrAttachment, self).unlink()

    def update_appointment_info(self, appointment_id):
        if not appointment_id:
            return {}
        appt = self.env['medical.appointment'].sudo().browse(appointment_id)
        return {
            'appointment_id': appointment_id,
            'patient_id': appt.patient and appt.patient.id
        }
