# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import api, exceptions, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


def to_js_weekday(dow):
    dow = int(dow)
    if dow == 6:
        dow = 0
    else:
        dow += 1
    return dow


def time_to_float(val):
    res = val.split(":")
    h_val = float(res[0])
    m_val = len(res) > 1 and float(res[1]) or 0.0
    return h_val + m_val / 60


def float_to_time(val):
    if float(val) > 24.0:
        val -= 24
    return '{0:02.0f}:{1:02.0f}'.format(*divmod(val * 60, 60))


default_time_slot = {
    'className': 'fc-nonbusiness',
    'start': "00:00",
    'end': "00:00",
    'dow': [0, 1, 2, 3, 4, 5, 6],
    'hide_slots': False,
    'block_selection': False,
    'rendering': 'background',
}


class WorkingTime(models.Model):
    _name = 'working.time'
    _rec_name = 'time_from'

    def get_time_selection(self):
        return [(i, i) for i in self.env[
            'calender.config']._prepare_full_slots()]

    active = fields.Boolean(default=True, copy=False)
    type = fields.Selection([
        ('on', "ON"), ('off', "OFF")])
    time_from = fields.Selection(
        selection=get_time_selection, string="From", required=True)
    time_to = fields.Selection(
        selection=get_time_selection, string="To", required=True)
    hide_slots = fields.Boolean(string="Hide Slots")

    @api.onchange('time_from', 'time_to')
    def onchange_time(self):
        for rec in self.filtered(lambda l: l.time_from and l.time_to):
            if time_to_float(rec.time_from) > time_to_float(rec.time_to):
                raise exceptions.Warning(
                    "Starting time cannot be after ending time!")

    def get_break_time(self):
        res = []
        for rec in self.search([('type', '=', 'off')]):
            tmp = default_time_slot.copy()
            tmp.update({
                'start': rec.time_from,
                'end': rec.time_to,
                'hide_slots': rec.hide_slots,
                'block_selection': rec.hide_slots,
            })
            res.append(tmp)
        return res and res or False

    def fetch_weekly_leaves(self, args):
        """Fetch the weekly leaves based on working time"""
        # assuming that this function will be used only in day mode
        # because resource grouping will be only in day mode
        week_day = datetime.strptime(args['datetime_to'], DTF).weekday()
        res_ids = args.get('res_ids', [])
        res_ids = [int(i) for i in res_ids]
        result = dict((i, []) for i in res_ids)
        cr = self._cr
        cr.execute("select mp.id, rr.calendar_id as wt_id "
                   "from medical_physician mp "
                   "join resource_resource rr on(rr.user_id=mp.user_id) "
                   "where mp.id in %s",
                   (tuple(res_ids), ))
        wt_ids = dict((m_p['id'], m_p['wt_id']) for m_p in cr.dictfetchall())
        work_times = self.env['resource.calendar'].browse(set(wt_ids.values()))
        full_week_days = ['0', '1', '2', '3', '4', '5', '6']
        for doc in wt_ids:
            work_time = work_times.filtered(lambda t: t.id == wt_ids[doc])
            # gather the leave days first
            work_days = work_time.attendance_ids.mapped('dayofweek')
            leave_days = list(set(full_week_days) - set(work_days))

            if str(week_day) in leave_days:
                # this day is not working day
                tmp = default_time_slot.copy()
                tmp.update({
                    'start': "00:00",
                    'end': "23:59",
                    # 'dow': [week_day]
                    'dow': [to_js_weekday(week_day)]
                })
                result[doc].append(tmp)
                continue

            # check all the working days and find off time per each day
            leave_by_day = {
                '0': [],
                '1': [],
                '2': [],
                '3': [],
                '4': [],
                '5': [],
                '6': [],
            }

            att_ids = work_time.attendance_ids.filtered(
                lambda w: int(w.dayofweek) == week_day)
            if not att_ids:
                continue
            if args.get('date_from'):
                att_ids = att_ids.filtered(
                    lambda w: not w.date_from or (
                            w.date_from and
                            datetime.strptime(
                                w.date_from, DF) <= datetime.strptime(
                        args['date_from'], DF)))

            if not att_ids:
                continue
            if args.get('date_to'):
                att_ids = att_ids.filtered(
                    lambda w: not w.date_to or (
                            w.date_to and datetime.strptime(
                                w.date_to, DF) >= datetime.strptime(
                        args['date_to'], DF)))

            if not att_ids:
                continue

            time_start = 0
            for w_day in att_ids:
                if time_start < w_day.hour_from:
                    tmp = default_time_slot.copy()
                    tmp.update({
                        'start': float_to_time(time_start),
                        'end': float_to_time(w_day.hour_from),
                        'dow': [0, 1, 2, 3, 4, 5, 6],
                        # 'dow': [int(w_day.dayofweek)],
                    })
                    leave_by_day[str(week_day)].append(tmp)
                    time_start = w_day.hour_to
            if time_start < 24:
                tmp = default_time_slot.copy()
                tmp.update({
                    'start': float_to_time(time_start),
                    'end': "23:59",
                    'dow': [0, 1, 2, 3, 4, 5, 6],
                    # 'dow': [week_day],
                })
                leave_by_day[str(week_day)].append(tmp)

            for l_day in leave_by_day:
                if len(leave_by_day[l_day]) > 0:
                    result[doc] += leave_by_day[l_day]

        return result

    def get_leave_domain(self, args, employees):
        return [
            '&',
            '&', ('employee_id', 'in', employees), ('state', 'in', ['validate']),
            '|',
            '|',
            '|',
            '|', ('date_from', '=', args['datetime_from']), ('date_to', '=', args['datetime_to']),  # start time same or end time same
            '&', ('date_from', '<=', args['datetime_from']), ('date_to', '>=', args['datetime_to']),  # booking included within selected slot or same timing
            '&', ('date_from', '<', args['datetime_from']), ('date_to', '>', args['datetime_from']),  # booking starts before slot time
            '&', ('date_from', '>', args['datetime_from']), ('date_from', '<', args['datetime_to'])  # booking starts after slot time
        ]

    def fetch_leave_requests(self, args):
        res_ids = args.get('res_ids', [])
        res_ids = [int(i) for i in res_ids]
        result = dict((i, []) for i in res_ids)

        cr = self._cr
        cr.execute("select mp.id, he.id as resource "
                   "from medical_physician mp "
                   "join resource_resource rr on(rr.user_id=mp.user_id) "
                   "join hr_employee he on(he.resource_id=rr.id) "
                   "where mp.id in %s",
                   (tuple(res_ids),))
        doctor_map = dict(
            (i['resource'], i['id']) for i in cr.dictfetchall()
            if i['resource'])

        dt_from = datetime.strptime(args['datetime_from'], DTF)
        dt_to = datetime.strptime(args['datetime_to'], DTF)
        l_domain = self.get_leave_domain(args, list(doctor_map.keys()))
        for leave in self.env['hr.holidays'].search(l_domain):
            l_from = datetime.strptime(leave.date_from, DTF)
            l_to = datetime.strptime(leave.date_to, DTF)

            time_start = 0
            time_stop = 24 - args.get('tz_offset', 0) / 60
            if l_from >= dt_from and l_to <= dt_to:
                # leave is inside the time input
                time_start = l_from.hour + l_from.minute / 60
                time_stop = l_to.hour + l_to.minute / 60
            elif l_from <= dt_from:
                time_start = dt_from.hour + dt_from.minute / 60
            elif l_to >= dt_to:
                time_stop = dt_to.hour + dt_to.minute / 60

            tmp = default_time_slot.copy()
            tmp.update({
                'start': float_to_time(
                    time_start + args.get('tz_offset', 0) / 60),
                'end': float_to_time(
                    time_stop + args.get('tz_offset', 0) / 60),
                'hide_slots': False,
                'block_selection': True,
                'dow': [0, 1, 2, 3, 4, 5, 6]
                # 'dow': [dt_to.weekday()]
            })

            if leave.employee_id.id in doctor_map:
                doc = doctor_map[leave.employee_id.id]
                result[doc].append(tmp)
        return result

    def _company_leave_domain(self, args):
        return [
            '&',
            '&', '&',
            ('calendar_id', '=', False), ('holiday_id', '=', False),
            ('resource_id', '=', False),
            '|',
            '|',
            '|',
            '|', ('date_from', '=', args['datetime_from']), ('date_to', '=', args['datetime_to']),
            '&', ('date_from', '<=', args['datetime_from']), ('date_to', '>=', args['datetime_to']),
            '&', ('date_from', '<', args['datetime_from']), ('date_to', '>', args['datetime_from']),
            '&', ('date_from', '>', args['datetime_from']), ('date_from', '<', args['datetime_to'])
        ]

    def fetch_company_holidays(self, args):
        result = []
        l_domain = self._company_leave_domain(args)

        dt_from = datetime.strptime(args['datetime_from'], DTF) + timedelta(
                            minutes=args.get('tz_offset', 0))
        dt_to = datetime.strptime(args['datetime_to'], DTF) + timedelta(
                            minutes=args.get('tz_offset', 0))
        for leave in self.env['resource.calendar.leaves'].search(l_domain):
            l_from = datetime.strptime(leave.date_from, DTF) + timedelta(
                            minutes=args.get('tz_offset', 0))
            l_to = datetime.strptime(leave.date_to, DTF) + timedelta(
                            minutes=args.get('tz_offset', 0))

            # single day holiday
            if l_from.date() == l_to.date():
                tmp = default_time_slot.copy()
                current_start = max(l_from, dt_from)
                current_stop = min(l_to, dt_to)
                time_start = current_start.hour + current_start.minute / 60
                time_stop = current_stop.hour + current_stop.minute / 60
                tmp.update({
                    'start': float_to_time(time_start),
                    'end': float_to_time(time_stop),
                    'hide_slots': False,
                    'block_selection': True,
                    'dow': [to_js_weekday(min(l_to, dt_to).weekday())]
                    # 'dow': [dt_to.weekday()]
                })

                result.append(tmp)
            else:
                # multi-day span
                current_start = max(l_from, dt_from)
                time_start = current_start.hour + current_start.minute / 60
                time_stop = 24
                # l_to_time = l_to.hour + l_to.minute / 60
                while current_start < min(dt_to, l_to):
                    tmp = default_time_slot.copy()
                    p_weekday = current_start.weekday()

                    if current_start.date() == l_to.date():
                        time_stop = l_to.hour + l_to.minute / 60
                    tmp.update({
                        'start': float_to_time(time_start),
                        'end': float_to_time(time_stop),
                        'hide_slots': False,
                        'block_selection': True,
                        'dow': [to_js_weekday(p_weekday)]
                    })

                    result.append(tmp)

                    current_start += timedelta(days=1)
                    current_start = current_start.replace(
                        hour=0, minute=0, second=0)
                    time_start = 0
        return result

    @api.model
    def fetch_business_hours(self, args={}):
        """
        prepare business hour object per resource
        :param args: object containing view mode, date duration and resource ids
        :return:
        """
        # fetch the common break hours configured
        break_hours = self.get_break_time()
        if not break_hours:
            break_hours = []
        weekly_leaves = {}
        leave_requests = {}

        # company holidays
        company_holidays = self.fetch_company_holidays(args)
        if args.get('mode', 'week') == "week":
            result = break_hours + company_holidays
        else:
            # weekly leaves
            if len(args.get('res_ids', [])) > 0:
                weekly_leaves = self.fetch_weekly_leaves(args)

                # fetch leave requests
                leave_requests = self.fetch_leave_requests(args)

            result = self.process_full_break(
                break_hours, weekly_leaves, leave_requests, company_holidays)
        return result

    def process_full_break(self, break_hours, weekly_leaves,
                           leave_requests, company_holidays):
        if break_hours:
            for w_l in weekly_leaves:
                weekly_leaves[w_l] += break_hours

        for l_r in leave_requests:
            weekly_leaves[l_r] += leave_requests[l_r]

        for l_r in weekly_leaves:
            weekly_leaves[l_r] += company_holidays
        return weekly_leaves


class CalendarConfigExt(models.Model):
    _inherit = 'calender.config'

    def prepare_break_time(self):
        return self.env['working.time'].get_break_time()
