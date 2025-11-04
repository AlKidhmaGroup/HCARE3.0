# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class RescheduleWizard(models.TransientModel):
    _name = 'reschedule.wizard'

    appointment_id = fields.Many2one('medical.appointment')
    appointment_sdate_old = fields.Datetime('Appointment Start')
    appointment_edate_old = fields.Datetime('Appointment End')

    appointment_sdate = fields.Datetime('Appointment Start')
    appointment_edate = fields.Datetime('Appointment End')

    doctor = fields.Many2one('medical.physician', string='Doctor')
    doctor_ids = fields.Many2many('medical.physician', string='Doctor')
    patient_ids = fields.Many2many('medical.patient', string='Patient')

    # @api.onchange('appointment_sdate', 'appointment_edate')

    def do_reschedule(self):
        self.onchange_date_vals()
        ctx = self._context.copy()
        ctx.update(action_origin='reschedule')
        self.appointment_id.with_context(ctx).write({
            'appointment_sdate': self.appointment_sdate,
            'appointment_edate': self.appointment_edate,
        })

    @api.multi
    def print_report(self):
        wiz_data = self.read()[0]
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': wiz_data
        }
        return self.env.ref(
            'calendar_scheduler.report_rescheduled_appointments'
        ).report_action(self, data=data)

    def onchange_date_vals(self):
        for rec in self:
            if rec.appointment_sdate >= rec.appointment_edate:
                rec.appointment_sdate = False
                rec.appointment_edate = False
                return {
                    'warning': {
                        'title': _("Invalid Date Input"),
                        'message': _("Please select a proper date input"),
                    }
                }

