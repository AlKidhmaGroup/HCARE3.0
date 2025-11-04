odoo.define('calendar_scheduler.CalendarRenderer2', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var relational_fields = require('web.relational_fields');
var FieldManagerMixin = require('web.FieldManagerMixin');
var field_utils = require('web.field_utils');
var session = require('web.session');
var Dialog = require('web.Dialog');
var Widget = require('web.Widget');
var utils = require('web.utils');
var core = require('web.core');
var QWeb = require('web.QWeb');
var rpc = require('web.rpc');
var NotificationManager = require('web.notification').NotificationManager;

var QWeb2 = core.qweb;

/*We have to gather some details before initialising the widget.
Using the deffered inside the widget does not seems working perfectly
*/

var patients = [];
var resources_list = [];

/*the below function is used to format the time.
 i.e to ensure the correct padding. It may change in some situations.*/
function n2(n){
    var number = n.split(":");
    try {
        number[0] = parseInt(number[0]);
        number[1] = parseInt(number[1]);
    }
    catch (err) {}

    var a = parseInt(number[0]) > 9 ? "" + number[0]: "0" + number[0];
    var b = parseInt(number[1]) > 9 ? "" + number[1]: "0" + number[1];

    return (a + ":" + b);
}

function timeToFloat(n){
    var t_str = n.split(":");
    let h_val = parseInt(t_str[0]) || 0;
    let m_val = 0;
    try {
        m_val = parseInt(t_str[1]);
    }
    catch (e) {}
    return h_val + m_val / 60;
}

var _t = core._t;
var qweb = core.qweb;

var scales = {
    day: 'agendaDay',
    week: 'agendaWeek',
    month: 'month'
};

var SidebarFilterM2O = relational_fields.FieldMany2One.extend({
    _getSearchBlacklist: function () {
        return this._super.apply(this, arguments).concat(this.filter_ids || []);
    },
});

var SidebarFilter = Widget.extend(FieldManagerMixin, {
    template: 'CalendarView.sidebar.filters',
    custom_events: _.extend({}, FieldManagerMixin.custom_events, {
        field_changed: '_onFieldChanged',
    }),
    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} options
     * @param {string} options.fieldName
     * @param {Object[]} options.filters A filter is an object with the
     *   following keys: id, value, label, active, avatar_model, color,
     *   can_be_removed
     * @param {Object} [options.favorite] this is an object with the following
     *   keys: fieldName, model, fieldModel
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        FieldManagerMixin.init.call(this);

        this.title = options.title;
        this.fields = options.fields;
        this.fieldName = options.fieldName;
        this.write_model = options.write_model;
        this.write_field = options.write_field;
        this.avatar_field = options.avatar_field;
        this.avatar_model = options.avatar_model;
        this.filters = options.filters;
        this.label = options.label;
        this.getColor = options.getColor;
    },
    willStart: function () {
        var self = this;
        var defs = [this._super.apply(this, arguments)];

        if (this.write_model || this.write_field) {
            var def = this.model.makeRecord(this.write_model, [{
                name: this.write_field,
                relation: this.fields[this.fieldName].relation,
                type: 'many2one',
            }]).then(function (recordID) {
                self.many2one = new SidebarFilterM2O(self,
                    self.write_field,
                    self.model.get(recordID),
                    {
                        mode: 'edit',
                        attrs: {can_create: false},
                    });
            });
            defs.push(def);
        }
        return $.when.apply($, defs);

    },
    start: function () {
        this._super();
        if (this.many2one) {
            this.many2one.appendTo(this.$el);
            this.many2one.filter_ids = _.without(_.pluck(this.filters, 'value'), 'all');
        }
        this.$el.on('click', '.o_remove', this._onFilterRemove.bind(this));
        this.$el.on('click', '.o_checkbox input', this._onFilterActive.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @param {OdooEvent} event
     */
    _onFieldChanged: function (event) {
        var self = this;
        event.stopPropagation();
        var value = event.data.changes[this.write_field].id;
        this._rpc({
                model: this.write_model,
                method: 'create',
                args: [{'user_id': session.uid,'partner_id': value,}],
            })
            .then(function () {
                self.trigger_up('changeFilter', {
                    'fieldName': self.fieldName,
                    'value': value,
                    'active': true,
                });
            });
    },
    _onFilterActive: function (e) {
        var $input = $(e.currentTarget);
        this.trigger_up('changeFilter', {
            'fieldName': this.fieldName,
            'value': $input.closest('.o_calendar_filter_item').data('value'),
            'active': $input.prop('checked'),
        });
    },
    /**
     * @param {MouseEvent} e
     */
    _onFilterRemove: function (e) {
        var self = this;
        var $filter = $(e.currentTarget).closest('.o_calendar_filter_item');
        Dialog.confirm(this, _t("Do you really want to delete this filter from favorites ?"), {
            confirm_callback: function () {
                self._rpc({
                        model: self.write_model,
                        method: 'unlink',
                        args: [[$filter.data('id')]],
                    })
                    .then(function () {
                        self.trigger_up('changeFilter', {
                            'fieldName': self.fieldName,
                            'id': $filter.data('id'),
                            'active': false,
                            'value': $filter.data('value'),
                        });
                    });
            },
        });
    },
});

return AbstractRenderer.extend({
    template: "CalendarView2",
    events: _.extend({}, AbstractRenderer.prototype.events, {
        'click .o_calendar_sidebar_toggler': '_onToggleSidebar',
        'click .time_schedule_controller': '_onToggleScheduler',
        'click .doctor_controller': '_onToggleDoctor',
        'click .room_controller': '_onToggleRoom',
        'click .states_controller': '_onToggleStates',
        'click .dept_controller': '_onToggleDept',
        'click .update_time': '_onUpdateSchedule',
        'change .cal_doctors': '_onUpdateCalendarDoctor',
        'change .cal_rooms': '_onUpdateCalendarRoom',
        'change .cal_states': '_onUpdateStates',
        'change .cal_dept': '_onUpdateDept',
        'click .all_doctors': 'selectAllDoctors',
        'click .all_rooms': 'selectAllRooms',
        'click .all_states': 'selectAllStates',
        'click .all_depts': 'selectAllDepts',
        'click .no_depts': 'removeAllDepts',
        'click .no_rooms': 'removeAllRooms',
        'click .no_doctors': 'removeAllDoctors',
        'click .no_states': 'removeAllStates',
    }),

    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} state
     * @param {Object} params
     */
    init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.displayFields = params.displayFields;
        this.model = params.model;
        this.filters = [];
        this.color_map = {};
        this.other_options = {};

        if (params.eventTemplate) {
            this.qweb = new QWeb(session.debug, {_s: session.origin});
            this.qweb.add_template(utils.json_node_to_xml(params.eventTemplate));
        }
        this.notification_manager = new NotificationManager(this);
    },
    willStart: function () {
	    var self = this;
	    var defs = [this._super.apply(this, arguments)];

	    var calendarConfig = rpc.query({
	       model: 'calender.config',
	       method: 'search_read_data',
	    }).then(function(res) {

	        _(res[9]).each(function (resource) {
	            resource['id'] = 'doctor_' + resource['id'];
	        });
	        self.doctors = res[9];
	        self.doctors_grouped = _.groupBy(res[9], 'dept');

	        _(res[0]).each(function (resource) {
	            resource['id'] = 'doctor_' + resource['id'];
	        });

	        /*doctors list*/
	        resources_list = res[0];

	        /*adding rooms list*/
	        if (res[12]==false){
                _(res[7]).each(function (resource) {
                    resource['id'] = 'room_' + resource['id'];
                    resources_list.push(resource);
                });
	        }

	        /*resources_list.push({
	            id: -1,
	            title: "Others"
	        });*/

	        patients = res[5];

	        self.resources = resources_list ? resources_list : [];
	        /*resource ids*/
	        self.resource_ids = res[4] ? res[4] : [];
	        /*calendar time schedule*/
	        self.time_schedule = res[1] ? res[1] : {schedule_start: '6:0', schedule_end: '17:0'};
	        /*states list*/
	        self.states_list = res[2] ? res[2] : [];
	        /*state names*/
	        self.state_names = res[3] ? res[3] : [];
	        /*dept*/
	        self.departments = res[6] ? res[6] : [];

	        self.patients = {};
	        self.phone_no = [];
	        self.qid = [];
	        self.pat_names = [];
	        self.pat_ids = [];

	        $.each(patients, function(p) {
	            self.patients[patients[p]['id']] = patients[p];
	            if(patients[p]['mobile']){
	                self.phone_no.push(
	                    {label:patients[p]['mobile'], value:patients[p]['id']});
	            }
	            if(patients[p]['qid']){
	                self.qid.push(
	                    {label:patients[p]['qid'], value:patients[p]['id']});
	            }
	            self.pat_ids.push(
	                {label:patients[p]['patient_id'], value:patients[p]['id']});
	            self.pat_names.push(
	                {label:patients[p]['name'], value:patients[p]['id']});
	        });
	        /*rooms*/
	        self.rooms_list = res[7] ? res[7] : [];
	        /*room_ids*/
	        self.room_ids = res[8] ? res[8] : [];
            self.break_schedule = res[10];
            self.nationality_ids = res[11];
            self.show_time_in_calendar_scheduler = res[13];
            self.other_options = res[14];
	    });
	    defs.push(calendarConfig);
	    return $.when.apply($, defs);
	},
    /**
     * @override
     * @returns {Deferred}
     */
    start: function () {
        this.time_slots = this.other_options.time_slots;

        this._initSidebar();
        this._initCalendar();
        $('.o_content').scroll(function () {
            if ($(this).find('div.o_scheduler_container')) {
                var cal_head = $(this).find('div.o_scheduler_container .o_calendar_view td.fc-head-container th');
                var cal_head2 = $(this).find('div.o_scheduler_container .o_calendar_view .o_calendar_widget *');
                cal_head2.css('z-index', 'unset');
                cal_head.css({
                    'transform': 'translateY('+ this.scrollTop +'px)',
                    'position': 'relative',
                    'z-index': '999',
                    'opacity': '1'
                });

            }
        });
        return this._super();
    },
    /**
     * @override
     */
    destroy: function () {
        if (this.$calendar) {
            this.$calendar.fullCalendar2('destroy');
        }
        if (this.$small_calendar) {
            this.$small_calendar.datepicker('destroy');
            $('#ui-datepicker-div:empty').remove();
        }
        this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

	/*find_time_slots: function (time_limit) {
		*//*Will return the time duration for the day
        * as 15 minute slots *//*
        function n(n){
            return n > 9 ? "" + n: "0" + n;
        }
        var schedule = [], temp;
		if (!time_limit) {
			var start = this.time_schedule.schedule_start.replace(':', '.');
            var end = this.time_schedule.schedule_end.replace(':', '.');
            var k = parseInt(start.split('.')[1]), j;
            switch(k) {
                case 0: j=0; break;
                case 15: j=1; break;
                case 30: j=2; break;
                case 45: j=3; break;
                default: j=0;
            }
		}
		else {
			var start = time_limit.start.replace(':', '.');
            var end = time_limit.end.replace(':', '.');
            k = j = 0;
		}

        for (var i=parseFloat(start); i<parseFloat(end); i++) {
            for (j;j<4;j++) {
                temp = n(parseInt(i)) + ':' + n(k);
                k += 15;
                schedule.push(temp);
            }
            k = j = 0;
        }
        if (parseFloat(end) == 24.0) {
            schedule.push('24:00');
        }
        return schedule;
	},*/
    /**
     * Note: this is not dead code, it is called by the calendar-box template
     *
     * @param {any} record
     * @param {any} fieldName
     * @param {any} imageField
     * @returns {string[]}
     */
    getAvatars: function (record, fieldName, imageField) {
        var field = this.state.fields[fieldName];

        if (!record[fieldName]) {
            return [];
        }
        if (field.type === 'one2many' || field.type === 'many2many') {
            return _.map(record[fieldName], function (id) {
                return '<img src="/web/image/'+field.relation+'/'+id+'/'+imageField+'" />';
            });
        } else if (field.type === 'many2one') {
            return ['<img src="/web/image/'+field.relation+'/'+record[fieldName][0]+'/'+imageField+'" />'];
        } else {
            var value = this._format(record, fieldName);
            var color = this.getColor(value);
            if (isNaN(color)) {
                return ['<span class="o_avatar_square" style="background-color:'+color+';"/>'];
            }
            else {
                return ['<span class="o_avatar_square o_calendar_color_'+color+'"/>'];
            }
        }
    },
    /**
     * Note: this is not dead code, it is called by two template
     *
     * @param {any} key
     * @returns {integer}
     */
    getColor: function (key) {
        if (!key) {
            return;
        }
        if (this.color_map[key]) {
            return this.color_map[key];
        }
        // check if the key is a css color
        if (typeof key === 'string' && key.match(/^((#[A-F0-9]{3})|(#[A-F0-9]{6})|((hsl|rgb)a?\(\s*(?:(\s*\d{1,3}%?\s*),?){3}(\s*,[0-9.]{1,4})?\))|)$/i)) {
            return this.color_map[key] = key;
        }
        var index = (((_.keys(this.color_map).length + 1) * 5) % 24) + 1;
        this.color_map[key] = index;
        return index;
    },
    getFont: function () {
        let f_style = 'font-size:' + this.other_options.patient_font_size + 'em;'
        if (this.other_options.patient_bold)
            f_style += 'font-weight: bold;'
        return f_style ? f_style : '';
    },
    /**
     * @override
     */
    getLocalState: function () {
        var $fcScroller = this.$calendar.find('.fc-scroller');
        return {
            scrollPosition: $fcScroller.scrollTop(),
        };
    },
    /**
     * @override
     */
    setLocalState: function (localState) {
        if (localState.scrollPosition) {
            var $fcScroller = this.$calendar.find('.fc-scroller');
            $fcScroller.scrollTop(localState.scrollPosition);
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @param {any} event
     * @returns {string} the html for the rendered event
     */
    _eventRender: function (event) {
        var qweb_context = {
            event: event,
            record: event.record,
            widget: this,
            read_only_mode: this.read_only_mode,
            user_context: session.user_context,
            format: this._format.bind(this),
            fields: this.state.fields
        };
        this.qweb_context = qweb_context;
        if (_.isEmpty(qweb_context.record)) {
            return '';
        } else {
            return (this.qweb || qweb).render("calendar-box", qweb_context);
        }
    },
    /**
     * @param {any} record
     * @param {any} fieldName
     * @returns {string}
     */
    _format: function (record, fieldName) {
        var field = this.state.fields[fieldName];
        if (field.type === "one2many" || field.type === "many2many") {
            return field_utils.format[field.type]({data: record[fieldName]}, field);
        } else {
            return field_utils.format[field.type](record[fieldName], field, {forceString: true});
        }
    },

    getCalendarOptions: function () {
        var self = this;
        this.event_rendering = {};
        return $.extend({}, this.state.fc_options, {
            snapMinutes: this.other_options.snap_minutes,
            defaultView: 'agendaDay',
            schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
            resourceAreaWidth: '100px',
            businessHours: this.break_schedule,
//            selectConstraint: 'businessHours',
//            selectConstraintType: 'nonBusinessHours',  // new option
            refetchResourcesOnNavigate: true,
            resources: function(callback, start, end, timezone) {
                var tz_offset = self.getSession().getTZOffset(start);
                let utc_start = start.clone().add(-tz_offset, 'minutes')
                let utc_end = end.clone().add(-tz_offset, 'minutes')
                self._rpc({
                    model: 'working.time',
                    method: 'fetch_business_hours',
                    args: [{
                        'mode': self.state.scale,
                        'date_from': utc_start.format("YYYY-MM-DD"),
                        'datetime_from': utc_start.format("YYYY-MM-DD HH:mm:ss"),
                        'date_to': utc_end.format("YYYY-MM-DD"),
                        'datetime_to': utc_end.format("YYYY-MM-DD HH:mm:ss"),
                        'res_ids': self.resource_ids,
                        'tz_offset': tz_offset
                    }],
                }).then(function (wt_list) {
                    if (self.state.scale == 'day') {
                        self.businessHours = [];
                        _.each(self.resources, function (r) {
                            r.businessHours = wt_list[r._id] || [];
                        });
                    }
                    else {
                        self.businessHours = wt_list;
                        _.each(self.resources, function (r) {
                            r.businessHours = [];
                        });
                    }
                    callback(self.resources);
                    self.resize_slot();
                });
            },
            unknownResourceTitle: 'Others',
            slotDuration: this.other_options.slot_duration,
            slotLabelInterval: this.other_options.slot_duration,
            minTime: n2(self.time_schedule.schedule_start),
            maxTime: n2(self.time_schedule.schedule_end),
            eventDrop: function (event, _delta, _revertFunc) { //_day_delta, _minute_delta, _all_day, _revertFunc) {
                if (!confirm("Are you sure about this change?")) {
                    _revertFunc();
                } else {
                    self.event_rendering[event.id] = false;
                    self.trigger_up('dropRecord', event);
                }
            },
            eventResize: function (event, delta, revertFunc) {
                if (!confirm("Are you sure about this change?")) {
                    revertFunc();
                }
                 else {
                    self.trigger_up('updateRecord', event);
                }
            },
            eventClick: function (event, js_event) {
                var $el = $(js_event.currentTarget);
                self.remove_tooltip($el);
                self.event_rendering[event.id] = false;
                self.trigger_up('openEvent', event);
                self.$calendar.fullCalendar2('unselect');
            },
            select: function (start_date, end_date, event, _js_event, _view) {
                if (!self.is_allowed_select(start_date, end_date, _view)) {
                    self.$calendar.fullCalendar2('unselect');
                    return
                }
                var today = moment().clone().startOf('day');
                if (start_date.isBefore(today) && !self.other_options.allow_past_booking) {
                    self.trigger_up('showWarning', {
                        'message': "You have no permission for backdated appointments!"
                    });
                    return
                }
                var data = {
                    'start': start_date,
                    'end': end_date,
                    'resourceId': _view ? _view.id : null
                };
                if (self.state.context.default_name) {
                    data.title = self.state.context.default_name;
                }
                /*check for reschedule*/
                if (self.cached_booking) {
                    let confirm_msg = ("An appointment is selected for rescheduling, " +
                        "press 'cancel' to proceed as a new booking, press 'ok' to reschedule the " +
                        "selected appointment to this slot");
                    if (confirm(confirm_msg)) {
                        self.do_apply_cached_data(self.cached_booking, data);
                        self.cached_booking = null;
                        return
                    }
                    self.cached_booking = null;
                }
                self.trigger_up('openCreate', data);
                self.$calendar.fullCalendar2('unselect');
            },
            eventAfterRender: function( event, element, view ) {
                self.event_rendering[event.id] = true;
            },
            eventRender: function (event, element) {
                var $render = $(self._eventRender(event));
                event.title = $render.find('.o_field_type_char:first').text();
                var display_hour = '';
                if (!event.allDay) {
                    var start = event.r_start || event.start;
                    var end = event.r_end || event.end;
                    var timeFormat = _t.database.parameters.time_format.search("%H") != -1 ? 'HH:mm': 'h:mma';
                    display_hour = start.format(timeFormat) + ' - ' + end.format(timeFormat);
                    if (display_hour === '00:00 - 00:00') {
                        display_hour = _t('All day');
                    }
                }
                var display_scheduler_hour = '';
                if (self.show_time_in_calendar_scheduler==true){
                    var display_scheduler_hour = display_hour;
                }
                var doctor_user = $render.find('.o_field_doctor_user').text().trim();
                if (doctor_user == 'True') {
                    $render.find('.o_field_doctor_user').text(display_scheduler_hour);
                    $render.find('.o_field_patient_name_phone').text('');
                }
                else {
                    $render.find('.o_field_doctor_user').text(display_scheduler_hour);
                    $render.find('.o_field_patient_name').text('');
                }
                element.find('.fc-content').html($render.html());
                element.addClass($render.attr('class'));
                if (event && event.record && event.record.has_insurance == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/insurance.jpeg'
                        }));
		if (event && event.record && event.record.followup == true && event.record.show_followup_icon == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/followup_patient.jpg'
                        }));
		if (event && event.record && event.record.is_registered == false && event.record.show_new_icon == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/new_patient.jpg'
                        }));
		if (event && event.record && event.record.urgency == true && event.record.show_urgency_icon == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/emergency.jpg'
                        }));
                if (event && event.record && event.record.is_child == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/child.jpeg'
                        }));
                if (event && event.record && event.record.frequent_cancel == true)
                    element.find('.fc-content').prepend(
                        QWeb2.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/cancelled.jpeg'
                        }));
                if (event && event.record && event.record.is_vip == true)
                    element.find('.fc-content').prepend(
                        '<div class="ribbon_div"><i class="fa fa-star checked" style="color:#39968a;background-color: white;"/>' +
                        '<i class="fa fa-star checked" style="color:#39968a;background-color: white;"/>' +
                        '<i class="fa fa-star checked" style="color:#39968a;background-color: white;"/></div>');
				/*try {
	                display_hour += event.record.patient ? ' - ' + event.record.patient[1]:'';
                }
                catch (err) {}*/
                element.find('.fc-content .fc-time').text(display_hour);
//                element.find('.fc-content .o_fields div').css('word-wrap', 'break-word');
                element.find('.fc-content .o_fields').attr('style', self.getFont());
                element.css({
                    'margin-top': '2px',
                    'margin-bottom': '2px'
                });
            },
            eventMouseout: function( event, jsEvent, view ) {
                var $el = $(jsEvent.currentTarget);
                self.remove_tooltip($el);
            },
            eventMouseover: function( event, jsEvent, view ) {
                var $el = $(jsEvent.currentTarget);
                self._addTooltip(event, $el);
                $el.trigger('mouseover');
            },
            stateCtrl: function (ev1, ev2) {
                return self.setup_state_control(ev1, ev2);
            },
            // Dirty hack to ensure a correct first render
            eventAfterAllRender: function () {
                $(window).trigger('resize');
            },
            viewRender: function (view) {
                // compute mode from view.name which is either 'month', 'agendaWeek' or 'agendaDay'
                var mode = view.name === 'month' ? 'month' : (view.name === 'agendaWeek' ? 'week' : 'agendaDay');
                // compute title: in week mode, display the week number
                view.title = view.title.trim();
                var title = mode === 'week' ? view.intervalStart.week() : view.title;
                self.trigger_up('viewUpdated', {
                    mode: mode,
                    title: title,
                });
            },
            height: 'parent',
            unselectAuto: false,
        });
    },
    /**
     * Initialize the main calendar
     */
    _initCalendar: function () {
        var self = this;

        this.$calendar = this.$(".o_calendar_widget");

        //Documentation here : http://arshaw.com/fullcalendar/docs/
        var fc_options = this.getCalendarOptions();

//        if (this.break_schedule)
//            fc_options.businessHours = this.break_schedule;

		$('.o_calendar_widget:not(".fc-event")').on('contextmenu', function (e) {
            e.preventDefault()
        });

        this.$calendar.fullCalendar2(fc_options);
    },

    is_allowed_select: function (start, end, resource) {
        let time_start = timeToFloat(start.format("HH:mm"));
        let time_end = timeToFloat(end.format("HH:mm"));
        let weekday = start.weekday(); // assume the selection will be within a day

        let active_hours = [];
        if (this.state.scale == 'week') {
            if (!this.businessHours || this.businessHours.length <= 0)
                return true

            active_hours = _.filter(this.businessHours, function (bh) {
                return bh.dow.includes(weekday) && bh.block_selection == true;
            });
        }
        else if (this.state.scale == 'day') {
            let res = _.filter(this.resources, function (r) {
                return r._id == resource._id;
            });
            if (!res || res.length <= 0)
                return true;

            active_hours = _.filter(res[0].businessHours, function (bh) {
                return bh.dow.includes(weekday) && bh.block_selection == true;
            });
        }
        if (active_hours && active_hours.length > 0) {
            let block_selection = false;
            for (var i=0;i<active_hours.length;i++) {
                let bh = active_hours[i];
                let current_start = timeToFloat(bh.start), current_stop = timeToFloat(bh.end);
                if (time_start >= current_start && time_start < current_stop) {
                    /*starts at or after break start and end before break end*/
                    block_selection = true;
                    break;
                }
                else if (time_end > current_start && time_end <= current_stop) {
                    /*starts after break start and end before break end*/
                    block_selection = true;
                    break;
                }
            }
            if (block_selection == true)
                return false
        }
        return true
    },
    resize_slot: function () {
        let slot_height = this.other_options.slot_height + 'px';
        this.$calendar.find('.fc-time-grid .fc-slats td').css('height', slot_height);
        this.strip_break_hours();
    },
    strip_break_hours: function () {
        /*shrink the break hours*/
        var $tr;
        var self = this;

        this.$calendar.fullCalendar2('option', {
            businessHours: this.businessHours
        });

        _.each(this.break_schedule, function (bs) {
            var b_start = timeToFloat(bs.start);
            var b_stop = timeToFloat(bs.end);
            _.each(self.time_slots, function (s) {
                let t_val = timeToFloat(s);
                if (t_val < b_stop && t_val >= b_start) {
                    $tr = self.$calendar.find("tr[time_slot='" + s + "']");
                    $tr.attr("data-slot_display", bs.block_selection ? "hidden" : "show");
                    if (!bs.hide_slots) {
                        $tr.css({
                            'background-color': '#7b7575',
                            'opacity': 0.3
                        });
                        return
                    }
                    if ($tr && $tr.length > 0) {
                        $tr.find("td").css({
                            'height': '1px',
                            'padding': '0px',
                            'border': '1px solid #f99494'
                        });
                        $tr.find("td span").hide();
                    }
                }
            });
    //        this.$calendar.find("div.fc-nonbusiness ").hide();
        });
    },

    do_apply_cached_data: function (rec_id, data) {
        this.trigger_up('applyReschedule', {
            id: rec_id,
            data: data
        });
    },
    setup_state_control: function (ev1, ev2) {
        var self = this, curr_state;
        if (ev1.record.break_time) {
            for (var j=0;j<this.states_list[0].length;j++) {
                var state_el = this.states_list[0][j];
                if (state_el.state[0] == ev1.record.state) {
                    curr_state = state_el;
                    break;
                }
            }
        }
        else
            curr_state = this.findCurrentState(ev1.color);

        var states_list = [];
        var new_state_sel;
        if (curr_state.state[0] == 'draft') {
            for (var s=0;s<this.states_list[0].length;s++) {
                if (this.states_list[0][s].state[0] == 'confirmed' ||
                    this.states_list[0][s].state[0] == 'cancel') {
                        new_state_sel = 'confirmed';
                        states_list.push(this.states_list[0][s]);
                    }
            }
            states_list.push(this.get_reschedule_entry());
        }
        else if (curr_state.state[0] == 'confirmed') {
            for (var s=0;s<this.states_list[0].length;s++) {
                if (this.states_list[0][s].state[0] == 'missed' ||
                    this.states_list[0][s].state[0] == 'cancel') {
                        new_state_sel = 'missed';
                        states_list.push(this.states_list[0][s]);
                    }
            }
            states_list.push(this.get_reschedule_entry());
        }
        else if (['missed', 'cancel'].includes(curr_state.state[0])) {
            states_list.push(this.get_reschedule_entry());
        }
        else {
            return false
        }

        var opt = {
            style_val: 'left:'+ (ev2.pageX - 180)+'px;top:'+(ev2.pageY - 150)+
                'px;width: 205px; height: 170px;',
            states_list: states_list,
            active_color: ev1.color
        };

        var sched_el = $(QWeb2.render(
            'calendarModal2',
            opt
        ));

        sched_el.find('.modal-dialog').draggable({
            cursor: 'move',
            handle: '.modal-header'
        });
        $('.modal-dialog>.modal-content>.modal-header').css('cursor', 'move');
        sched_el.modal();

        sched_el.find('.state_ctrl').val(new_state_sel);

        sched_el.on('click', '#update_evt_status', function () {
            var new_state = sched_el.find('.state_ctrl').val();
            var new_color = ev1.color;

            var state_el;
            for (var j=0;j<self.states_list[0].length;j++) {
                state_el = self.states_list[0][j];
                if (state_el.state[0] == new_state) {
                    new_color = state_el.color;
                    break;
                }
            }
            if (new_color == ev1.color) {sched_el.find(".close_btn").click();}

            ev1.color = new_color;
            ev1.state = new_state;
            self.trigger_up('updateState', ev1);

            sched_el.find(".close_btn").click();
        });

        return false
    },
    get_reschedule_entry: function () {
        return {
            'state': ['reschedule', 'Reschedule']
        }
    },
    remove_tooltip: function (el) {
        $("div.popover").remove();
        el.popover('destroy');
    },
    _addTooltip: function (event, el) {
        this.remove_tooltip(el);
	    if (!event.record || !this.event_rendering[event.id]){
	        return
        }
        el.popover({
            html: true,
            title: event.record.display_name,
            content: function () {
                return "<p>" + event.record.patient_name_phone + "</br>" + event.record.comments + "</p>";
            },
            trigger: 'hover',
            placement: 'top',
            container: 'body'
        });
    },
    findCurrentState: function (color_val) {
        for (var j=0;j<this.states_list[0].length;j++) {
            var state_el = this.states_list[0][j];
            if (state_el.color == color_val) {
                return state_el;
            }
        }
    },
    /**
     * Initialize the mini calendar in the sidebar
     */
    _initCalendarMini: function () {
        var self = this;
        this.$small_calendar = this.$(".o_calendar_mini");
        this.$small_calendar.datepicker({
            'onSelect': function (datum, obj) {
                self.trigger_up('changeDate', {
                    date: moment(new Date(+obj.currentYear , +obj.currentMonth, +obj.currentDay))
                });
            },
            'dayNamesMin' : this.state.fc_options.dayNamesShort,
            'monthNames': this.state.fc_options.monthNamesShort,
            'firstDay': this.state.fc_options.firstDay,
        });

        if (this.state.fullWidth == true) {
            this.$('.o_calendar_sidebar_schedule').addClass('o_hidden');
            this.$('.o_calendar_sidebar_doctor').addClass('o_hidden');
            this.$('.o_calendar_sidebar_room').addClass('o_hidden');
//            this.$('.o_calendar_sidebar_resource').addClass('o_hidden');
            this.$('.o_calendar_sidebar_states').addClass('o_hidden');
            this.$('.o_calendar_sidebar_dept').addClass('o_hidden');
        }
        else {
            this.$('.o_calendar_sidebar_schedule').removeClass('o_hidden');
            this.$('.o_calendar_sidebar_doctor').removeClass('o_hidden');
            this.$('.o_calendar_sidebar_room').removeClass('o_hidden');
//            this.$('.o_calendar_sidebar_resource').removeClass('o_hidden');
            this.$('.o_calendar_sidebar_states').removeClass('o_hidden');
            this.$('.o_calendar_sidebar_dept').removeClass('o_hidden');
        }
    },
    initCalendarSchedule: function () {
        /*initialises the calendar time schedule controller*/
        var options = {
            time_schedule: this.other_options.full_slots,
            start: n2(this.time_schedule.schedule_start),
            end: n2(this.time_schedule.schedule_end),
        };

		var sched_el = QWeb2.render(
			'CalendarView2.sidebar.schedule',
			options
		);

		this.$calendar_schedule.append($(sched_el));
    },
    initCalendarDoctors: function () {
	    /*initialises the calendar doctors controller*/
	    var options = {
	        doctors: this.doctors
	    };

	    var res_el = QWeb2.render(
	        'CalendarView2.sidebar.doctors',
	        options
	    );
	    this.$calendar_doctor.append($(res_el));
	    this.$calendar_doctor.find('.cal_doctors').select2();
	},
	initCalendarRooms: function () {
	    /*initialises the calendar rooms controller*/
	    var options = {
	        rooms: this.rooms_list
	    };

	    var res_el = QWeb2.render(
	        'CalendarView2.sidebar.rooms',
	        options
	    );
	    this.$calendar_room.append($(res_el));
	    this.$calendar_room.find('.cal_rooms').select2();
	},
    initCalendarStates: function () {
        /*initialises the calendar states controller*/
        var self = this;
        this.state_color = {};
        for (var s in this.states_list[0]) {
            this.state_color[this.states_list[0][s].state[0]] = this.states_list[0][s].color;
        }
        var options = {
            states: this.state_names,
            state_color: this.state_color,
            show_cancelled: this.other_options.show_cancelled
        };

		var res_el = QWeb2.render(
			'CalendarView2.sidebar.states',
			options
		);
		this.$calendar_states.append($(res_el));
		this.$calendar_states.find('.cal_states').select2({
		    formatSelection: function (data, container) {
                return "<span style='padding: 2px;color: #2d2c2cc7;font-weight: 600;" +
                    "background-image:none;background-color:" +
                    self.state_color[data.id] + "'>" + data.text + "</span>";
            }
		});
    },
    initCalendarDept: function () {
        /*initialises the calendar dept controller*/
        var options = {
            departments: this.departments
        };

		var res_el = QWeb2.render(
			'CalendarView2.sidebar.dept',
			options
		);
		this.$calendar_dept.append($(res_el));
		this.$calendar_dept.find('.cal_dept').select2();
    },
    _onUpdateSchedule: function (e) {
        var start = $('.duration_start').val();
        var end = $('.duration_end').val();
        if (!this.validate_time_schedule(start, end)) {
            this.notification_manager.do_warn(
                "Invalid Timing",
                _t("Ending time should be after starting time!")
            );
            return
        }

        var self = this;

        var time_def = rpc.query({
            model: 'calender.config',
            method: 'update_calendar_schedule',
            args: [[start, end]]
        });
        return $.when(time_def).then(function (result) {
                self.schedule_start = start ? start : "06:00";
                self.schedule_end = end ? end : "17:00";
                location.reload();
            });
    },
    /**
     * Initialize the sidebar
     */
    _initSidebar: function () {
        this.$sidebar = this.$('.o_calendar_sidebar');
        this.$sidebar_container = this.$(".o_calendar_sidebar_container");
        this.$calendar_schedule = this.$(".o_calendar_schedule");
        this.$calendar_doctor = this.$(".o_calendar_doctor");
        this.$calendar_room = this.$(".o_calendar_room");
        this.$calendar_states = this.$(".o_calendar_states");
        this.$calendar_dept = this.$(".o_calendar_dept");
        this._initCalendarMini();
        this.initCalendarSchedule();
        this.initCalendarDoctors();
        this.initCalendarRooms();
        this.initCalendarStates();
        this.initCalendarDept();
    },
    /**
     * Render the calendar view, this is the main entry point.
     *
     * @override method from AbstractRenderer
     * @returns {Deferred}
     */
    _render: function () {
        var $calendar = this.$calendar;
        var $fc_view = $calendar.find('.fc-view');
        var scrollPosition = $fc_view.scrollLeft();
        var scrollTop = this.$calendar.find('.fc-scroller').scrollTop();

        $fc_view.scrollLeft(0);
        $calendar.fullCalendar2('unselect');

        if (scales[this.state.scale] !== $calendar.data('fullCalendar').getView().type) {
            $calendar.fullCalendar2('changeView', scales[this.state.scale]);
        }

        if (this.target_date !== this.state.target_date.toString()) {
            $calendar.fullCalendar2('gotoDate', moment(this.state.target_date));
            this.target_date = this.state.target_date.toString();
        }

        this.$small_calendar.datepicker("setDate", this.state.highlight_date.toDate())
                            .find('.o_selected_range')
                            .removeClass('o_color o_selected_range');
        var $a;
        switch (this.state.scale) {
            case 'month': $a = this.$small_calendar.find('td a'); break;
            case 'week': $a = this.$small_calendar.find('tr:has(.ui-state-active) a'); break;
            case 'day': $a = this.$small_calendar.find('a.ui-state-active'); break;
        }
        $a.addClass('o_selected_range');
        setTimeout(function () {
            $a.not('.ui-state-active').addClass('o_color');
        });

        $fc_view.scrollLeft(scrollPosition);

        var fullWidth = this.state.fullWidth;
        this.$('.o_calendar_sidebar_toggler')
            .toggleClass('fa-close', !fullWidth)
            .toggleClass('fa-chevron-left', fullWidth)
            .attr('title', !fullWidth ? _('Close Sidebar') : _('Open Sidebar'));
        this.$sidebar_container.toggleClass('o_sidebar_hidden', fullWidth);
        this.$sidebar.toggleClass('o_hidden', fullWidth);

        this._renderFilters();
        this.$calendar.appendTo('body');
        if (scrollTop) {
            this.$calendar.fullCalendar2('reinitView');
        } else {
            this.$calendar.fullCalendar2('render');
        }
        this._renderEvents();
        this.$calendar.prependTo(this.$('.o_calendar_view'));

        this.resize_slot();
        return this._super.apply(this, arguments);
    },
    /**
     * Render all events
     */
    _renderEvents: function () {
        this.$calendar.fullCalendar2('removeEvents');
        this.$calendar.fullCalendar2('addEventSource', this.state.data);
    },
    /**
     * Render all filters
     */
    _renderFilters: function () {
        var self = this;
        _.each(this.filters || (this.filters = []), function (filter) {
            filter.destroy();
        });
        if (this.state.fullWidth) {
            return;
        }
        _.each(this.state.filters, function (options) {
            if (!_.find(options.filters, function (f) {return f.display == null || f.display;})) {
                return;
            }
            options.getColor = self.getColor.bind(self);
            options.fields = self.state.fields;

            var filter = new SidebarFilter(self, options);
            filter.appendTo(self.$sidebar);
            self.filters.push(filter);
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Toggle the sidebar
     */
    _onToggleSidebar: function () {
        this.trigger_up('toggleFullWidth');
        /*scheduler start*/
        this.$('.o_calendar_sidebar_schedule').toggleClass('o_hidden');
        this.$('.o_calendar_schedule').addClass('o_hidden');

		var height_val = '30px';
        var class_name = 'fa fa-caret-right';
        var cl1 = '.o_calendar_sidebar_schedule';
        var cl2 =  '.time_schedule_controller';
        this._updateScheduleController(cl1, cl2, height_val, class_name);
		/*scheduler end*/

			/*doctor start*/
        this.$('.o_calendar_sidebar_doctor').toggleClass('o_hidden');
//        this.$('.o_calendar_sidebar_resource').toggleClass('o_hidden');
        this.$('.o_calendar_doctor').addClass('o_hidden');

        var cl1 = '.o_calendar_sidebar_doctor';
//        var cl1 = '.o_calendar_sidebar_resource';
        var cl2 =  '.doctor_controller';
//        var cl2 =  '.resource_controller';
        this._updateScheduleController(cl1, cl2, height_val, class_name);
        /*doctor end*/

        /*room start*/
        this.$('.o_calendar_sidebar_room').toggleClass('o_hidden');
        this.$('.o_calendar_room').addClass('o_hidden');

        var cl1 = '.o_calendar_sidebar_room';
        var cl2 =  '.room_controller';
        this._updateScheduleController(cl1, cl2, height_val, class_name);
        /*room end*/

        /*states start*/
        this.$('.o_calendar_sidebar_states').toggleClass('o_hidden');
        this.$('.o_calendar_states').addClass('o_hidden');

        var cl1 = '.o_calendar_sidebar_states';
        var cl2 =  '.states_controller';
        this._updateScheduleController(cl1, cl2, height_val, class_name);
        /*states end*/

        /*dept start*/
        this.$('.o_calendar_sidebar_dept').toggleClass('o_hidden');
        this.$('.o_calendar_dept').addClass('o_hidden');

        var cl1 = '.o_calendar_sidebar_dept';
        var cl2 =  '.dept_controller';
        this._updateScheduleController(cl1, cl2, height_val, class_name);
        /*states end*/
    },
    _onToggleScheduler: function () {
        var cl1 = '.o_calendar_sidebar_schedule';
        var cl2 =  '.time_schedule_controller';
        this.$('.o_calendar_schedule').toggleClass('o_hidden');
        if(this.$('.o_calendar_schedule').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = '170px';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },
    _onToggleDoctor: function () {
        var cl1 = '.o_calendar_sidebar_doctor';
//        var cl1 = '.o_calendar_sidebar_resource';
        var cl2 =  '.doctor_controller';
//        var cl2 =  '.resource_controller';
        this.$('.o_calendar_doctor').toggleClass('o_hidden');
        if(this.$('.o_calendar_doctor').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = 'auto';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },
    _onToggleRoom: function () {
        var cl1 = '.o_calendar_sidebar_room';
        var cl2 =  '.room_controller';
        this.$('.o_calendar_room').toggleClass('o_hidden');
        if(this.$('.o_calendar_room').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = 'auto';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },
    _onToggleStates: function () {
        var cl1 = '.o_calendar_sidebar_states';
        var cl2 =  '.states_controller';
        this.$('.o_calendar_states').toggleClass('o_hidden');
        if(this.$('.o_calendar_states').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = 'auto';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },
    _onToggleDept: function () {
        var cl1 = '.o_calendar_sidebar_dept';
        var cl2 =  '.dept_controller';
        this.$('.o_calendar_dept').toggleClass('o_hidden');
        if(this.$('.o_calendar_dept').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = 'auto';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },
    _onToggleDept: function () {
        var cl1 = '.o_calendar_sidebar_dept';
        var cl2 =  '.dept_controller';
        this.$('.o_calendar_dept').toggleClass('o_hidden');
        if(this.$('.o_calendar_dept').hasClass('o_hidden')) {
            var height_val = '30px';
            var class_name = 'fa fa-caret-right';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
        else {
            var height_val = 'auto';
            var class_name = 'fa fa-caret-down';
            this._updateScheduleController(cl1, cl2, height_val, class_name);
        }
    },

    _updateScheduleController: function (cl1, cl2, height_val, class_name) {
        this.$(cl1).css('height', height_val);
        this.$(cl2).removeClass('fa fa-caret-down');
        this.$(cl2).removeClass('fa fa-caret-right');
        this.$(cl2).addClass(class_name);
    },
    _onUpdateCalendarDoctor: function (event) {
        if ($(event)[0].val && typeof $(event)[0].val == 'object') {
            $('select.cal_dept').find('option').removeAttr('selected');
            var doctor_ids_selected = $(event)[0].val;
            var doctors = this.doctorById(doctor_ids_selected);

            var rooms = this._findResourceRooms();
            var room_ids = this.roomsById(rooms);

            this.trigger_up('reloadCalendarDoctor', {
                'doctors': doctors[0],
                'doctor_ids': doctors[1],
                'rooms': room_ids[0],
                'room_ids': room_ids[1],
            });

            /*update dept filter*/
            var dept_ids = this.findValidDept(doctors[1]);
            this.selectDept(dept_ids);
            $('select.cal_dept').trigger('change');
        }
    },
    _onUpdateCalendarRoom: function (event) {
        if ($(event)[0].val && typeof $(event)[0].val == 'object') {
	        var doctor_ids_selected = this._findResourceDoctors();;
	        var doctors = this.doctorById(doctor_ids_selected);

	        var rooms = this._findResourceRooms();
	        var room_ids = this.roomsById(rooms);

	        this.trigger_up('reloadCalendarDoctor', {
	            'doctors': doctors[0],
	            'doctor_ids': doctors[1],
	            'rooms': room_ids[0],
	            'room_ids': room_ids[1],
	        });
        }
    },
    _onUpdateStates: function (event) {
        this.trigger_up('reloadCalendarState',
            $(event)[0].val);

        var state_tags = this.$calendar_states.find('.select2-container-multi .select2-choices .select2-search-choice');

        state_tags.css({
            'background-image': 'none'
        });

        for (var tag=0;tag<state_tags.length;tag++) {
            var color_key = $(state_tags[tag]).find('div').text().trim();
            $(state_tags[tag]).css({
                'background-color': this.state_color[color_key]
            });
        }
    },
    _onUpdateDept: function (event) {
        if ($(event)[0].val && typeof $(event)[0].val == 'object') {
	        /*remove all existing doctors and add doctors of selected departments only*/
	        /*removing all doctors*/
	        $('select.cal_doctors').find('option').removeAttr('selected');
	        /*find doctors in the selected departments*/
	        var dept_selected = $(event)[0].val ? $(event)[0].val : [];

	        var doctor_ids = this.doctorByDept(dept_selected);

	        var rooms = this._findResourceRooms();
	        var room_ids = this.roomsById(rooms);
	        this.trigger_up('reloadCalendarDoctor', {
	            'doctors': doctor_ids[0],
	            'doctor_ids': doctor_ids[1],
	            'rooms': room_ids[0],
	            'room_ids': room_ids[1],
	        });
	        /*select the doctors automatically*/
	        this.selectDoctors(doctor_ids[1]);

	        $('select.cal_doctors ').trigger('change');
        }
    },
    selectAllDoctors: function (event) {
        var doctor_ids = [];
        _.each(this.doctors, function (doc) {
            doctor_ids.push(doc.id);
        });

        var rooms = this._findResourceRooms();
        var room_ids = this.roomsById(rooms);
        var self = this;
        this.trigger_up('reloadCalendarDoctor', {
            'doctors': self.doctors,
            'doctor_ids': doctor_ids,
            'rooms': room_ids[0],
            'room_ids': room_ids[1],
        });

        $('select.cal_dept > option').prop('selected', 'selected')
        $('select.cal_dept ').trigger('change');

        $('select.cal_doctors > option').prop('selected', 'selected')
        $('select.cal_doctors ').trigger('change');
    },
    removeAllDoctors: function (event) {
        var rooms = this._findResourceRooms();
        var room_ids = this.roomsById(rooms);
        this.trigger_up('reloadCalendarDoctor', {
            'doctors': [],
            'doctor_ids': [],
            'rooms': room_ids[0],
            'room_ids': room_ids[1],
        });

        $('select.cal_dept > option').removeAttr('selected');
        $('select.cal_dept ').trigger('change');

        $('select.cal_doctors > option').removeAttr('selected');
        $('select.cal_doctors ').trigger('change');
    },
    selectAllRooms: function (event) {
        var doctor_ids_selected = this._findResourceDoctors();;
        var doctors = this.doctorById(doctor_ids_selected);

        this.trigger_up('reloadCalendarDoctor', {
            'doctors': doctors[0],
            'doctor_ids': doctors[1],
            'rooms': this.rooms_list,
            'room_ids': this.room_ids,
        });
        $('select.cal_rooms > option').prop('selected', 'selected');
        $('select.cal_rooms ').trigger('change', event);
    },
    removeAllRooms: function (event) {
        var doctor_ids_selected = this._findResourceDoctors();;
        var doctors = this.doctorById(doctor_ids_selected);

        this.trigger_up('reloadCalendarDoctor', {
            'doctors': doctors[0],
            'doctor_ids': doctors[1],
            'rooms': [],
            'room_ids': [],
        });
        $('select.cal_rooms > option').removeAttr('selected');
        $('select.cal_rooms ').trigger('change', event);
    },
    selectAllStates: function (event) {
        $('select.cal_states > option').prop('selected', 'selected');
        $('select.cal_states ').trigger('change', event);
        this.trigger_up('reloadCalendarState',
                $('select.cal_states ').val());
    },
    removeAllStates: function (event) {
        $('select.cal_states').find('option').removeAttr('selected');
        $('select.cal_states ').trigger('change', event);
        this.trigger_up('reloadCalendarState',
                $('select.cal_states ').val());
    },
    selectAllDepts: function (event) {
        var doctor_ids = [];
        _.each(this.doctors, function (doc) {
            doctor_ids.push(doc.id);
        });

        var rooms = this._findResourceRooms();
        var room_ids = this.roomsById(rooms);
        var self = this;
        this.trigger_up('reloadCalendarDoctor', {
            'doctors': self.doctors,
            'doctor_ids': doctor_ids,
            'rooms': room_ids[0],
            'room_ids': room_ids[1],
        });

		$('select.cal_dept > option').prop('selected', 'selected')
		$('select.cal_dept ').trigger('change');

		$('select.cal_doctors > option').prop('selected', 'selected')
        $('select.cal_doctors ').trigger('change');
    },
    removeAllDepts: function (event) {
        var rooms = this._findResourceRooms();
        var room_ids = this.roomsById(rooms);
        this.trigger_up('reloadCalendarDoctor', {
            'doctors': [],
            'doctor_ids': [],
            'rooms': room_ids[0],
            'room_ids': room_ids[1],
        });

        $('select.cal_dept > option').removeAttr('selected');
        $('select.cal_dept ').trigger('change');

        $('select.cal_doctors > option').removeAttr('selected');
        $('select.cal_doctors ').trigger('change');
    },
    _findResourceDoctors: function () {
        var doctor_ids = $('select.cal_doctors').val() ? $('select.cal_doctors').val() : [];
        return doctor_ids;
    },
    _findResourceRooms: function () {
        var room_ids = $('select.cal_rooms').val() ? $('select.cal_rooms').val() : [];
        return room_ids;
    },
    doctorById: function (ids) {
        var doctors = [];
        var doctor_ids = [];
        for (var r in this.doctors) {
            if (ids.includes(this.doctors[r].id)) {
                doctors.push(this.doctors[r]);
                doctor_ids.push(this.doctors[r].id);
            }
        }
        return [doctors, doctor_ids];
    },
    doctorByDept: function (dept_ids) {
        if (!dept_ids) {
            return [[], []];
        }
        for (var i in dept_ids) {
            dept_ids[i] = parseInt(dept_ids[i]);
        }
        var doctors = [];
        var doctor_ids = [];
        for (var r in this.doctors) {
            if (this.doctors[r].dept &&
                dept_ids.includes(this.doctors[r].dept)) {
                doctors.push(this.doctors[r]);
                doctor_ids.push(this.doctors[r].id);
            }
        }
        return [doctors, doctor_ids];
    },
    roomsById: function (room_ids) {
        if (!room_ids) {
            return [[], []];
        }
        var rooms = [];
        var room_id = [];
        for (var r in this.rooms_list) {
            if (room_ids.includes(this.rooms_list[r].id)) {
                rooms.push(this.rooms_list[r]);
                room_id.push(this.rooms_list[r].id);
            }
        }

        return [rooms, room_id];
    },
    selectDoctors: function (doc_ids) {
        var options = $('select.cal_doctors > option');
        for (var i=0; i<options.length;i++) {
            if (doc_ids.includes($(options[i]).val())) {
                $(options[i]).prop('selected', 'selected');
            }
        }
    },
    selectDept: function (dept_ids) {
        var options = $('select.cal_dept > option');
        for (var i=0; i<options.length;i++) {
            if (dept_ids.includes($(options[i]).val())) {
                $(options[i]).prop('selected', 'selected');
            }
        }
    },
    findValidDept: function (doctor_ids) {
        /*executed when we change doctors list: need to show departments
        only if all the doctors under each dept is loaded*/
        var valid_dept, dept_ids = [];
        for (var i in this.doctors_grouped) {
            valid_dept = true;
            for (var j in this.doctors_grouped[i]) {
                if (!doctor_ids.includes(this.doctors_grouped[i][j]['id'])) {
                    valid_dept = false;
                }
            }
            if (valid_dept == true) {
                dept_ids.push(i);
            }
        }
        return dept_ids;
    },
    validate_time_schedule: function (start, end) {
        return timeToFloat(end) > timeToFloat(start)
    }
});

});
