# -*- coding: utf-8 -*-

import pytz
import datetime
from ast import literal_eval
from odoo import api, exceptions, fields, models


class ViewExtended(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('scheduler', "Scheduler")])


class ActWindowViewExtended(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[('scheduler', "Scheduler")])


class CalenderSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    schedule_start = fields.Char(string="Schedule start", default='06:00')
    schedule_end = fields.Char(string="Schedule end", default='17:00')
    hide_room_from_calendar_column = fields.Boolean('Hide Room from Calendar column')
    show_time_in_calendar_scheduler = fields.Boolean('Show time in Calendar Scheduler')

    # phone number validation
    validate_phone = fields.Boolean(
        string="Require minimum length for phone number search")
    phone_min_length = fields.Integer(string="Minimum length", default=8)

    phone_max_length = fields.Integer(string="Maximum length", default=8)
    show_country_code = fields.Boolean(string="Show country code", default=True)

    resource_order = fields.Selection([
        ('sequence', 'Sequence'), ('name', 'Name')], string="Resource Order",
        help="How the resource columns in scheduler should be ordered.",
        default='sequence')
    hide_department = fields.Boolean(
        string="Hide Department",
        help="Hide department details in scheduler.")
    check_availability = fields.Boolean(
        string="Restrict multiple appointments in same slot for patients",
        help="Restrict multiple appointments in same slot for a patient.")
    show_cancelled = fields.Boolean(
        string="Show cancelled & missed bookings", default=True)
    slot_duration = fields.Float(string="Slot Duration", default=0.25)
    slot_height = fields.Float(string="Slot Height(pixels)", default=40)

    patient_font_size = fields.Float(string="Patient Font Size(unit: em)",
                                     default=.85)
    patient_bold = fields.Boolean(string="Make Bold",
                                  help="Shoe patient info in bold style")
    show_urgency = fields.Boolean(string="Show Urgency Patient Icon",help="Show Urgency in scheduler.")
    show_followup = fields.Boolean(string="Show Followup Patient Icon",help="Show Followup details in scheduler.")
    show_new = fields.Boolean(string="Show New Patient Icon",help="Show New in scheduler.")

    @api.model
    def get_values(self):
        res = super(CalenderSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        hide_room_from_calendar_column = literal_eval(ICPSudo.get_param(
            'hide_room_from_calendar_column', default='False'))
        show_time_in_calendar_scheduler = literal_eval(ICPSudo.get_param(
            'show_time_in_calendar_scheduler', default='False'))
        hide_department = literal_eval(ICPSudo.get_param(
            'hide_department', default='False'))
        # Additional Fields added
        show_urgency = literal_eval(ICPSudo.get_param(
            'show_urgency', default='False'))
        show_followup = literal_eval(ICPSudo.get_param(
            'show_followup', default='False'))
        show_new = literal_eval(ICPSudo.get_param(
            'show_new', default='False'))
        
        check_availability = literal_eval(ICPSudo.get_param(
            'check_availability', default='False'))
        validate_phone = literal_eval(ICPSudo.get_param(
            'validate_phone', default='False'))
        patient_bold = literal_eval(ICPSudo.get_param(
            'patient_bold', default='False'))
        patient_font_size = ICPSudo.get_param('patient_font_size', default=0.85)
        resource_order = ICPSudo.get_param('resource_order', default='sequence')
        phone_min_length = ICPSudo.get_param('phone_min_length', default=8)
        phone_max_length = ICPSudo.get_param('phone_max_length', default=8)
        slot_duration = ICPSudo.get_param('slot_duration', default=0.25)
        slot_height = ICPSudo.get_param('slot_height', default=40)
        show_country_code = ICPSudo.get_param('show_country_code')
        show_cancelled = ICPSudo.get_param('show_cancelled')
        res.update({
            'hide_room_from_calendar_column': hide_room_from_calendar_column,
            'show_time_in_calendar_scheduler': show_time_in_calendar_scheduler,
            'resource_order': resource_order,
            'hide_department': hide_department,
            'check_availability': check_availability,
            'validate_phone': validate_phone,
            'patient_bold': patient_bold,
            'patient_font_size': float(patient_font_size),
            'phone_min_length': int(phone_min_length),
            'phone_max_length': int(phone_max_length),
            'slot_duration': float(slot_duration),
            'slot_height': float(slot_height),
            'show_country_code': show_country_code,
            'show_cancelled': show_cancelled,
            'show_urgency': show_urgency,
            'show_followup': show_followup,
            'show_new': show_new,
        })
        return res

    @api.multi
    def set_values(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        super(CalenderSettings, self).set_values()
        ICPSudo.set_param("hide_room_from_calendar_column", self.hide_room_from_calendar_column)
        ICPSudo.set_param("show_time_in_calendar_scheduler", self.show_time_in_calendar_scheduler)
        ICPSudo.set_param("resource_order", self.resource_order)
        ICPSudo.set_param("hide_department", self.hide_department)
        ICPSudo.set_param("check_availability", self.check_availability)
        ICPSudo.set_param("validate_phone", self.validate_phone)
        ICPSudo.set_param("patient_bold", self.patient_bold)
        ICPSudo.set_param("patient_font_size", self.patient_font_size)
        ICPSudo.set_param("phone_min_length", self.phone_min_length)
        ICPSudo.set_param("phone_max_length", self.phone_max_length)
        ICPSudo.set_param("slot_duration", self.slot_duration)
        ICPSudo.set_param("slot_height", self.slot_height)
        ICPSudo.set_param("show_country_code", self.show_country_code)
        ICPSudo.set_param("show_cancelled", self.show_cancelled)
        
        ICPSudo.set_param("show_new", self.show_new)
        ICPSudo.set_param("show_followup", self.show_followup)
        ICPSudo.set_param("show_urgency", self.show_urgency)


class CalendarConfig(models.Model):
    _name = 'calender.config'

    @api.model
    def update_calendar_schedule(self, time_slot):
        """Updates the calendar time schedule"""
        self.env['ir.config_parameter'].sudo().set_param(
            'calendar_scheduler.schedule_start', str(time_slot[0]))
        self.env['ir.config_parameter'].sudo().set_param(
            'calendar_scheduler.schedule_end', str(time_slot[1]))

        return True

    @api.model
    def find_model_options(self):
        tz = pytz.timezone(self.env.user.tz)
        dt = datetime.datetime.utcnow()

        offset_seconds = tz.utcoffset(dt).seconds

        offset_minutes = offset_seconds / 60.0

        show_cancelled = self.env['ir.config_parameter'].sudo().get_param(
            'show_cancelled')
        return [offset_minutes, show_cancelled]

    @api.model
    def find_doctor_ids(self):
        resource_ids = []
        cr = self._cr
        other_hcare_grps = self.find_hcare_groups()
        if other_hcare_grps:
            cr.execute("select D.id "
                       " from medical_physician D,"
                       " res_partner P, medical_department T "
                       "where D.name= P.id and D.active is true and"
                       " T.company_id=%s and "
                       "D.department_id = T.id ORDER BY P.name ASC",
                       (self.env.user.company_id.id,))
            resources = cr.dictfetchall()
            resource_ids = [i['id'] for i in resources]
        else:
            doctor_by_user = (
                self.env.user.physician_ids.ids if self.env.user.physician_ids
                else [])
            if doctor_by_user:
                cr.execute("select D.id "
                           " from medical_physician D,"
                           " res_partner P, medical_department T "
                           "where D.id in %s and "
                           "D.name= P.id and D.active is true and"
                           " D.company_id=%s and "
                           "D.department_id = T.id ORDER BY P.name ASC",
                           (tuple(doctor_by_user),
                            self.env.user.company_id.id))
                resources = cr.dictfetchall()
                resource_ids = [i['id'] for i in resources]
        return resource_ids

    @api.model
    def search_patient_prefix(self, val):
        prefix = self.env.user.company_id.patient_prefix
        vals = [val]
        if prefix:
            if prefix not in val:
                with_prefix = prefix + val
                vals.append(with_prefix)
        return [prefix, vals]

    @api.model
    def search_read_data(self):
        """Gathers the data required for calendar initialisation
        :returns {
            resources: columns used to group the calendar dayview,
            time_schedule: calendar time schedule,
            services: services involved,
            customers: customers list
        }
        """
        ICPSudo = self.env['ir.config_parameter'].sudo()
        cr = self._cr
        states = self.find_states()
        state_names = {}
        for state in states[0]:
            # if state != 'missed' and state != 'cancel':
            state_names[state['state'][0]] = state['state'][1]

        doc_ids = None
        other_hcare_grps = self.find_hcare_groups()
        # #####################################################
        #  old code commented out
        # #####################################################
        # if (self.env.user.has_group(
        #         'pragtech_dental_management.group_dental_doc_menu') and
        #         not other_hcare_grps):
        #     partner_ids = [self.env.user.partner_id.id]
        #     if partner_ids:
        #         doc_ids = [x.id for x in self.env[
        #           'medical.physician'].search(
        #             [('name', 'in', partner_ids)])]
        #     if doc_ids:
        #         cr.execute("select D.id:: VARCHAR as id, P.name as name, "
        #                    "P.id as p_id, P.name as title, "
        #                    "T.id as dept, T.name as dname "
        #                    "from medical_physician D,"
        #                    " res_partner P, medical_department T "
        #                    # "where D.name= P.id and
        #                    D.department_id = T.id;")
        #                    " where D.name= P.id and D.active is true and "
        #                    "D.department_id = T.id and D.id in %s "
        #                    "ORDER BY P.name ASC;", (tuple(doc_ids),))
        resources = []
        resource_ids = []
        resource_order = ICPSudo.get_param('resource_order', default='sequence')
        hide_department = literal_eval(ICPSudo.get_param(
            'hide_department', default='False'))
        order_by = "P.name"
        if resource_order == 'sequence':
            order_by = "D.sequence, P.name"
        d_col = ", T.id as dept, T.name as dname "
        if hide_department:
            d_col = ""

        query_str = ""
        if other_hcare_grps:
            query_str = """
                select D.id:: VARCHAR as id, D.id as _id, 
                P.name as name, P.id as p_id, 
                P.name as title %s  
                from medical_physician D, res_partner P, medical_department T 
                where D.name= P.id and D.active is true and D.company_id=%s and 
                D.department_id = T.id ORDER BY %s ASC
            """ % (d_col, self.env.user.company_id.id, order_by)
        else:
            doctor_by_user = (
                self.env.user.physician_ids.ids if self.env.user.physician_ids
                else [])
            if doctor_by_user:
                if len(doctor_by_user) > 1:
                    d_query = "D.id in %s" % str(tuple(doctor_by_user))
                else:
                    d_query = "D.id=%s" % str(doctor_by_user[0])
                query_str = """
                    select D.id:: VARCHAR as id, D.id as _id,
                     P.name as name, P.id as p_id, 
                    P.name as title %s  
                    from medical_physician D, res_partner P, medical_department T
                    where %s and D.name= P.id and D.active is true and 
                    D.company_id=%s and D.department_id = T.id ORDER BY %s ASC
                """ % (d_col, d_query, self.env.user.company_id.id, order_by)

        if query_str:
            cr.execute(query_str)
            resources = cr.dictfetchall()
            resource_ids = [i['id'] for i in resources]
        rooms = []
        room_ids = []
        if other_hcare_grps:
            cr.execute("select name, id, id as _id, name as title "
                       "from medical_hospital_oprating_room WHERE company_id=%s "
                       "order by sequence asc", (self.env.user.company_id.id,))
            rooms = cr.dictfetchall()
            room_ids = [i['id'] for i in rooms]
        else:
            room_by_user = (
                self.env.user.room_ids.ids if self.env.user.room_ids
                else [])
            if room_by_user:
                cr.execute("select name, id, id as _id, name as title "
                           "from medical_hospital_oprating_room "
                           "where id in %s and company_id=%s "
                           "order by sequence asc",
                           (tuple(room_by_user),self.env.user.company_id.id ))
                rooms = cr.dictfetchall()
                room_ids = [i['id'] for i in rooms]

        get_param = self.env['ir.config_parameter'].sudo().get_param
        #  fetching time schedule
        time_schedule = {
            'schedule_start': get_param(
                'calendar_scheduler.schedule_start') if get_param(
                'calendar_scheduler.schedule_start') else '6:0',
            'schedule_end': get_param(
                'calendar_scheduler.schedule_end') if get_param(
                'calendar_scheduler.schedule_end') else '17:0'
        }
        #  fetching break schedule
        break_schedule = self.prepare_break_time()
        # fetching patients
        cr.execute("SELECT rp.name, mp.id, mp.qid, rp.mobile, mp.patient_id, "
                   "mp.sex, mp.dob, mp.nationality_id "
                   "FROM medical_patient mp "
                   "JOIN res_partner rp  ON(mp.name=rp.id) "
                   "WHERE mp.name IS NOT NULL ")
        patients = cr.dictfetchall()
        # patients = []
        # departments
        cr.execute('select id:: VARCHAR as id, name as name '
                   'from medical_department WHERE company_id=%s ORDER BY name ASC', (self.env.user.company_id.id,))
        departments = cr.dictfetchall()
        # nationality
        cr.execute("select name, code, id "
                   "from patient_nationality")
        nationality_ids = cr.dictfetchall()

        hide_room_from_calendar_column = literal_eval(ICPSudo.get_param('hide_room_from_calendar_column', default='False'))
        show_time_in_calendar_scheduler = literal_eval(ICPSudo.get_param('show_time_in_calendar_scheduler', default='False'))
        other_options = self.get_other_options(time_schedule)

        return [
            resources,
            time_schedule,
            states,
            state_names,
            resource_ids,
            patients,
            # patients_qids,
            departments,
            rooms,
            room_ids,
            resources,
            break_schedule,
            nationality_ids,
            hide_room_from_calendar_column,
            show_time_in_calendar_scheduler,
            other_options
        ]

    @api.model
    def add_appointment(self, data):
        """creates an appointment. Called from js"""
        if data:
            order_id = self.env['pos.order'].create(data)
        return order_id.lines.ids

    def find_states(self):
        """fetching states, with their color"""
        StateObj = self.env['appointment.state.color']
        labels = {}
        for state in StateObj._fields['state'].selection:
            labels[state[0]] = state[1]
        result = []
        vals = []
        for rec in StateObj.search([('state', '!=', None)]):
            vals.append(rec.state)
            result.append({
                'state': [rec.state, labels[rec.state]],
                'color': rec.color
            })
        return result and [result, vals] or []

    def find_hcare_groups(self):
        is_group = False
        # Admin/Receptionist
        if (self.env.user.has_group(
                'pragtech_dental_management.group_dental_mng_menu') or
                self.env.user.has_group(
                    'pragtech_dental_management.group_dental_user_menu')):
            is_group = True
        return is_group

    def _prepare_full_slots(self):
        full_slots = []
        get_param = self.env['ir.config_parameter'].sudo().get_param
        slot = float(get_param('slot_duration')) or 0.25
        start = 0
        end = 24
        while start <= end:
            h_val = start
            if float('.{1:02.0f}'.format(*divmod(start * 60, 60))) >= 0.6:
                h_val = float('{0:02.0f}'.format(*divmod(start * 60, 60))) + 1
            full_slots.append('{0:02.0f}:{1:02.0f}'.format(
                *divmod(h_val * 60, 60)))
            start += slot
        return full_slots

    def get_other_options(self, time_schedule):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        doctor_room_map = self.get_doctor_rooms()
        slot = float(get_param('slot_duration')) or 0.25
        slot_height = float(get_param('slot_height')) or 40


        time_slots = []
        full_slots = self._prepare_full_slots()

        start = time_schedule['schedule_start']
        tmp = start.split(":")
        start = int(tmp[0]) + int(tmp[1]) / 60
        end = time_schedule['schedule_end']
        tmp = end.split(":")
        end = int(tmp[0]) + int(tmp[1]) / 60
        while start <= end:
            h_val = start
            if float('.{1:02.0f}'.format(*divmod(start * 60, 60))) >= 0.6:
                h_val = float('{0:02.0f}'.format(*divmod(start * 60, 60))) + 1
            time_slots.append('{0:02.0f}:{1:02.0f}'.format(
                *divmod(h_val * 60, 60)))
            start += slot

        return {
            'phone_number': {
                'validate_phone': literal_eval(
                    get_param('validate_phone', default='False')),
                'phone_min_length': int(get_param('phone_min_length')) or 8,
                'max_length': int(get_param('phone_max_length')) or 8,
                'show_country_code': get_param('show_country_code'),
            },
            'show_cancelled': get_param('show_cancelled'),
            'patient_bold': literal_eval(
                get_param('patient_bold', default='False')),
            'patient_font_size': get_param('patient_font_size') or '0.85',
            'doctor_map': doctor_room_map[0],
            'room_map': doctor_room_map[1],
            'snap_minutes': slot,
            'slot_duration': '{0:02.0f}:{1:02.0f}:00'.format(*divmod(slot * 60, 60)),
            'full_slots': full_slots,
            'time_slots': time_slots,
            'slot_height': slot_height,
            'allow_past_booking': self.env.user.has_group(
                'pragtech_dental_management.group_allow_past_booking')
        }

    def get_doctor_rooms(self):
        self._cr.execute("select * from doctor_allowed_rooms")
        doctor_map = {}
        room_map = {}
        for rec in self._cr.dictfetchall():
            if rec['doctor_id'] in doctor_map:
                doctor_map[rec['doctor_id']].append(rec['room_id'])
            else:
                doctor_map[rec['doctor_id']] = [rec['room_id']]

            if rec['room_id'] in room_map:
                room_map[rec['room_id']].append(rec['doctor_id'])
            else:
                room_map[rec['room_id']] = [rec['doctor_id']]
        return [doctor_map, room_map]
