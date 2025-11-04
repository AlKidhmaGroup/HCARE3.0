odoo.define('calendar_scheduler.CalendarController2', function (require) {
"use strict";

/**
 * Calendar Controller
 *
 * This is the controller in the Model-Renderer-Controller architecture of the
 * calendar view.  Its role is to coordinate the data from the calendar model
 * with the renderer, and with the outside world (such as a search view input)
 */

var AbstractController = require('web.AbstractController');
var QuickCreate = require('calendar_scheduler.CalendarQuickCreate2');
var dialogs = require('web.view_dialogs');
var Dialog = require('web.Dialog');
var core = require('web.core');
var rpc = require('web.rpc');
var time = require('web.time');
var NotificationManager = require('web.notification').NotificationManager;

var _t = core._t;
var QWeb = core.qweb;

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

function dateToServer (date) {
    return date.clone().utc().locale('en').format('YYYY-MM-DD HH:mm:ss');
}

var CalendarController2 = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        quickCreate: '_onQuickCreate',
        openCreate: '_onOpenCreate',
        openEvent: '_onOpenEvent',
        applyReschedule: '_onApplyReschedule',
        dropRecord: '_onDropRecord',
        updateRecord: '_onUpdateRecord',
        updateState: '_onUpdateState',
        changeDate: '_onChangeDate',
        changeFilter: '_onChangeFilter',
        toggleFullWidth: '_onToggleFullWidth',
        viewUpdated: '_onViewUpdated',
        reloadCalendarDoctor: 'reloadCalendarDoctor',
        reloadCalendarState: 'reloadCalendarState',
        showWarning: 'showWarning',
        resize_slot: 'resizeSlot',
    }),
    /**
     * @override
     * @param {Widget} parent
     * @param {AbstractModel} model
     * @param {AbstractRenderer} renderer
     * @param {Object} params
     */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.current_start = null;
        this.displayName = params.displayName;
        this.quickAddPop = params.quickAddPop;
        this.disableQuickCreate = params.disableQuickCreate;
        this.eventOpenPopup = params.eventOpenPopup;
        this.formViewId = params.formViewId;
        this.readonlyFormViewId = params.readonlyFormViewId;
        this.mapping = params.mapping;
        this.context = params.context;
        // The quickCreating attribute ensures that we don't do several create
        this.quickCreating = false;
        this.notification_manager = new NotificationManager(this);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Render the buttons according to the CalendarView.buttons template and
     * add listeners on it. Set this.$buttons with the produced jQuery element
     *
     * @param {jQueryElement} [$node] a jQuery node where the rendered buttons
     *   should be inserted. $node may be undefined, in which case the Calendar
     *   inserts them into this.options.$buttons or into a div of its template
     */
    renderButtons: function ($node) {
        var self = this;
        this.$buttons = $(QWeb.render("CalendarView.buttons", {'widget': this}));
        this.$buttons.on('click', 'button.o_calendar_button_new', function () {
            self.trigger_up('switch_view', {view_type: 'form'});
        });

        _.each(['prev', 'today', 'next'], function (action) {
            self.$buttons.on('click', '.o_calendar_button_' + action, function () {
                self.model[action]();
                self.reload();
            });
        });
        _.each(['day', 'week', 'month'], function (scale) {
            self.$buttons.on('click', '.o_calendar_button_' + scale, function () {
                self.model.setScale(scale);
                self.reload();
            });
        });

         this.$buttons.on('click', '.o_calendar_reload', function () {
		    self.reload();
		    self.reloadPatients();
		 });

        this.$buttons.find('.o_calendar_button_' + this.mode).addClass('active');

        if ($node) {
            this.$buttons.appendTo($node);
        } else {
            this.$('.o_calendar_buttons').replaceWith(this.$buttons);
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @param {Object} record
     * @param {integer} record.id
     * @returns {Deferred}
     */
    _updateRecord: function (record) {
        return this.model.updateRecord(record).then(this.reload.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @param {OdooEvent} event
     */
    _onChangeDate: function (event) {
        var modelData = this.model.get();
        if (modelData.target_date.format('YYYY-MM-DD') === event.data.date.format('YYYY-MM-DD')) {
            // When clicking on same date, toggle between the two views
            switch (modelData.scale) {
                case 'month': this.model.setScale('day'); break;
                case 'week': this.model.setScale('day'); break;
                case 'day': this.model.setScale('day'); break;
            }
        } else if (modelData.target_date.week() === event.data.date.week()) {
            // When clicking on a date in the same week, switch to day view
            this.model.setScale('day');
        } else {
            // When clicking on a random day of a random other week, switch to week view
            this.model.setScale('day');
        }
        this.model.setDate(event.data.date);
        this.reload();
    },
    /**
     * @param {OdooEvent} event
     */
    _onChangeFilter: function (event) {
        if (this.model.changeFilter(event.data) && !event.data.no_reload) {
            this.reload();
        }
    },
    /**
     * @param {OdooEvent} event
     */
    _onDropRecord: function (event) {
        var self = this;
        var data = this.model.calendarEventToRecord(event.data);
        this.model._rpc({
            model: this.model.modelName,
            method: 'check_availability',
            args: [[event.data.id], data, null, event.data.id]
        }).then(function (res) {
            if (!res) {
                self.notification_manager.do_warn(
                    "Slot unavailable!",
                    _t('Patient already has another appointment at the same time!')
                );
                self.reload();
            }
            else {
                self._updateRecord(event.data);
            }
        });
    },
    /**
     * Handles saving data coming from quick create box
     *
     * @private
     * @param {OdooEvent} event
     */
    _onQuickCreate: function (event) {
        if (this.quickCreating) {
            return;
        }
        this.quickCreating = true;
        var self = this;
        var data = this.model.calendarEventToRecord(event.data.data);
        data.break_time = event.data.create_vals.break_time;
        let patient = null;
        if (event.data && event.data.create_vals && event.data.create_vals.patient)
            patient = event.data.create_vals.patient;
        this.model._rpc({
            model: this.model.modelName,
            method: 'check_availability',
            args: [[], data, patient]
        }).then(function (res) {
            if (!res) {
                self.notification_manager.do_warn(
                    "Slot unavailable!",
                    _t('Patient already has another appointment at the same time!')
                );
                self.quickCreating = false;
            }
            else {
                self.model.createRecord(event)
                    .done(function (res) {
                        self.quick.destroy();
                        self.quick = null;
                        self.reload().then(function () {
                         /*if (event.data.create_vals &&
                             event.data.create_vals.is_registered == false) {

                                *//*res: created appointment id,
                                p_id: created patient id,
                                pf_id: created patient file number*//*
                                var p_id = self.renderer.state.appointment_patient[res][0];
                                var pf_id = self.renderer.state.appointment_patient[res][1];

                                var pat_rec = {
                                    dob: event.data.create_vals['dob'],
                                    id: p_id,
                                    mobile: event.data.create_vals['patient_phone'],
                                    name: event.data.create_vals['patient_name'],
                                    patient_id: self.renderer.state.appointment_patient[res][1],
                                    qid: event.data.create_vals['qid'],
                                    sex: event.data.create_vals['sex'],
                                };
                                self.renderer.patients[p_id] = pat_rec;

                                if(pat_rec['mobile']){
                                    self.renderer.phone_no.push(
                                        {label:pat_rec['mobile'], value:p_id});
                                }
                                if(pat_rec['qid']){
                                    self.renderer.qid.push(
                                        {label:pat_rec['qid'], value:p_id});
                                }
                                self.renderer.pat_ids.push(
                                    {label:pf_id, value:p_id});
                                self.renderer.pat_names.push(
                                    {label:pat_rec['name'], value:p_id});
                             }*/
                        });
                    })
                    .fail(function (error, errorEvent) {
                        // This will occurs if there are some more fields required
                        // Preventdefaulting the error event will prevent the traceback window
                        errorEvent.preventDefault();
                        event.data.options.disableQuickCreate = true;
                        event.data.data.on_save = self.quick.destroy.bind(self.quick);
                        self._onOpenCreate(event.data);
                    })
                    .always(function () {
                        self.quickCreating = false;
                    });
            }
        });
    },
    /**
     * @param {OdooEvent} event
     */
    _onOpenCreate: function (event) {
        var self = this;
        if (this.model.get().scale === "month") {
            event.data.allDay = true;
        }
        var data = this.model.calendarEventToRecord(event.data);

        var context = _.extend({}, this.context, event.options && event.options.context);
        context.default_name = data.name || null;
        context['default_' + this.mapping.date_start] = data[this.mapping.date_start] || null;
        if (this.mapping.date_stop) {
            context['default_' + this.mapping.date_stop] = data[this.mapping.date_stop] || null;
        }
        if (this.mapping.date_delay) {
            context['default_' + this.mapping.date_delay] = data[this.mapping.date_delay] || null;
        }
        if (this.mapping.all_day) {
            context['default_' + this.mapping.all_day] = data[this.mapping.all_day] || null;
        }

        for (var k in context) {
            if (context[k] && context[k]._isAMomentObject) {
                context[k] = context[k].clone().utc().format('YYYY-MM-DD HH:mm:ss');
            }
        }

        var options = _.extend({}, this.options, event.options, {context: context});

        if (this.quick != null) {
            this.quick.destroy();
            this.quick = null;
        }

        if(!options.disableQuickCreate && !event.data.disableQuickCreate && this.quickAddPop) {
            this.quick = new QuickCreate(this, true, options, data, event.data);
            this.quick.open();
            this.quick.focus();
            return;
        }

        var title = _t("Create");
        if (this.renderer.arch.attrs.string) {
            title += ': ' + this.renderer.arch.attrs.string;
        }
        if (this.eventOpenPopup) {
            new dialogs.FormViewDialog(self, {
                res_model: this.modelName,
                context: context,
                title: title,
                disable_multiple_selection: true,
                on_saved: function () {
                    if (event.data.on_save) {
                        event.data.on_save();
                    }
                    self.reload();
                },
            }).open();
        } else {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: this.modelName,
                views: [[this.formViewId || false, 'form']],
                target: 'current',
                context: context,
            });
        }
    },
    /**
     * @param {OdooEvent} event
     */
    _onOpenEvent: function (event) {
        var self = this;
        var id = event.data.id;
        id = id && parseInt(id).toString() === id ? parseInt(id) : id;

        if (!this.eventOpenPopup) {
            this._rpc({
                model: self.modelName,
                method: 'get_formview_id',
                //The event can be called by a view that can have another context than the default one.
                args: [],
            }).then(function (viewId) {
                self.do_action({
                    type:'ir.actions.act_window',
                    res_id: id,
                    res_model: self.modelName,
                    views: [[viewId || false, 'form']],
                    target: 'current',
                    context: event.context || self.context,
                });
            });
            return;
        }

        var open_dialog = function (readonly) {
            var options = {
                res_model: self.modelName,
                res_id: id || null,
                context: event.context || self.context,
                readonly: readonly,
                title: _t("Open: ") + event.data.title,
                on_saved: function () {
                    if (event.data.on_save) {
                        event.data.on_save();
                    }
                    self.reload();
                },
            };
            if (readonly) {
                if (self.readonlyFormViewId) {
                    options.view_id = parseInt(self.readonlyFormViewId);
                }
                options.buttons = [
                    {
                        text: _t("Edit"),
                        classes: 'btn-primary',
                        close: true,
                        click: function () { open_dialog(false); }
                    },
                    {
                        text: _t("Delete"),
                        click: function () {
                            Dialog.confirm(this, _t("Are you sure you want to delete this record ?"), {
                                confirm_callback: function () {
                                    self.model.deleteRecords([id], self.modelName)
                                        .then(function () {
                                            self.dialog.destroy();
                                            self.reload();
                                        });
                                }
                            });
                        },
                    },
                    {text: _t("Close"), close: true}
                ];
            } else if (self.formViewId) {
                options.view_id = parseInt(self.formViewId);
            }
            self.dialog = new dialogs.FormViewDialog(self, options).open();
        };
        open_dialog(true);
    },
    /**
     * Called when we want to open or close the sidebar.
     */
    _onToggleFullWidth: function () {
        this.model.toggleFullWidth();
        this.reload();
    },
    /**
     * @param {OdooEvent} event
     */
    _onUpdateRecord: function (event) {
        var self = this;
        var data = this.model.calendarEventToRecord(event.data);
        this.model._rpc({
            model: this.model.modelName,
            method: 'check_availability',
            args: [[event.data.id], data, null, event.data.id]
        }).then(function (res) {
            if (!res) {
                self.notification_manager.do_warn(
                    "Slot unavailable!",
                    _t('Patient already has another appointment at the same time!')
                );
                self.reload();
            }
            else {
                self._updateRecord(event.data);
            }
        });
    },
    _onUpdateState: function (event) {
        if (event.data.state == 'reschedule') {
            return this.trigger_reschedule(event);
        }
        this._updateRecord(event.data).then(function () {
            if (event.data.state == 'checkin') {
                rpc.query({
                    model: 'medical.appointment',
                    method: 'checkin',
                    args: [[event.data.id]]
                });
            }
        });
    },

    trigger_reschedule: function (event) {
        let book_id = null;
        if (event && event.data && event.data.id)
            book_id = event.data.id;
        if (!book_id)
            return
        this.renderer.cached_booking = book_id;
        return
    },
    _onApplyReschedule: function (event) {
        var data = event.data.data, rec_id = event.data.id;
        var self = this;
        let ctx = Object.assign({}, this.context);
        ctx.action_origin = 'reschedule';

        let event_data = this.model.calendarEventToRecord(event.data.data);
        let write_vals = {};
        write_vals[this.mapping.date_start] = dateToServer(event_data[this.mapping.date_start]);
        write_vals[this.mapping.date_stop] = dateToServer(event_data[this.mapping.date_stop]);

        var resource_vals = data.resourceId ? data.resourceId.split('_') : [false];
		if (resource_vals[0] == 'doctor') {
            write_vals.doctor = parseInt(resource_vals[1]);
            write_vals.room_id = false;
        } else if (resource_vals[0] == 'room') {
            write_vals.room_id = parseInt(resource_vals[1]);
            write_vals.doctor = false;
        }
        else {
            write_vals.doctor = parseInt(data.resourceId);
        }

        var self = this;
        this.model._rpc({
            model: this.model.modelName,
            method: 'check_availability',
            args: [[parseInt(rec_id)], write_vals]
        })
        .then(function (res) {
            if (!res) {
                self.notification_manager.do_warn(
                    "Slot unavailable!",
                    _t('Patient already has another appointment at the same time!')
                );
                self.reload();
            }
            else {
                self.model._rpc({
                    model: self.model.modelName,
                    method: 'write',
                    args: [[parseInt(rec_id)], write_vals],
                    context: ctx
                }).then(function () {
                    self.reload();
                });
            }
        });

    },
    /*
    trigger_reschedule: function (event) {
        var data = event.data, self = this;
        var dateFormat = time.getLangDateFormat();
        var timeFormat = time.getLangTimeFormat();
        var opt = {
            allow_update: true,
            old_date_from: moment(data.start).format(dateFormat + " " + timeFormat),
            old_date_to: moment(data.end).format(dateFormat + " " + timeFormat),
            doctor: data.record.doctor,
            time_slots: self.renderer.time_slots
        };
        var $modal = $(QWeb.render('EventUpdateModal', opt));
        $modal.find("select").select2();
        $modal.modal();

        $modal.find("button.do_reschedule").click(function (ev) {
            var write_vals = self.fetch_reschedule_data($modal);
            if (!write_vals)
                return false

            let ctx = Object.assign({}, self.context);
            ctx.action_origin = 'reschedule';
            self.model._rpc({
                model: self.model.modelName,
                method: 'write',
                args: [[parseInt(data.id)], write_vals],
                context: ctx
            }).then(function () {
                $modal.find(".close_btn").click();
                self.reload();
            });
        });
        $modal.show();
    },
    fetch_reschedule_data: function ($el) {
        var result = {};
        var target_date = $el.find("input.target_date").val();
        var target_from = $el.find("select.target_time_from").val();
        var target_to = $el.find("select.target_time_to").val();

        let opt = {
            target_date: target_date,
            target_from: target_from,
            target_to: target_to,
        };
        let form_data = this._validateReschedule(opt, $el);
        if (form_data == false)
            return false

        result[this.mapping.date_start] = form_data.target_date_from;
        result[this.mapping.date_stop] = form_data.target_date_to;

        return result;
    },

    _validateReschedule: function (options, $el) {
        $el.find("input.target_date").css("border-color", "unset");
        $el.find("div.select2-container.target_time_from .select2-choice").css("border-color", "unset");
        $el.find("div.select2-container.target_time_to .select2-choice").css("border-color", "unset");
        var result = true;
        if (!options.target_date) {
            result = false;
            $el.find("input.target_date").css("border", "1px solid red");
        }
        if (!options.target_from) {
            result = false;
            $el.find("div.select2-container.target_time_from .select2-choice").css("border", "1px solid red");
        }
        if (!options.target_to) {
            result = false;
            $el.find("div.select2-container.target_time_to .select2-choice").css("border", "1px solid red");
        }

        if (result) {
            let target_date = moment(new Date(options.target_date));
            var target_date_from = target_date.clone();
            var target_date_to = target_date.clone();
            target_date_from.set({
                'hour': parseInt(options.target_from.split(':')[0]),
                'minute': parseInt(options.target_from.split(':')[1])
            });
            target_date_to.set({
                'hour': parseInt(options.target_to.split(':')[0]),
                'minute': parseInt(options.target_to.split(':')[1])
            });

            if (target_date_from >= target_date_to) {
                result = false;
                $el.find("div.select2-container.target_time_from .select2-choice").css("border", "1px solid red");
                $el.find("div.select2-container.target_time_to .select2-choice").css("border", "1px solid red");
            }
            else {
                result = {
                    target_date_from: target_date_from,
                    target_date_to: target_date_to,
                }
            }
        }
        return result;
    },
    */
    /**
     * The internal state of the calendar (mode, period displayed) has changed,
     * so update the control panel buttons and breadcrumbs accordingly.
     *
     * @param {OdooEvent} event
     */
    _onViewUpdated: function (event) {
        this.mode = event.data.mode;
        if (this.$buttons) {
            this.$buttons.find('.active').removeClass('active');
            this.$buttons.find('.o_calendar_button_' + this.mode).addClass('active');
        }
        var subtitle = (this.mode === 'week' ? _t('Week ') : '') + event.data.title;
        this.set({title: this.displayName + ' (' + subtitle + ')'});
    },
    reloadCalendarDoctor: function (event) {
        this._reloadDoctor(event);
    },
    reloadCalendarState: function (event) {
        this.model.data.state_domain = ['state', 'in', Object.values(event.data)];
        this.reload();
    },
    resizeSlot: function (event) {
        this.renderer.resize_slot();
    },
    showWarning: function (event) {
        this.notification_manager.do_warn(
            "Permission Denied",
            _t(event.data.message)
        );
    },
    find_fc_options: function () {
        var self = this;
        var renderer = this.renderer;
        return $.extend({}, renderer.getCalendarOptions());
        /*return $.extend({}, renderer.state.fc_options, {
            defaultView: 'agendaDay',
            schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
            resources: [],
            snapMinutes: renderer.other_options.snap_minutes,
            slotDuration: renderer.other_options.slot_duration,
            slotLabelInterval: renderer.other_options.slot_duration,
            selectConstraint: 'businessHours',
            selectConstraintType: 'nonBusinessHours',
            unknownResourceTitle: 'Others',
            minTime: n2(renderer.time_schedule.schedule_start),
            maxTime: n2(renderer.time_schedule.schedule_end),
            eventDrop: function (event, _delta, _revertFunc) {
               //_day_delta, _minute_delta, _all_day, _revertFunc) {
               if (!confirm("Are you sure about this change?")) {
                   _revertFunc();
               } else {
                   self.renderer.trigger_up('dropRecord', event);
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
            eventClick: function (event) {
               renderer.remove_tooltip($el);
               event.is_rendered = false;
               renderer.trigger_up('openEvent', event);
               renderer.$calendar.fullCalendar2('unselect');
            },
            select: function (target_date, end_date, event, _js_event, _view) {
                var data = {
                   'start': target_date,
                   'end': end_date,
                   'resourceId': _view.id
                };
                if (renderer.state.context.default_name) {
                   data.title = renderer.state.context.default_name;
                }
                renderer.trigger_up('openCreate', data);
                renderer.$calendar.fullCalendar2('unselect');
            },
            eventRender: function (event, element) {
               var $render = $(renderer._eventRender(event));
               event.title = $render.find('.o_field_type_char:first').text();

               var doctor_user = $render.find('.o_field_doctor_user').text().trim();
               if (doctor_user == 'True') {
                   $render.find('.o_field_doctor_user').text('');
                   $render.find('.o_field_patient_name_phone').text('');
               }
               else {
                   $render.find('.o_field_doctor_user').text('');
                   $render.find('.o_field_patient_name').text('');
               }

               element.find('.fc-content').html($render.html());
               element.addClass($render.attr('class'));
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
               if (event && event.record && event.record.has_insurance == true)
                    element.find('.fc-content').prepend(
                        QWeb.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/insurance.jpeg'
                        }));
               if (event && event.record && event.record.is_child == true)
                    element.find('.fc-content').prepend(
                        QWeb.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/child.jpeg'
                        }));
               if (event && event.record && event.record.frequent_cancel == true)
                    element.find('.fc-content').prepend(
                        QWeb.render('calendar_scheduler.patient_icon', {
                            custom_class: 'source_sch_evt',
                            icon_url: '/calendar_scheduler/static/src/img/cancelled.jpeg'
                        }));

               if (event && event.record && event.record.is_vip == true)
                    element.find('.fc-content').prepend(
                        '<div class="ribbon_div"><i class="fa fa-star checked" style="color:#39968a;background-color: white;"/>' +
                        '<i class="fa fa-star checked" style="color:#39968a;background-color: white;"/>' +
                        '<i class="fa fa-star checked" style="color:#39968a;background-color: white;"/></div>');
               element.find('.fc-content .fc-time').text(display_hour);
            },
            // Dirty hack to ensure a correct first render
            eventAfterAllRender: function () {
               $(window).trigger('resize');
            },
            viewRender: function (view) {
               // compute mode from view.name which is either 'month', 'agendaWeek' or 'agendaDay'
               var mode = view.name === 'month' ? 'month' : (view.name === 'agendaWeek' ? 'week' : 'agendaDay');
               // compute title: in week mode, display the week number
               var title = mode === 'week' ? view.intervalStart.week() : view.title;
               renderer.trigger_up('viewUpdated', {
                   mode: mode,
                   title: title,
               });
            },
            eventAfterRender: function( event, element, view ) {
                event.is_rendered = true;
            },
            eventMouseout: function( event, jsEvent, view ) {
                var $el = $(jsEvent.currentTarget);
                renderer.remove_tooltip($el);
            },
            eventMouseover: function( event, jsEvent, view ) {
                var $el = $(jsEvent.currentTarget);
                renderer._addTooltip(event, $el);
                $el.trigger('mouseover');
            },
            stateCtrl: function (ev1, ev2) {
                return renderer.setup_state_control(ev1, ev2);
            },
            height: 'parent',
            unselectAuto: false,
       });*/
    },
    _reloadDoctor: function (event) {
        var self = this;

		var filtered_resources = event.data.doctors ? event.data.doctors : [];
		filtered_resources = filtered_resources.concat(
			event.data.rooms ? event.data.rooms : []);

		var filter_option = event.data.doctor_ids ? event.data.doctor_ids : [];
		filter_option = filter_option.concat(
			event.data.room_ids ? event.data.room_ids : []);

		this._doUpdateCalendar(event, filtered_resources, filter_option);
    },
    _doUpdateCalendar: function (event, filtered_resources, filter_option) {
        this.renderer.resources = filtered_resources;
        this.renderer.$calendar.fullCalendar2('refetchResources');
    },
   /* _doUpdateCalendar: function (event, filtered_resources, filter_option) {
        var old_date = this.renderer.$calendar.fullCalendar2('getDate');

        this.renderer.$calendar.fullCalendar2('destroy');

        var fc_options = this.find_fc_options();
        fc_options.resources = filtered_resources;

        this.renderer.$calendar.fullCalendar2(fc_options);
        this.renderer.resize_slot();
//        this.model._loadCalendar();
        this.renderer.$calendar.fullCalendar2('removeEvents');
        var filter_options = {
            resource: filter_option
        };

        var filtered_events = this.filter_events(
            this.renderer.state.data,
            filter_options);
        this.renderer.$calendar.fullCalendar2(
            'gotoDate', old_date);
        this.renderer.$calendar.fullCalendar2(
            'addEventSource', filtered_events);
    },*/
    filter_events: function (ev_data, options) {
        var filtered_events = [], to_remove;
        for (var i in ev_data) {
            to_remove = true;
            if (options.resource && options.resource.includes(ev_data[i].resourceId)) {
                to_remove = false;
            }

            if (to_remove == false) {
                filtered_events.push(ev_data[i]);
            }
        }
        return filtered_events;
    },
    reloadPatients: function () {
        var self = this;
        this._rpc({
            model: 'medical.patient',
            method: 'fetch_patients',
        }).then(function (patients) {
            self.renderer.patients = {};
            self.renderer.phone_no = [];
            self.renderer.qid = [];
            self.renderer.pat_names = [];
            self.renderer.pat_ids = [];

            $.each(patients, function(p) {
                self.renderer.patients[patients[p]['id']] = patients[p];
                if(patients[p]['mobile']){
                    self.renderer.phone_no.push(
                        {label:patients[p]['mobile'], value:patients[p]['id']});
                }
                if(patients[p]['qid']){
                    self.renderer.qid.push(
                        {label:patients[p]['qid'], value:patients[p]['id']});
                }
                self.renderer.pat_ids.push(
                    {label:patients[p]['patient_id'], value:patients[p]['id']});
                self.renderer.pat_names.push(
                    {label:patients[p]['name'], value:patients[p]['id']});
            });
        });
    },
});

return CalendarController2;

});
