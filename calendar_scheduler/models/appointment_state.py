# -*- coding: utf-8 -*-

from datetime import datetime, date
from ast import literal_eval

from odoo import api, fields, exceptions, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


def calculate_age(born):
    today = date.today()
    return today.year - born.year - (
            (today.month, today.day) < (born.month, born.day))


def update_appointment_color(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("select color, state "
               "from appointment_state_color")
    temp = cr.dictfetchall()
    state_color = {}
    for state in temp:
        state_color[state['state']] = state['color']

    apt_rec = env['medical.appointment'].search([])

    for i in apt_rec:
        i.write({'color': state_color[i.state]})
        # updating patient data
        if i.patient:
            if i.patient.patient_name and i.patient.mobile:
                i.update({
                    'patient_name_phone': (i.patient.patient_name + ' : ' +
                                           i.patient.mobile)
                })
        else:
            if i.patient_name and i.patient_phone:
                i.update({
                    'patient_name_phone': (i.patient_name + ' : ' +
                                           i.patient_phone)
                })
            elif i.patient_name:
                i.update({
                    'patient_name_phone': i.patient_name
                })
            else:
                i.update({
                    'patient_name_phone': i.patient_phone
                })


class AppointmentColorConfig(models.Model):
    _name = 'appointment.state.color'

    state = fields.Selection([
        ('draft', 'Booked'), ('confirmed', 'Confirmed'), ('missed', 'Missed'),
        ('checkin', 'Checked In'), ('ready', 'In Chair'),
        ('done', 'Completed'),
        ('visit_closed', 'Visit Closed'), ('cancel', 'Canceled')
    ], string="Status")
    color = fields.Char(string="Color")

class BreakType(models.Model):
    _name = 'break.type'

    name = fields.Char(string="Name")
    color = fields.Char(string="Color")


class AppointmentExtended(models.Model):
    _inherit = 'medical.appointment'

    color = fields.Char(default='rgba(115,138,230,0.59)',
                        compute='_get_color',
                        store=True)
    patient_file_no = fields.Char(
        related='patient.patient_id',
        store=True)

    insurance_icon = fields.Char()  # dummy field for icon
    has_insurance = fields.Boolean(
        related='patient.has_insurance',
        store=True, readonly=True)
    child_icon = fields.Char()  # dummy field for icon
    is_child = fields.Boolean(related='patient.is_child', readonly=True)

    cancel_icon = fields.Char()  # dummy field for icon
    urgent_icon = fields.Char()  # dummy field for icon
    follow_icon = fields.Char()  # dummy field for icon
    new_icon = fields.Char()  # dummy field for icon
    
    frequent_cancel = fields.Boolean(
        related='patient.frequent_cancel',
        store=True, readonly=True)
    # patient_phone = fields.Char(
    #     related='patient.mobile',
    #     store=True)
    # patient_name = fields.Char(
    #     related='patient.patient_name',
    #     store=True)
    patient_name_phone = fields.Char(
        compute='_get_patient_data',
        store=True)
    doctor_user = fields.Char(compute='find_is_doctor')
    
    show_new_icon = fields.Boolean(compute='_compute_urgency_icon')
    show_urgency_icon = fields.Boolean(compute='_compute_urgency_icon')
    show_followup_icon = fields.Boolean(compute='_compute_urgency_icon')

    history_line_ids = fields.One2many(
        'appointment.history', 'appointment_id',
        string="History")
    reschedule_count = fields.Integer(
        string="Reschedule count", default=0, copy=False,
        track_visibility="onchange")
    break_time = fields.Boolean(string="Is Break Time", default=False)
    break_type_id = fields.Many2one('break.type', string="Break Type")

    # @api.model
    # def create(self, vals):
    #     if ('is_registered' in vals.keys()
    #             and not vals['is_registered'] and
    #             ('sex' in vals.keys() or 'dob' in vals.keys())):
    #         # this portion is created for the appointment creation
    #         # from the scheduler, for the unregistered patients,
    #         # we will create a new patient record
    #         patient_rec = self.env['medical.patient'].create({
    #             'patient_name': vals.get('patient_name'),
    #             'mobile': vals.get('patient_phone'),
    #             'qid': vals.get('qid'),
    #             'sex': vals.get('sex'),
    #             'dob': vals.get('dob'),
    #         })
    #         vals['patient'] = patient_rec.id
    #         vals['patient_file_no'] = patient_rec.patient_id
    #     res = super(AppointmentExtended, self).create(vals)
    #     return res

    @api.depends('patient')
    @api.multi
    def find_is_doctor(self):
        if self.env.user.has_group(
                'pragtech_dental_management.group_dental_doc_menu'):
            for rec in self:
                rec.doctor_user = 'True'
        else:
            for rec in self:
                rec.doctor_user = 'False'
                
    @api.depends('patient')
    @api.multi
    def _compute_urgency_icon(self):
        for rec in self:
            conf_obj = self.env['ir.config_parameter'].sudo()
            rec.show_new_icon = conf_obj.get_param('show_new') or False
            rec.show_urgency_icon = conf_obj.get_param('show_urgency') or False
            rec.show_followup_icon = conf_obj.get_param('show_followup') or False

    @api.depends('patient')
    @api.multi
    def _get_patient_data(self):
        for appt in self:
            if appt.patient:
                if appt.patient.patient_name and appt.patient.mobile:
                    appt.update({
                        'patient_name_phone': (
                                    appt.patient.patient_name + ' : ' +
                                    appt.patient.mobile)
                    })
                elif appt.patient.patient_name:
                    appt.update({
                        'patient_name_phone': appt.patient.patient_name
                    })
                elif appt.patient.mobile:
                    appt.update({
                        'patient_name_phone': appt.patient.mobile
                    })

            else:
                if appt.patient_name and appt.patient_phone:
                    appt.update({
                        'patient_name_phone': (appt.patient_name + ' : ' +
                                               appt.patient_phone)
                    })
                elif appt.patient_name:
                    appt.update({
                        'patient_name_phone': appt.patient_name
                    })
                elif appt.patient_phone:
                    appt.update({
                        'patient_name_phone': appt.patient_phone
                    })

    @api.depends('state', 'break_time', 'break_type_id')
    @api.multi
    def _get_color(self):
        for appt in self:
            color = ''
            if appt.break_time and appt.break_type_id:
                color = appt.break_type_id.color
            elif appt.state:
                state_obj = self.env['appointment.state.color'].search(
                    [('state', '=', appt.state)], limit=1)
                if state_obj:
                    color = state_obj.color
            appt.update({
                'color': color
            })

    @api.multi
    def write(self, vals):
        if vals.get('appointment_sdate') or vals.get(
                'appointment_edate') or vals.get('patient'):
            tmp = {
                'appointment_sdate': vals.get(
                    'appointment_sdate', self.appointment_sdate) ,
                'appointment_edate': vals.get(
                    'appointment_edate', self.appointment_edate),
            }
            if not self.check_availability(tmp, None, self.id):
                raise exceptions.Warning(_(
                    "There is another appointment exists for the same time for"
                    " this patient. Please try a different time slot."))
        if self._context.get('action_origin') == 'reschedule':
            vals.update(self.update_history_info())
        res = super(AppointmentExtended, self).write(vals)
        if vals.get('appointment_sdate') and not self.check_date_validity(
                self.appointment_sdate):
            raise exceptions.Warning(_(
                "Backdated bookings are not allowed!"))
        return res

    @api.model
    def create(self, vals):
        if not self.check_availability(vals, vals.get('patient')):
            raise exceptions.Warning(_(
                "There is another appointment exists for the same time for "
                "this patient. Please try a different time slot."))
        res = super(AppointmentExtended, self).create(vals)
        if res.break_time:
            res.patient_name = res.break_type_id.name or "Break Time"
            res.is_registered = False
        if not self.check_date_validity(res.appointment_sdate):
            raise exceptions.Warning(_(
                "Backdated bookings are not allowed!"))
        return res

    def action_reschedule(self):
        """Reschedule this appointment to another date/time"""
        ctx = self._context.copy()
        ctx.update({
            'default_appointment_id': self.id,
            'default_appointment_sdate_old': self.appointment_sdate,
            'default_appointment_edate_old': self.appointment_edate,
            'default_doctor': self.doctor.id,
        })
        return {
            'name': _("Reschedule Appointment"),
            'type': 'ir.actions.act_window',
            'res_model': 'reschedule.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'context': ctx,
            'target': 'new'
        }

    def update_history_info(self):
        """gather the booking info before reschedule"""
        return {
            'reschedule_count': self.reschedule_count + 1,
            'history_line_ids': [(0, 0, {
                'appointment_sdate': self.appointment_sdate,
                'appointment_edate': self.appointment_edate,
                'doctor': self.doctor.id
            })]
        }

    def check_date_validity(self, start_date):
        """Check appointment date is past date and is allowed or not"""
        if not start_date:
            return True
        dt_val = datetime.strptime(start_date, DTF)
        is_past = dt_val.date() < datetime.today().date()
        if not is_past:
            return True
        allowed = self.env.user.has_group(
            'pragtech_dental_management.group_allow_past_booking')
        if allowed:
            return True
        return False

    @api.multi
    def check_availability(self, data, patient=None, active_id=None):
        """checking the availability of the selected slot for the customer"""
        if data.get('break_time'):
            return True
        if not literal_eval(self.env['ir.config_parameter'].sudo().get_param(
                'check_availability', default='False')):
            return True
        if not patient and self.patient:
            patient = self.patient.id
        if not patient:
            return True
        dt_from = data['appointment_sdate']
        dt_to = data['appointment_edate']
        s_domain = [('patient', '=', int(patient))]
        if active_id:
            s_domain += [('id', '!=', self.id)]
        s_domain += [
            '&',
            ('state', 'not in', ['missed', 'cancel']),
            '|',
            '|',
            '|',
            '|', ('appointment_sdate', '=', dt_from), ('appointment_edate', '=', dt_to),  # start time same or end time same
            '&', ('appointment_sdate', '<=', dt_from), ('appointment_edate', '>=', dt_to),  # booking included within selected slot or same timing
            '&', ('appointment_sdate', '<', dt_from), ('appointment_edate', '>', dt_from),  # booking starts before slot time
            '&', ('appointment_sdate', '>', dt_from), ('appointment_sdate', '<', dt_to)  # booking starts after slot time
        ]
        if self.search(s_domain):
            return False
        return True


class AppointmentHistory(models.Model):
    _name = 'appointment.history'

    appointment_id = fields.Many2one('medical.appointment')
    appointment_sdate = fields.Datetime('Appointment Start')
    appointment_edate = fields.Datetime('Appointment End')
    doctor = fields.Many2one('medical.physician', string='Doctor')


class PatientExt(models.Model):
    _inherit = 'medical.patient'

    # Note: DON'T REMOVE THESE 2 FIELDS
    insurance_icon = fields.Char()
    has_insurance = fields.Boolean(compute='compute_has_insurance',
                                   store=True)
    child_icon = fields.Char()  # dummy field for icon
    is_child = fields.Boolean(compute='compute_is_child')

    cancel_icon = fields.Char()  # dummy field for icon
    frequent_cancel = fields.Boolean(string="Appointment Frequently Cancelled")

    def compute_is_child(self):
        for rec in self.filtered(lambda p: p.dob):
            dob = datetime.strptime(rec.dob, DF)
            is_child = False
            if calculate_age(dob) < 9:
                is_child = True
            rec.is_child = is_child

    @api.depends('insurance_ids')
    def compute_has_insurance(self):
        for rec in self:
            rec.has_insurance = True if rec.insurance_ids else False

    @api.onchange('patient_name')
    def onchange_patient_name(self):
        for rec in self:
            if rec.patient_name and rec.name:
                rec.name.name = rec.patient_name
                rec.name.write({'name': rec.patient_name})

            for appt in rec.apt_id:
                new_val = ""
                if rec.patient_name and rec.mobile:
                    new_val = rec.patient_name + ":" + rec.mobile
                elif rec.patient_name:
                    new_val = rec.patient_name
                elif rec.mobile:
                    new_val = rec.mobile
                self._cr.execute(
                    'UPDATE medical_appointment '
                    'SET patient_name_phone=%s WHERE id=%s',
                    (new_val, appt.id))

    @api.onchange('mobile')
    def onchange_mobilee(self):
        for rec in self:
            if rec.mobile:
                for appt in rec.apt_id:
                    new_val = ""
                    if rec.patient_name and rec.mobile:
                        new_val = rec.patient_name + ":" + rec.mobile
                    elif rec.patient_name:
                        new_val = rec.patient_name
                    elif rec.mobile:
                        new_val = rec.mobile
                    self._cr.execute(
                        'UPDATE medical_appointment '
                        'SET patient_phone=%s, patient_name_phone=%s '
                        'WHERE id=%s',
                        (rec.mobile, new_val, appt.id))

    @api.model
    def fetch_patients(self):
        cr = self._cr
        # fetching patients
        cr.execute("SELECT rp.name, mp.id, mp.qid, rp.mobile, mp.patient_id, "
                   "mp.sex, mp.dob, mp.nationality_id, mp.is_vip,"
                   " mp.has_insurance, mp.is_child, mp.frequent_cancel "
                   "FROM medical_patient mp "
                   "JOIN res_partner rp  ON(mp.name=rp.id) "
                   "WHERE mp.name IS NOT NULL ")
        patients = cr.dictfetchall()
        return patients

    @api.model
    def search_patient_read(self, domain_here, fields_here):
        domain_new = []
        for dom_elem in domain_here:
            domain_new.append(dom_elem)
        search_patient_read = self.search_read(domain_new, fields_here, offset=0, limit=None, order=None)
        return search_patient_read


class PhysicianExtended(models.Model):
    _inherit = 'medical.physician'

    allowed_rooms = fields.Many2many(
        'medical.hospital.oprating.room', 'doctor_allowed_rooms',
        'doctor_id', 'room_id', string="Allowed Rooms")


class RoomExtended(models.Model):
    _inherit = 'medical.hospital.oprating.room'

    allowed_doctors = fields.Many2many(
        'medical.physician', 'doctor_allowed_rooms',
        'room_id', 'doctor_id', string="Allowed Doctors")
