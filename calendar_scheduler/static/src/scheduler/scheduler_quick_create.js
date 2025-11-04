odoo.define('calendar_scheduler.CalendarQuickCreate2', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var rpc = require('web.rpc');
var session = require('web.session');
var _t = core._t;
var QWeb = core.qweb;

function dateToServer (date) {
    return date.clone().utc().locale('en').format('YYYY-MM-DD HH:mm:ss');
}

function verifyPhoneNumber(number, min, max) {
    min = min ? min : 8;
    max = max ? max : 8;
    let reg_exp = "^[0-9]{" + min + "," + max + "}$";
    var validity = new RegExp(reg_exp);
    return validity.test(number);
}

/**
 * Quick creation view.
 *
 * Triggers a single event "added" with a single parameter "name", which is the
 * name entered by the user
 *
 * @class
 * @type {*}
 */
var QuickCreate3 = Dialog.extend({
	init: function (parent, options) {
		this.parent = parent;

        this._super(parent, {
            title: "Patient Selection",
            size: 'smaller',
            buttons: [{text: _t("Cancel"),
                       close: true, click: function () {
                        parent.clearAll();
                     }}
            ],
            $content: QWeb.render('CalendarView2.pat_list_wiz', {
                options: options,
            })
        });
    },
    start: function () {
        this._super();
    }
});

var QuickCreate2 = Dialog.extend({
    events: _.extend({}, Dialog.events, {
        'keyup input': '_onkeyup',
        'change .break_time': 'change_break_time',
        'change .patient_type': 'change_patient_type',
        'change .followup_app': 'onchange_followup_app',
        'change .modal_start_time': 'get_followup_app_start',
        'change .modal_end_time': 'onchange_app_end',
        'change select.staff': 'get_followup_modalPhysician',
//        'change .dob': 'onchange_dob',
    }),

    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} buttons
     * @param {Object} options
     * @param {Object} dataTemplate
     * @param {Object} dataCalendar
     */
    init: function (parent, buttons, options, dataTemplate, dataCalendar) {
        this._buttons = buttons || false;
        this.options = options;

        // Can hold data pre-set from where you clicked on agenda
        this.dataTemplate = dataTemplate || {};
        this.dataCalendar = dataCalendar;

        var self = this;

		function n(n){
            return n > 9 ? "" + n: "0" + n;
        }
		options.time_slots = parent.renderer.time_slots;

		options.start = n(dataCalendar.start.hour()) + ':' + n(dataCalendar.start.minutes());
		options.end = n(dataCalendar.end.hour()) + ':' + n(dataCalendar.end.minutes());

        this.other_options = parent.renderer.other_options ? parent.renderer.other_options : {
            max_length: 8,
            show_country_code: true
        };

		options.nationality_ids = parent.renderer.nationality_ids;
		options.staff = parent.renderer.doctors;
		options.rooms = parent.renderer.rooms_list;

		var resource_vals = dataCalendar.resourceId ? dataCalendar.resourceId.split('_') : [false];
		if (resource_vals[0] == 'doctor') {
            options.doctor = dataCalendar.resourceId;
            options.room_id = false;
            let d_map = this.other_options.doctor_map || {};

            let tmp = d_map[parseInt(resource_vals[1])];
            if (tmp) {
                options.rooms = [];
                options.rooms = _.filter(parent.renderer.rooms_list, function (r) {
                    return tmp.includes(r._id);
                });
            }
        } else if (resource_vals[0] == 'room') {
            let r_map = this.other_options.room_map || {};
            options.room_id = dataCalendar.resourceId;
            options.doctor = false;

            let tmp = r_map[parseInt(resource_vals[1])];
            if (tmp) {
                options.staff = [];
                options.staff = _.filter(parent.renderer.doctors, function (s) {
                    return tmp.includes(s._id);
                });
            }
        }
        else {
            options.doctor = parseInt(dataCalendar.resourceId);
        }

		this.patients = parent.renderer.patients ? parent.renderer.patients : [];
        this.phone_no = parent.renderer.phone_no ? parent.renderer.phone_no : [];
        this.qid = parent.renderer.qid ? parent.renderer.qid : [];
        this.pat_names = parent.renderer.pat_names ? parent.renderer.pat_names : [];
        this.pat_ids = parent.renderer.pat_ids ? parent.renderer.pat_ids : [];

        var patients = parent.renderer.patients ? parent.renderer.patients : {};
		var self = this;

        this._super(parent, {
            title: this._getTitle(),
            size: 'large',
            buttons: this._buttons ? [
                {text: _t("Create"),
                 classes: 'btn-primary scheduler_create',
                  click: function () {
                    if (!self._quickAdd(dataCalendar)) {
                        self.focus();
                    }
                }},{text: _t("Clear"),
                 classes: 'scheduler_edit',
                  click: function () {
                    self.clearAll();
                }},
//                {text: _t("Edit"),
//                 classes: 'scheduler_edit',
//                 click: function () {
//                    dataCalendar.disableQuickCreate = true;
//                    dataCalendar.title = self.$('input').val().trim();
//                    dataCalendar.on_save = self.destroy.bind(self);
//                    self.trigger_up('openCreate', dataCalendar);
//                }},
                {text: _t("Cancel"),
                 classes: 'scheduler_cancel',
                 close: true},
            ] : [],
            $content: QWeb.render('CalendarView2.quick_create', {
                widget: this,
                options: options
            })
        });
    },
    start: function () {
        this._super();
		var self = this;
		self.pat_list_all = [];
		self.pat_list = [];
		self.search_status = "";
        function split(val) {
            return val.split(/,\s*/);
        }
        function extractLast(term) {
            return split(term).pop();
        }

        var phone_numbers = this.other_options.phone_number;
        let default_phone = this.get_default_phone();
        this.$input = this.$('input').keydown(function enterHandler (e) {
            $(".phone_note").addClass("o_hidden");
            $('.patient_phone').css('border-color', 'unset');
            if ($(this).hasClass('patient_phone') &&
                    $('input.patient_type').prop("checked") != true) {
                var x = e.which || e.keycode;
                var length = $(this).val().length;
                var length_valid = length < (phone_numbers.max_length + default_phone.length) ? true : false;
                var number_only = (length_valid && x >= 48 && x <= 57) || (length_valid && x >= 96 && x <= 105)
                                    || x == 8 || (x >= 35 && x <= 40) || x == 46;
                var length_valid = length < (phone_numbers.max_length + default_phone.length) ? true : false;
                if (number_only)
                    return true;
                else
                    e.preventDefault();
            }

            self.search_status = "pending";
        });

        this.$input = this.$('input').on('textInput', e => {
            var keycode  = e.originalEvent.data.charCodeAt(0);
            self.search_status = "pending";
            var currentTarget = $(e.currentTarget);

            if (keycode === $.ui.keyCode.SPACE && $('input.patient_type').prop("checked") == true) {
                self.search_status = '';
                switch (currentTarget.attr('class')) {
                    case 'patient_phone': self.keydown_phone(); break;
                    case 'patient_name': self.keydown_name(); break;
                    case 'qid': self.keydown_qid(); break;
                    case 'patient_ids': self.keydown_patient_ids(); break;
                    default: break;
                };
            }
        });
        this.$input.on('change', function enterHandler (e) {
            if ($('input.patient_type').prop("checked") == true &&
                    self.search_status == 'pending') {
                self.search_status = "";
                switch ($(this).attr('class')) {
                    case 'patient_phone': self.keydown_phone(); break;
                    case 'patient_name': self.keydown_name(); break;
                    case 'qid': self.keydown_qid(); break;
                    case 'patient_ids': self.keydown_patient_ids(); break;
                    default: break;
                };
            }
            if ($(this).hasClass('patient_phone') &&
                    $('input.patient_type').prop("checked") != true) {
                self.validate_phone_number($(this).val());
            }
        });
        this.$('.staff,.patient_stat, select.room_id, select.nationality_id').select2({
            placeholder: 'Select',
			allowClear: true
        });
        this.$(".dob").datepicker();
        this.$('input.patient_phone').val(default_phone);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    get_default_phone: function () {
        return this.other_options.phone_number.show_country_code ? '974' : '';
    },
    validate_phone_number: function (val) {
        if (!val)
            return
        let opt = this.other_options.phone_number;
        let ph_valid = verifyPhoneNumber(val, opt.max_length, opt.max_length);
        if (!ph_valid) {
            let $el = this.$('input.patient_phone');
            $el.css('border', '1px solid red');
            let msg_valid_msg = "Invalid phone number: need " + opt.max_length + " digits.";
            $(".phone_note").text(msg_valid_msg);
            $(".phone_note").removeClass("o_hidden");
        }
    },
    /*check whether minimum length validation needed for
    phone number search or not*/
    check_phone_validation: function (val) {
        let opt = this.other_options.phone_number;
        if (!opt.validate_phone)
            return true

        let ph_valid = verifyPhoneNumber(val, opt.phone_min_length, 20);
        if (!ph_valid) {
            let $el = this.$('input.patient_phone');
            $el.css('border', '1px solid red');
            let msg_valid_msg = "Invalid phone number: need " + opt.phone_min_length + " digits.";
            $(".phone_note").text(msg_valid_msg);
            $(".phone_note").removeClass("o_hidden");
            return false
        }
        return true
    },
    clearAll: function () {
        this._removeRibbonVip();
        this._removeInsuranceIcon();
        this._removeChildIcon();
        this._removeCancelIcon();
        this.hideDueAmount();
        this.hideAdvanceAmount();
        $(".phone_note").addClass("o_hidden");
        this.$("input,textarea").val('');
        this.$("select.gender").val('');
        this.$("select.nationality_id").val('');
        this.$("select.nationality_id").trigger('change');
        this.$("select.room_id").val('');
        this.$("select.room_id").trigger('change');
        this.$("input.urgent_app").removeAttr('checked');
        this.$("input.followup_app").removeAttr('checked');
        this.patient_rec = false;
    },
    focus: function () {
        this.$('.patient_name').focus();
    },
    keydown_phone: function () {
        this.autocomplete_method(
            '.patient_phone',
            'mobile'
        );
    },
    keydown_name: function () {
        this.autocomplete_method(
            '.patient_name',
            'patient_name'
        );
    },
    keydown_qid: function () {
        this.autocomplete_method(
            '.qid',
            'qid'
        );
    },
    keydown_patient_ids: function () {
        this.autocomplete_method(
            '.patient_ids',
            'pat_ids'
        );
    },
    onchange_dob: function () {
        if ($('input.patient_type').prop("checked") == true) {
            $('.dob').val((this.patient_rec ? this.patient_rec.dob : '' ));
        }
    },
    patient_by_file: function(patient){
//        var patient = this.patients[p_id];
        $('.patient_list').val(patient.id);
        $('.patient_name').val(patient.name ? patient.name : patient.patient_name);
        $('.qid').val(patient.qid ? patient.qid : null);
        $('.patient_phone').val(patient.mobile ? patient.mobile: null);
        $('.patient_ids').val(patient.patient_id);
        $('select.gender').val(patient.sex);
//        $('select.gender').trigger('change');
        $('.dob').val(patient.dob ? patient.dob : '');
        $('select.nationality_id').val('');
        $('select.nationality_id').val(patient.nationality_id ? patient.nationality_id[0] : '');
        $('select.nationality_id').trigger('change');
        this.patient_rec = patient;
        $('select.gender').attr('disabled', true);
        $('select.nationality_id').attr('disabled', true);

        /*Adding a ribbon to indicate vip customers*/
        if (patient && patient.is_vip) {
            this._addRibbonVip();
        }
        else {
            this._removeRibbonVip();
        }
        /*add insurance patient icon*/
        if (patient && patient.has_insurance) {
            this._addInsuranceIcon();
        }
        else {
            this._removeInsuranceIcon();
        }

        if (patient && patient.is_child) {
            this._addChildIcon();
        }
        else {
            this._removeChildIcon();
        }

        if (patient && patient.frequent_cancel) {
            this._addCancelIcon();
        }
        else {
            this._removeCancelIcon();
        }
//        $('.dob').attr('readonly', true);
        this.onChangeCustomer(patient);
    },
    onChangeCustomer: function (patient) {
        /*expanded in other modules*/
        if (parseFloat(patient.amount_due) > 0) {
            this.showDueAmount(patient.amount_due);
        }
        else
            this.hideDueAmount();
        if (parseFloat(patient.amount_advance) > 0) {
            this.showAdvanceAmount(patient.amount_advance);
        }
        else
            this.hideAdvanceAmount();
        return $.Deferred();
    },
    _removeRibbonVip: function () {
        var $ribbon = this.$el.find('.ribbon');
        $ribbon.length > 0 ? $ribbon.remove() : null;
    },
    _addRibbonVip: function () {
        this._removeRibbonVip();
        var ribbon = QWeb.render('calendar_scheduler.ribbon', {
           widget: {
               text: "VIP Patient",
               bgColor: 'bg-lightgreen',
               show_stars: true,
               custom_class: 'appt_create_ribbon'
           }
        });
        this.$el.prepend(ribbon);
    },

    _removeInsuranceIcon: function () {
        var $ins = this.$el.find('div.insurance_icon_img');
        $ins.length > 0 ? $ins.remove() : null;
    },
    _addInsuranceIcon: function () {
        this._removeInsuranceIcon();
        var $ins = QWeb.render('calendar_scheduler.patient_icon', {
            custom_class: 'source_sch_create insurance_icon_img',
            icon_url: '/calendar_scheduler/static/src/img/insurance.jpeg'
        });
        this.$el.prepend($ins);
    },
    _removeChildIcon: function () {
        var $ins = this.$el.find('div.child_icon_img');
        $ins.length > 0 ? $ins.remove() : null;
    },
    _addChildIcon: function () {
        this._removeChildIcon();
        var $ins = QWeb.render('calendar_scheduler.patient_icon', {
            custom_class: 'source_sch_create child_icon_img',
            icon_url: '/calendar_scheduler/static/src/img/child.jpeg'
        });
        this.$el.prepend($ins);
    },
    _removeCancelIcon: function () {
        var $ins = this.$el.find('div.cancel_icon_img');
        $ins.length > 0 ? $ins.remove() : null;
    },
    _addCancelIcon: function () {
        this._removeCancelIcon();
        var $ins = QWeb.render('calendar_scheduler.patient_icon', {
            custom_class: 'source_sch_create cancel_icon_img',
            icon_url: '/calendar_scheduler/static/src/img/cancelled.jpeg'
        });
        this.$el.prepend($ins);
    },
    hideDueAmount: function () {
        this.$("p.amount_due_p").remove();
    },
    showDueAmount: function (amount) {
        this.hideDueAmount();
        let amount_el = $("<span class='amount_due_p'><strong>Due Amount:</strong> " + amount + "</span>");
        this.$el.prepend(amount_el);
        this.$el.prepend(amount_el);
    },
    hideAdvanceAmount: function () {
        this.$("p.amount_advance_p").remove();
    },
    showAdvanceAmount: function (amount) {
        this.hideAdvanceAmount();
        let amount_el = $("<span class='amount_advance_p'><b>Advance Amount:</b> " + amount + "</span>");
        this.$el.prepend(amount_el);
        this.$el.prepend(amount_el);
    },
    /*onchange_patient: function(p_id){
        var patient = this.patients[p_id];
        $('.patient_list').val(patient.id);
        $('.patient_name').val(patient.name);
        $('.qid').val(patient.qid);
        $('.patient_phone').val(patient.mobile);
        $('.patient_ids').val(patient.patient_id);
        $('select.gender').val(patient.sex);
//        $('select.gender').trigger('change');
        $('.dob').val(patient.dob);
        $('select.nationality_id').val('');
        $('select.nationality_id').val(patient.nationality_id);
        $('select.nationality_id').trigger('change');
        this.patient_rec = patient;
        $('select.gender').attr('disabled', true);
        $('select.nationality_id').attr('disabled', true);
//        $('.dob').attr('readonly', true);
    },*/

    fetch_patient_fields: function () {
        return [
            'patient_name', 'id', 'qid', 'mobile',
            'patient_id', 'sex', 'dob',
            'nationality_id', 'is_vip', 'amount_due', 'amount_advance',
            'has_insurance', 'is_child', 'frequent_cancel'
        ];
    },
    autocomplete_method: function (selector, key) {
        var self = this;

        function split(val) {
            return val.split(/,\s*/);
        }

        var fields_here = this.fetch_patient_fields();
        if (key == 'pat_ids') {
            var search_val = $(selector).val().trim();
            rpc.query({
                   model: 'calender.config',
                   method: 'search_patient_prefix',
                    args: [search_val]
                }).then(function(res) {
                    var patient_prefix = res[0];
                    var search_vals = res[1];
                    var domain_here = [['patient_id', 'in', search_vals], ['company_id','=', session.company_id]];
                    return rpc.query({
                            model: 'medical.patient',
                            method: 'search_patient_read',
                            args: [domain_here, fields_here]
                        }).then(function (result) {

                            if (result.length > 0) {
                                self.patient_by_file(result[0]);
                                $(selector).css('border', '1px solid #aaa');
                                $('.qid').css('border', '1px solid #aaa');
                                $('.patient_name').css('border', '1px solid #aaa');
                                $('.patient_phone').css('border', '1px solid #aaa');
                            }
                            else {
                                $(selector).val('');
                                $(selector).css('border', '1px solid red');
                                self.clearAll();
                            }
                    });
                    });
        }
        else if (key == 'patient_name') {
            var search_val = $(selector).val().trim();
            $(selector).val(search_val);

            self.pat_list = [];
            self.pat_list_all = [];
            $(selector).autocomplete({
                select: function (event, ui) {
                    var terms = split(this.value);
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.label);
                    this.value = terms;

                    var patient = null;
                    if (self.pat_list_all[ui.item.value - 1]) {
	                    self.patient_by_file(self.pat_list_all[ui.item.value - 1]);
	                    patient = self.pat_list_all[ui.item.value - 1].id;
	                    $(this).css('border', '1px solid #aaa');
	                    $(selector).autocomplete('destroy');
                    }

                    var doctor_id = $('select.staff').val() ? parseInt($('select.staff').val().split('_')[1]) : false;
                    if (doctor_id == false) {
                        alert("Select a doctor first !");
                        return;
                    }
                    self.followup_function(patient,
                                           self.dataCalendar.start,
                                           doctor_id,
                                           'New')
					self.pat_list_all = [];
					self.pat_list = [];
					search_val = false;
//
                    return false;
                },
                source: function (request, response) {
                    self.pat_list = [];
                    var domain_here = [[key, 'ilike', search_val], ['company_id','=', session.company_id]];
                    rpc.query({
                        model: 'medical.patient',
                        method: 'search_patient_read',
                        args: [domain_here, fields_here]
                    }).then(function (result) {
                        if (result) {
                            self.pat_list_all = result;
                            for (var p=0;p<result.length;p++) {
                                self.pat_list.push(
                                    {label:result[p][key], value:p+1});
                            }

                            response(self.pat_list);
                        }
                        else {
                            $(selector).val('');
                            $(selector).css('border', '1px solid red');
                            self.clearAll();
                        }
                    });
                },
                change: function (event, ui) {
                    if (ui.item) {
                        $(this).css('border', '1px solid black');
                    }
                    else {
                        $(this).val('');
                        $(this).css('border', '1px solid red');
                        self.clearAll();
                    }
                    $(selector).autocomplete('destroy');
                }
            });
        }
        else {
            /*case for phone number, qid
            i.e, there may be multiple records with same value*/
            /*check for minimum length validation before calling search_read*/
            var search_val = $(selector).val().trim(), s_op = 'ilike';
            if (key == 'mobile') {
                if (!this.check_phone_validation(search_val))
                    return
                s_op = '=';
                if (this.other_options.phone_number.validate_phone)
                    s_op = 'ilike';
            }

            var domain_here = [[key, 'ilike', search_val], ['company_id','=', session.company_id]];
            rpc.query({
                model: 'medical.patient',
                method: 'search_patient_read',
                args: [domain_here, fields_here]
            }).then(function (result) {
                result = self._process_patient_list(result, s_op, search_val, key);
                if (result.length > 1) {
                    var quick = new QuickCreate3(self, result);
                    quick.open();
                    quick.$modal.find('button.close').css('right', '20px');
                    quick.$modal.find('button.close').click(function () {
                        self.clearAll();
                    });
                    $('.patient_body tr').click(function () {
                        var p_selected = $(this).attr('id') ? parseInt($(this).attr('id')) : false;
                        if (!p_selected) {return;}
                        self.patient_by_file(result[p_selected - 1]);
                        $(selector).css('border', '1px solid #aaa');
                        $('.qid').css('border', '1px solid #aaa');
                        $('.patient_name').css('border', '1px solid #aaa');
                        $('.patient_phone').css('border', '1px solid #aaa');
                        quick.close();
                    });
                }
                else if (result.length == 1) {
                    self.patient_by_file(result[0]);
                    $(selector).css('border', '1px solid #aaa');
                    $('.qid').css('border', '1px solid #aaa');
                    $('.patient_name').css('border', '1px solid #aaa');
                    $('.patient_phone').css('border', '1px solid #aaa');
                }
                else {
                    $(selector).val('');
                    $(selector).css('border', '1px solid red');
                    self.clearAll();
                }
            });
        }



//        function split(val) {
//            return val.split(/,\s*/);
//        }
//        function extractLast(term) {
//            return split(term).pop();
//        }
        /*$(el).autocomplete({
            select: function (event, ui) {
                var terms = split(this.value);
                // remove the current input
                terms.pop();
                // add the selected item
                terms.push(ui.item.label);
                this.value = terms;
                self.onchange_patient(ui.item.value);
                var patient =  ui.item.value;
                var doctor_id = $('select.staff').val() ? parseInt($('select.staff').val().split('_')[1]) : false;
                if (doctor_id == false) {
                    alert("Select a doctor first !");
                    return;
                }
				self.followup_function(patient,
				                       self.dataCalendar.start,
				                       doctor_id,
				                       'New')
                return false;
            },
            source: function (request, response) {
                // delegate back to autocomplete, but extract the last term
                if ($('input.patient_type').prop("checked") == true) {
                    var res = $.ui.autocomplete.filter(
                        self[key], extractLast(request.term));
                    if (el== '.patient_ids' && key=='pat_ids'){
                        if(res.length==1){response(res);}
                    }
                    else{
                        response(res);
                    }
                }
                else {
                    response([]);
                }
            },
            change: function (event, ui) {
                if ($('input.patient_type').prop("checked") == true) {
	                var el_class = $(this).attr('class').replace(
	                    'ui-autocomplete-input', '');
	                el_class = el_class.trim();
	                var new_val = '';
	                if (ui.item) {
	                    new_val = ui.item.label;
	                }
	                else if (self.patient_rec) {
	                    new_val = self.findPatientData(el_class);
	                }
	                $(this).val(new_val);
                }
            }
        });*/
    },/*
    findPatientData: function (key) {
        var result = "";
        switch (key) {
            case 'patient_name': result = this.patient_rec.name; break;
            case 'patient_ids': result = this.patient_rec.patient_id; break;
            case 'patient_phone': result = this.patient_rec.mobile; break;
            case 'qid': result = this.patient_rec.qid; break;
            default: break;
        };
        return result;
    },*/
    _process_patient_list: function (patients, s_op, search_val, key) {
        if (s_op != '=')
            return patients
        return _.filter(patients, function (p) {
            return p[key] ? p[key].trim() == search_val : true;
        });
    },
    get_followup_modalPhysician: function () {
        var doctor_id = $('select.staff').val() ? parseInt($('select.staff').val().split('_')[1]) : false;
        if (doctor_id == false) {
	        alert("Select a doctor first !");
            return;
        }
        var patient =  $('.patient_list').val();
        this.followup_function(patient,
                               this.dataCalendar.start,
                               doctor_id,
                               'New')
	},
    onchange_app_end: function () {
        this.dataCalendar.end.set({
            'hour': parseInt($('.modal_end_time').val().split(':')[0]),
            'minute': parseInt($('.modal_end_time').val().split(':')[1])
        });
    },
    get_followup_app_start: function () {
        var appointment_sdate =  $('.modal_start_time').val();
        this.dataCalendar.start.set({
            'hour': parseInt(appointment_sdate.split(':')[0]),
            'minutes': parseInt(appointment_sdate.split(':')[1])
        });
        this.dataCalendar.end.set({
            'hour': parseInt(appointment_sdate.split(':')[0]),
            'minutes': parseInt(appointment_sdate.split(':')[1])
        });
        this.dataCalendar.end.add(15, 'minutes');

        var end_date = this.dataCalendar.end.format('HH:mm');
        $('.modal_end_time').val(end_date);

        var patient =  $('.patient_list').val();

		var doctor_id = $('select.staff').val() ? parseInt($('select.staff').val().split('_')[1]) : false;
        if (doctor_id == false) {
            alert("Select a doctor first !");
            return;
        }
        this.followup_function(patient,
                               this.dataCalendar.start,
                               doctor_id,
                               'New')
    },
    onchange_followup_app: function () {
        if($(".followup_app").prop("checked")== true){
            $('.followup_app').prop('checked',false);
            alert("You cant make this Appointment Followup");
        }

    },
    change_break_time: function () {
        var break_time = $('input.break_time').prop("checked");
        var $break_type = $(".break_type_div");
        if (break_time) {
            $break_type.show();
            rpc.query({
                model: 'break.type',
                method: 'search_read',
                fields: ['name', 'color', 'id'],
                domain: []
            }).then(function (res) {
                let bt = "<option value=''/>";
                for (var i=0;i<res.length;i++) {
                    bt += "<option value='" + res[i].id + "'>" + res[i].name + "</option>"
                }
                $break_type.find("select.break_type_id").html(bt);
            });
        }
        else
            $break_type.hide();
    },
    change_patient_type: function () {
        this._removeRibbonVip();
        this._removeInsuranceIcon();
        this._removeChildIcon();
        this._removeCancelIcon();
        this.hideDueAmount();
        this.hideAdvanceAmount();
        var checked = $('input.patient_type').prop("checked");
        let default_phone = this.get_default_phone();
        $(".phone_note").addClass("o_hidden");
        if (checked == true) {
            $('.box.patient').css('visibility', 'visible');
            $('.patient_ids').val('');
            $('.patient_name').val('');
            $('.patient_list').val('');
            $('.patient_phone').val(default_phone);
            $('.qid').val('');
            $('.dob').val('');
            $('select.nationality_id').val('');
            $('select.nationality_id').trigger('change');
            $('select.gender').val('');

//            $('select.gender').trigger('change');

			$('select.gender').attr('disabled', true);
			$('select.nationality_id').attr('disabled', true);
			this.patient_rec = null;
//			$('.dob').attr('readonly', true);
//			$('.patient_phone').attr('readonly', true);
//			$('.qid').attr('readonly', true);
//			$('select.nationality_id').attr('readonly', true);
//			$('select.gender').attr('readonly', true);
        }
        else{
            $('.patient_ids').val('');
            $('.patient_name').val('');
            $('.patient_list').val('');
            $('.patient_phone').val(default_phone);
            $('.qid').val('');
            $('.dob').val('');
            $('select.nationality_id').val('');
            $('select.nationality_id').trigger('change');
            $('select.gender').val('');
//            $('select.gender').trigger('change');
            $('.box.patient').css('visibility', 'hidden');

			$('select.gender').attr('disabled', false);
            $('select.nationality_id').attr('disabled', false);
            $('.dob').attr('readonly', false);
            this.patient_rec = null;
//            $('.patient_ids').attr('readonly', false);
//            $('.patient_phone').attr('readonly', false);
//            $('.qid').attr('readonly', false);
//            $('select.nationality_id').attr('readonly', false);
//            $('select.gender').attr('readonly', false);
        }
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

	followup_function: function(patient, appointment_sdate, doctor, name){
		var new_date = dateToServer(appointment_sdate);

        rpc.query({
            model: 'medical.appointment',
            method: 'funct_followup',
            args: [patient, patient, new_date, doctor, name],
        })
        .then(function(follow_up_expired) {
            var is_follow_up = follow_up_expired[0]
            var is_expired_up = follow_up_expired[1]
            if (is_follow_up == 1){
                $(".followup_app").prop("checked", true);
                var message = 'This can be a followup visit';
            }
            else{
                $('.followup_app').prop('checked',false);
                if (is_expired_up == 1){
                    var message = 'Followup expired';
                }
                else{
                    var message =  'This is not a followup visit';
                }
            }
//            alert(message);
        });
    },
    /**
     * @returns {string}
     */
    _getTitle: function () {
        var parent = this.getParent();
        if (_.isUndefined(parent)) {
            return _t("Mark Booking/ Visit");
        }
        var title = (_.isUndefined(parent.field_widget)) ?
                (parent.title || parent.string || parent.name) :
                (parent.field_widget.string || parent.field_widget.name || '');
        return _t("Mark Booking/ Visit: ") + title;
    },
    get_create_vals: function (dataCalendar) {
        var doctor_id = $('select.staff').val() ? parseInt($('select.staff').val().split('_')[1]) : false;
        var room_data = $('select.room_id').val() ? parseInt($('select.room_id').val().split('_')[1]) : false;
        if (! room_data){
            var room_data = $('select.room_id').val();
        }
        var break_time = $('input.break_time').prop("checked"), break_type_id = $('select.break_type_id').val();
        return {
            break_time : break_time,
            break_type_id : break_time && break_type_id ? parseInt(break_type_id) : null,
            is_registered : $('input.patient_type').prop("checked"),
            appointment_sdate: dataCalendar.start.clone(),
            appointment_edate: dataCalendar.end.clone(),
            patient_name: break_type_id ? $("select.break_type_id option:selected").text() : $('.patient_name').val(),
            patient_state: $('select.patient_stat').val(),
            patient_phone: $('.patient_phone').val(),
            sex: $('select.gender').val(),
            dob: $('.dob').val() ? $('.dob').val() : false,
            nationality_id: $('select.nationality_id').val(),
            qid: $('.qid').val(),
            doctor: doctor_id ? doctor_id : null,
            room_id: room_data ? room_data : null,
            urgency: $('.urgent_app').prop("checked"),
            followup: $('.followup_app').prop("checked"),
            comments: $('input.notes').val(),
        }
    },
    /**
     * Gathers data from the quick create dialog a launch quick_create(data) method
     */
    _quickAdd: function (dataCalendar) {
        if (dataCalendar.start >= dataCalendar.end) {
            alert("Appointment start time should be before end time.")
            return false;
        }
        dataCalendar = $.extend({}, this.dataTemplate, dataCalendar);

		var self = this, patient = false;
        var break_time = $('input.break_time').prop("checked");
        if ($('input.patient_type').prop("checked") == true) {
            patient = parseInt($('.patient_list').val());
        }

        var vals = this.get_create_vals(dataCalendar);
        if (!break_time) {
            var missing_values = false;
            if (vals['is_registered'] === false) {
                if (!vals['patient_name']) {
                    missing_values = true;
                    $('.patient_name').css('border-color', 'red');
                }
            }
            else {
                if (patient) {
                    vals['patient'] = patient;
                } else {
                    missing_values = true;
                    $('.patient_name').css('border-color', 'red');
                }
            }
            if (!vals['doctor']) {
                missing_values = true;
                $('select.staff').css('border-color', 'red');
            }

            if (!vals['patient_state']) {
                missing_values = true;
                $('select.patient_stat').css('border-color', 'red');
            }
            if(vals['dob']){
                var today = new Date();
                today.setHours(0,0,0,0);
                var strToDate = new Date(vals['dob']);
                vals['dob'] = strToDate;
                if ( today < strToDate){
                    missing_values = true
                    alert("Enter A Valid DOB!!!")
                }
            }
        }
        if (!vals['appointment_sdate']) {
            missing_values = true;
            $('.app_start input').css('border-color', 'red');
        }
        if (missing_values === true) {
            alert("Please fill all the missing values.")
            /*$('.required_field_warning').css({
                'display': 'block'
            });*/
        }
        else {

			return (vals)? this.trigger_up('quickCreate', {
                data: dataCalendar,
                options: this.options,
                create_vals: vals
            }) : false;
        }
    },
    /**
     * @private
     * @param {keyEvent} event
     */
    _onkeyup: function (event) {
        /*the form was submitting on enter key press earlier.
        Now it wont.
        */
        if (event.keyCode === $.ui.keyCode.ESCAPE && this._buttons) {
            this.close();
        }
        /*if (this._flagEnter) {
            return;
        }
        if(event.keyCode === $.ui.keyCode.ENTER) {
            this._flagEnter = true;
            if (!this._quickAdd(this.dataCalendar)){
                this._flagEnter = false;
            }
        } else if (event.keyCode === $.ui.keyCode.ESCAPE && this._buttons) {
            this.close();
        }*/
    },
});

return QuickCreate2;

});
