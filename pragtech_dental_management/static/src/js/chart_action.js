odoo.define('pragtech_dental_management.chart_action', function(require) {
	"use strict";

	var core = require('web.core');
	var WebClient = require('web.WebClient');
	var Widget = require('web.Widget');
	var rpc = require('web.rpc');
	var session = require('web.session');
	var _t = core._t;
	var _lt = core._lt;
	var QWeb = core.qweb;
	var Class = core.Class;
    var mapkeystatus;
	//Dental Chart variables
	var operation_id = 0;
	var list_delete_line_id = new Array();
	var full_mouth_selected = 0;
	var upper_mouth_selected = 0;
	var lower_mouth_selected = 0;
	var selected_treatment = '';
	var selected_tooth = '';
	var tooth_by_part = 0;
	var tid = '';
	var toothmap_id = '';
	var toothmap_list = new Array();
	var keyList = new Array();
	var imageMapList = new Array();
	var selected_surface = new Array();

	//console.log("Selected surface   ",selected_surface)
	var is_tooth_select = false
	var selected_category = '';
	var treatment_lines = new Array();
	var full_mouth_teeth = new Array();
	var Missing_Tooth = 0;
	var NO_OF_TEETH = 32;
	var teethcount = 0;
	var user_name = '';
	var cont = true;
	var update = false;
	var action_on_teeth = new Array();
	var other_patient_history = new Array();
	var final_surfaces = new Array();
	var final_plus = new Array();
	/*CHANGED HERE*/
//	var dignosis_records = new Array();
	var dignosis_records = [];
	/*will be useful for autocomplete*/
	var dignosis_records_by_id = {};

	var self_var;
	//Tooth Number selection array list
	var Palmer;
	// create an empty array
	var Iso;
	//Chart Selection Check
	var type = '';

	//Chart Selection Check
	var type = '';
	var settings_qty_for_teeth = '';
	var chartopened = true;
	var lst_tooth = new Array();

	var colormap = [];

	function split(val) {
		return val.split(/,\s*/);
	}
	function extractLast(term) {
		return split(term).pop();
	}
	var month, day, year, hour, minute, second;
       function formatDate(d) {
       	if (typeof d != "string") {
               month = '' + (d.getMonth() + 1),
               day = '' + d.getDate(),
               year = d.getFullYear();
               if (month.length < 2) month = '0' + month;
               if (day.length < 2) day = '0' + day;

               second = '' + d.getSeconds(),
               minute = '' + d.getMinutes(),
               hour = '' + d.getHours();

               if (second.length < 2) second = '0' + second;
               if (minute.length < 2) minute = '0' + minute;
               if (hour.length < 2) hour = '0' + hour;

               var date = [year, month, day].join('-');
               var time = [hour, minute, second].join(':');
               return [date, time].join(' ');
       }
       return d
    }

	var DentalChartView = Widget.extend({
		template : "DentalChartView",
		cssLibs: [
            '/pragtech_dental_management/static/src/css/base_new.css',
            '/web/static/lib/jquery.ui/jquery-ui.css',
            '/pragtech_dental_management/static/src/css/toastr.css'
        ],
        jsLibs: [
            '/web/static/lib/jquery/jquery.js',
            '/pragtech_dental_management/static/src/js/jquery.imagemapster.js',
            '/pragtech_dental_management/static/src/js/teeth_selection.js',
            '/pragtech_dental_management/static/src/js/image_action.js',
            '/pragtech_dental_management/static/src/js/toastr.js'
        ],
        events: {
            'keyup .amount_td': 'onchange_amount'
        },
        onchange_amount: function (ev) {
            var original_amount = $(ev.currentTarget).attr('original_amount');
            var curr_val = $(ev.currentTarget).val();
            if (original_amount && curr_val) {
                if (parseInt(curr_val) > parseInt(original_amount)) {
                    alert("The amount is too large !!")
                    $(ev.currentTarget).val(original_amount);
                }
            }
        },

		init : function(parent, options) {
			this._super(parent);
			var self = this;
			operation_id = 0;
			selected_treatment = '';
			selected_tooth = '';
			full_mouth_selected = 0;
			toothmap_id = '';
			tooth_by_part = 0;
			selected_category = '';
			treatment_lines.length = 0;
			Missing_Tooth = 0;
			other_patient_history = new Array();
			/*CHANGED HERE*/
			self.get_diagnosis_records();
			NO_OF_TEETH = 32;
			user_name = '';
			cont = true;
			update = false;
            var checkVal = '';
			self.patient_id = options.params.patient_id;
			self.appointment_id = options.params.appt_id;

			self.excluded_tooth = {
			    full_mouth: [],
			    tooth_ids: {},
			    draft_ids: {},
				upper_jaw: [],
				lower_jaw: [],
			};
			// this variable is used to load all the
			// treatment lines for the patient

			self.get_user(session.partner_id);
            self.type = options.params.type;
            self.settings_qty_for_teeth = options.params.settings_qty_for_teeth;
            var settings_qty_for_teeth = options.params.settings_qty_for_teeth;
			type = self.type;
			self.insurance = options.params.insurance;
			self.doctor = options.params.doctor;
			self.initial_exam = false;
			localStorage.removeItem('initial_exam');

			$(".navbar").addClass('hidden');
			$(".o_sub_menu").addClass('hidden');
			$(".breadcrumb").addClass('hidden');
			$(".o_cp_searchview").addClass('hidden');
			$(".o_cp_left").addClass('hidden');
			$(".o_cp_right").addClass('hidden');

			if (type == 'palmer') {
				var palmer = {
					'1' : '8-1x',
					'2' : '7-1x',
					'3' : '6-1x',
					'4' : '5-1x',
					'5' : '4-1x',
					'6' : '3-1x',
					'7' : '2-1x',
					'8' : '1-1x',
					'9' : '1-2x',
					'10' : '2-2x',
					'11' : '3-2x',
					'12' : '4-2x',
					'13' : '5-2x',
					'14' : '6-2x',
					'15' : '7-2x',
					'16' : '8-2x',
					'17' : '8-3x',
					'18' : '7-3x',
					'19' : '6-3x',
					'20' : '5-3x',
					'21' : '4-3x',
					'22' : '3-3x',
					'23' : '2-3x',
					'24' : '1-3x',
					'25' : '1-4x',
					'26' : '2-4x',
					'27' : '3-4x',
					'28' : '4-4x',
					'29' : '5-4x',
					'30' : '6-4x',
					'31' : '7-4x',
					'32' : '8-4x',

				};
				Palmer = palmer;
			}

			if (type == 'iso') {
				var iso = {
					'1' : '18',
					'2' : '17',
					'3' : '16',
					'4' : '15',
					'5' : '14',
					'6' : '13',
					'7' : '12',
					'8' : '11',
					'9' : '21',
					'10' : '22',
					'11' : '23',
					'12' : '24',
					'13' : '25',
					'14' : '26',
					'15' : '27',
					'16' : '28',
					'17' : '38',
					'18' : '37',
					'19' : '36',
					'20' : '35',
					'21' : '34',
					'22' : '33',
					'23' : '32',
					'24' : '31',
					'25' : '41',
					'26' : '42',
					'27' : '43',
					'28' : '44',
					'29' : '45',
					'30' : '46',
					'31' : '47',
					'32' : '48',
				};
				Iso = iso;
				self.Iso = Iso;
			}
			$("div.charttype").hide();
            $("div.childteethchart").hide();
            $("div.teethchartadult").hide();
            $("div.mapdetails").hide();

			self.patient_history().then(function(res) {
				self.write_patient_history(self, other_patient_history);
				var cnt = 1;
				var cnt2 = 1;
				var surface2_cnt = 32;
				var tooth2_cnt = 32;
				for (var t = 1; t <= NO_OF_TEETH; t++) {
					var NS = 'http://www.w3.org/2000/svg';
					var svg = $('#svg_object')[0];

					if (cnt <= 16) {//devided teeths into 2 sections
						var path1_1 = 34.95833333333337;
						var path1_2 = 21.250000000000007;
						var path2_1 = 25.513888888888914;
						var path2_2 = 31.875000000000007;
						var path3_1 = 34.95833333333337;
						var path3_2 = 46.04166666666665;
						var path4_1 = 52.666666666666686;
						var path4_2 = 31.875000000000007;
						var path5_1 = 34.958333333333385;
						var path5_2 = 31.875000000000007;

						//var source_img = '<img class = "teeth" src = "/pragtech_dental_management/static/src/img/tooth' + t + '.png" id = ' + t + ' width = "46" height = "50"/>';
						var missing = 0;
						for (var m = 0; m < Missing_Tooth.length; m++) {
							if (t == Missing_Tooth[m]) {
								missing = 1;
								// var source_img = '<img class = "blank" src = "/pragtech_dental_management/static/src/img/images.png" id = ' + t + ' width = "46" height = "50"/>';
								var source_img = '<img class = "blank" src = "/pragtech_dental_management/static/src/img/tooth' + t + '.png" id = ' + t + ' width = "46" height = "50" style="visibility:hidden"/>';
							}
						}

					//	$("#teeth-surface-1").append(source_img);
						if (cnt == 1) {//hardcode first rectangular coordinates

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view buccal " + cnt + '_buccal 0');
							newElement.setAttribute("id", "view_" + cnt + "_top");

							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path1_1 + " " + path1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path2_1 + " " + path2_2 + ")");
							newElement.setAttribute("class", "view distal " + cnt + '_distal 0');
							newElement.setAttribute("id", "view_" + cnt + "_left");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view lingual " + cnt + '_lingual 0');
							newElement.setAttribute("id", "view_" + cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path3_1 + " " + path3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view mesial " + cnt + '_mesial 0');
							newElement.setAttribute("id", "view_" + cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path4_1 + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view occlusal " + cnt + '_occlusal 0');
							newElement.setAttribute("id", "view_" + cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path5_1 + " " + path5_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

						} else {
							var top,
							    bottom,
							    right,
							    left,
							    center;
							if (cnt <= 5) {
								top = 'buccal';
								right = 'mesial';
								bottom = 'lingual';
								left = 'distal';
								center = 'occlusal';
							} else if (cnt <= 11) {
								top = 'labial';
								right = 'mesial';
								bottom = 'lingual';
								left = 'distal';
								center = 'incisal';
							} else if (cnt <= 16) {
								top = 'buccal';
								right = 'distal';
								bottom = 'lingual';
								left = 'mesial';
								center = 'occlusal';
							}
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + top + " " + cnt + '_' + top + ' 0');
							newElement.setAttribute("id", "view_" + cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path1_1 + (46 * (cnt - 1))) + " " + path1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + left + " " + cnt + '_' + left + ' 0');
							newElement.setAttribute("id", "view_" + cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path2_1 + (46 * (cnt - 1))) + " " + path2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + bottom + " " + cnt + '_' + bottom + ' 0');
							newElement.setAttribute("id", "view_" + cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path3_1 + (46 * (cnt - 1))) + " " + path3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + right + " " + cnt + '_' + right + ' 0');
							newElement.setAttribute("id", "view_" + cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path4_1 + (46 * (cnt - 1))) + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + center + " " + cnt + '_' + center + ' 0');
							newElement.setAttribute("id", "view_" + cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path1_1 + (46 * (cnt - 1))) + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

						}
						if (missing) {
							$("#view_" + cnt + "_top,#view_" + cnt + "_left,#view_" + cnt + "_bottom,#view_" + cnt + "_right,#view_" + cnt + "_center").attr('visibility', 'hidden');
						}
					} else {

						var p1_1 = 33.998659373659635;
						var p1_2 = 69.01321857571864;
						var p2_1 = 24.554214929215078;
						var p2_2 = 79.63821857571861;
						var p3_1 = 33.998659373659635;
						var p3_2 = 93.80488524238524;
						var p4_1 = 51.706992706992764;
						var p4_2 = 79.63821857571861;

					//	var source_img = '<img class = "teeth" src = "/pragtech_dental_management/static/src/img/tooth' + tooth2_cnt + '.png" id = ' + tooth2_cnt + ' width = "46" height = "50"/>';

						var missing = 0;
						for (var m = 0; m < Missing_Tooth.length; m++) {
							if (tooth2_cnt == Missing_Tooth[m]) {
								missing = 1;
								// var source_img = '<img class = "blank" src = "/pragtech_dental_management/static/src/img/images.png" id = ' + tooth2_cnt + ' width = "46" height = "50"/>';
								var source_img = '<img class = "blank" src = "/pragtech_dental_management/static/src/img/tooth' + tooth2_cnt + '.png" id = ' + tooth2_cnt + ' width = "46" height = "50" style="visibility:hidden"/>';
							}
						}
						//$("#teeth-surface-2").append(source_img);
						if (cnt == 17) {//hardcode first rectangular coordinates
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view lingual " + surface2_cnt + '_lingual 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p1_1 + " " + p1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view distal " + surface2_cnt + '_distal 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p2_1 + " " + p2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view buccal " + surface2_cnt + '_buccal 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p3_1 + " " + p3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view mesial " + surface2_cnt + '_mesial 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p4_1 + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view occlusal " + surface2_cnt + '_occlusal 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p1_1 + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

						} else {
							var top,
							    bottom,
							    right,
							    left,
							    center;
							if (surface2_cnt <= 21) {
								top = 'lingual';
								right = 'distal';
								bottom = 'buccal';
								left = 'mesial';
								center = 'occlusal';
							} else if (surface2_cnt <= 27) {
								top = 'lingual';
								right = 'mesial';
								bottom = 'labial';
								left = 'distal';
								center = 'incisal';
							} else {
								top = 'lingual';
								right = 'mesial';
								bottom = 'buccal';
								left = 'distal';
								center = 'occlusal';
							}
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + top + " " + surface2_cnt + "_" + top + ' 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path1_1 + (46 * (cnt2 - 1)) - 1)) + " " + p1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + left + " " + surface2_cnt + "_" + left + ' 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path2_1 + (46 * (cnt2 - 1)) - 1)) + " " + p2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + bottom + " " + surface2_cnt + "_" + bottom + ' 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path3_1 + (46 * (cnt2 - 1)) - 1)) + " " + p3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + right + " " + surface2_cnt + "_" + right + ' 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path4_1 + (46 * (cnt2 - 1)) - 1)) + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + center + " " + surface2_cnt + "_" + center + ' 0');
							newElement.setAttribute("id", "view_" + surface2_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path1_1 + (46 * (cnt2 - 1)) - 1)) + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);
						}
						if (missing) {
							$("#view_" + surface2_cnt + "_top,#view_" + surface2_cnt + "_left,#view_" + surface2_cnt + "_bottom,#view_" + surface2_cnt + "_right,#view_" + surface2_cnt + "_center").attr('visibility', 'hidden');
						}
						surface2_cnt -= 1;
						tooth2_cnt -= 1;
						cnt2++;
					}
					cnt++;
				}

				var child_cnt = 1;
				var child_cnt2 = 1;
				var child_surface2_cnt = 20;
				var child_tooth2_cnt = 20;
				for (var t = 1; t <= 20; t++) {
					var NS = 'http://www.w3.org/2000/svg';
					var svg = $('#svg_object_child')[0];

					if (child_cnt <= 10) {
						var path1_1 = 34.95833333333337;
						var path1_2 = 21.250000000000007;
						var path2_1 = 25.513888888888914;
						var path2_2 = 31.875000000000007;
						var path3_1 = 34.95833333333337;
						var path3_2 = 46.04166666666665;
						var path4_1 = 52.666666666666686;
						var path4_2 = 31.875000000000007;
						var path5_1 = 34.958333333333385;
						var path5_2 = 31.875000000000007;

						if (child_cnt == 1) {
							//hardcode first rectangular coordinateview_s
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view buccal " + child_cnt + '_buccal 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_top");

							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path1_1 + " " + path1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path2_1 + " " + path2_2 + ")");
							newElement.setAttribute("class", "view distal " + child_cnt + '_distal 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_left");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view lingual " + child_cnt + '_lingual 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path3_1 + " " + path3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view mesial " + child_cnt + '_mesial 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path4_1 + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view occlusal " + child_cnt + '_occlusal 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + path5_1 + " " + path5_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);
						} else {
							var top, bottom, right, left, center;
							if (child_cnt <= 5) {
								top = 'buccal';
								right = 'mesial';
								bottom = 'lingual';
								left = 'distal';
								center = 'occlusal';
							} else  {
								top = 'labial';
								right = 'mesial';
								bottom = 'lingual';
								left = 'distal';
								center = 'incisal';
							}
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + top + " " + child_cnt + '_' + top + ' 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path1_1 + (46 * (child_cnt - 1))) + " " + path1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + left + " " + child_cnt + '_' + left + ' 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path2_1 + (46 * (child_cnt - 1))) + " " + path2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + bottom + " " + child_cnt + '_' + bottom + ' 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path3_1 + (46 * (child_cnt - 1))) + " " + path3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + right + " " + child_cnt + '_' + right + ' 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path4_1 + (46 * (child_cnt - 1))) + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + center + " " + child_cnt + '_' + center + ' 0');
							newElement.setAttribute("id", "childview_" + child_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + (path1_1 + (46 * (child_cnt - 1))) + " " + path4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);
						}
					} else {
						var p1_1 = 33.998659373659635;
						var p1_2 = 69.01321857571864;
						var p2_1 = 24.554214929215078;
						var p2_2 = 79.63821857571861;
						var p3_1 = 33.998659373659635;
						var p3_2 = 93.80488524238524;
						var p4_1 = 51.706992706992764;
						var p4_2 = 79.63821857571861;

						if (child_cnt == 11) {
							//hardcode first rectangular coordinates
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view lingual " + child_surface2_cnt + '_lingual 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p1_1 + " " + p1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view distal " + child_surface2_cnt + '_distal 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p2_1 + " " + p2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view buccal " + child_surface2_cnt + '_buccal 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p3_1 + " " + p3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view mesial " + child_surface2_cnt + '_mesial 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p4_1 + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view occlusal " + child_surface2_cnt + '_occlusal 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + p1_1 + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

						} else {
							var top, bottom, right, left, center;
							if (child_surface2_cnt <= 15) {
								top = 'lingual';
								right = 'mesial';
								bottom = 'labial';
								left = 'distal';
								center = 'incisal';
							} else {
								top = 'lingual';
								right = 'mesial';
								bottom = 'buccal';
								left = 'distal';
								center = 'occlusal';
							}
							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + top + " " + child_surface2_cnt + "_" + top + ' 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_top");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path1_1 + (46 * (child_cnt2 - 1)) - 1)) + " " + p1_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + left + " " + child_surface2_cnt + "_" + left + ' 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_left");
							newElement.setAttribute("d", "M0 0 L9.444444444444457 0 L9.444444444444457 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path2_1 + (46 * (child_cnt2 - 1)) - 1)) + " " + p2_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + bottom + " " + child_surface2_cnt + "_" + bottom + ' 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_bottom");
							newElement.setAttribute("d", "M0 0 L17.708333333333314 0 L17.708333333333314 10.625 L0 10.625 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path3_1 + (46 * (child_cnt2 - 1)) - 1)) + " " + p3_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + right + " " + child_surface2_cnt + "_" + right + ' 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_right");
							newElement.setAttribute("d", "M0 0 L8.263888888888914 0 L8.263888888888914 14.166666666666657 L0 14.166666666666657 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path4_1 + (46 * (child_cnt2 - 1)) - 1)) + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);

							var newElement = document.createElementNS("http://www.w3.org/2000/svg", 'path');
							newElement.setAttribute("class", "view " + center + " " + child_surface2_cnt + "_" + center + ' 0');
							newElement.setAttribute("id", "childview_" + child_surface2_cnt + "_center");
							newElement.setAttribute("d", "M0 0 L17.7083333333333 0 L17.7083333333333 14.166666666666629 L0 14.166666666666629 L0 0 Z");
							newElement.setAttribute("transform", "matrix(1 0 0 1 " + ((path1_1 + (46 * (child_cnt2 - 1)) - 1)) + " " + p4_2 + ")");
							newElement.setAttribute("fill", "white");
							newElement.setAttribute("stroke", "black");
							svg.appendChild(newElement);
						}
						child_surface2_cnt -= 1;
						child_tooth2_cnt -= 1;
						child_cnt2++;
					}
					child_cnt++;
				}

				if (other_patient_history){
                    mapkeystatus = 1;
                    localStorage.setItem('status',mapkeystatus);
				} else {
                    mapkeystatus = 0;
                    localStorage.setItem('status',mapkeystatus);
				}
				var tempImageMapList = new Array();
                _.each(other_patient_history, function(each_operation) {
					imageMapList = each_operation['surface'];
                    var ts = imageMapList ;
                    var tooth_surface = ts;
//                    var tooth_surface = ts.slice(0,-3);
                    var surface_chk =((tooth_surface == 'root')||(tooth_surface == 'crown')||(tooth_surface == 'toothcap'));
                    var operation_is_child = each_operation['child'];
                    if ((each_operation.tooth_id) && (!surface_chk) ) {
                        self.color_surfaces(svg, each_operation['surface'].split(' '),
                                              each_operation['tooth_id'], self);
                        imageMapList = imageMapList.split(',')
                        for (var i=0; i<imageMapList.length; i++) {
                        	if(jQuery.inArray(imageMapList[i], tempImageMapList) == -1) {
                        		tempImageMapList.push(imageMapList[i]);
                        	}
                        }
                    }
                    else if((each_operation.tooth_id) && (surface_chk)) {
                        imageMapList = imageMapList.split(',')
                        for (var i=0; i<imageMapList.length; i++) {
                        	if(jQuery.inArray(imageMapList[i], tempImageMapList) == -1) {
                        		tempImageMapList.push(imageMapList[i]);
                        		var mapkeystr = tempImageMapList +',';
                        	}
                        }
                    }
                    if (each_operation['desc']['action'] == 'missing') {
                        self.perform_missing_action(each_operation['multiple_teeth']);
                    }
				});

                var toothkey = localStorage.getItem('test') || "";
				var upkey = localStorage.getItem('upperkeys');
                var lowkey = localStorage.getItem('lowerkeys');
//              csv = csv+toothkey+upkey+lowkey;
                /*----------------------*/
                var temp = toothkey.split(","), val, new_val, toothkey2 = "";
                for (var t=0;t<temp.length;t++) {
                    try {
                        new_val = temp[t].split("_");
                        val = new_val[1];
                        if (new_val[0] == 'toothcap' &&
                            val && parseInt(val) < 10) {
                            temp[t] = new_val[0] + "_" + parseInt(val);
                        }
                    }
                    catch (err) {}
                    toothkey2 += temp[t] + ",";
                }
                if (toothkey2) {
                    toothkey2 = toothkey2.slice(0, -1);
                }
                var csv = csv+toothkey2+upkey+lowkey;
                /*----------------------*/
//                console.log('lowkey', lowkey);
//                console.log('toothkey2', toothkey2);
//                console.log('the csv values configure are', csv);
                var setChk = (toothkey2||upkey||lowkey);

				$("img").click(function() {
					if (!selected_treatment) {
						if ($(this).attr('class') == 'selected_tooth') {
						    try {
                                $(this).removeClass('selected_tooth');
                                self.decrement_thread(['view_' + this.id + '_bottom', 'view_' + this.id + '_center', 'view_' + this.id + '_right', 'view_' + this.id + '_left', 'view_' + this.id + '_top']);
                                if (document.getElementById('view_' + this.id + '_center').classList[3] == "0")
                                    $('#view_' + this.id + '_center').attr('fill', 'white');
                                if (document.getElementById('view_' + this.id + '_right').classList[3] == "0")
                                    $('#view_' + this.id + '_right').attr('fill', 'white');
                                if (document.getElementById('view_' + this.id + '_left').classList[3] == "0")
                                    $('#view_' + this.id + '_left').attr('fill', 'white');
                                $('#view_' + this.id + '_top').attr('fill', 'white');
                                $('#view_' + this.id + '_bottom').attr('fill', 'white');
                                selected_surface.length = 0;
                            }
                            catch (err) {}
						} else {
							$(this).attr('class', 'selected_tooth');
							$('#view_' + this.id + '_center').attr('fill', 'orange');
							$('#view_' + this.id + '_right').attr('fill', 'orange');
							$('#view_' + this.id + '_left').attr('fill', 'orange');
							$('#view_' + this.id + '_top').attr('fill', 'orange');
							$('#view_' + this.id + '_bottom').attr('fill', 'orange');
							self.increment_thread(['view_' + this.id + '_bottom', 'view_' + this.id + '_center', 'view_' + this.id + '_right', 'view_' + this.id + '_left', 'view_' + this.id + '_top']);
						}
						return;
					}
					selected_tooth = this.id;
					self.execute_create(false, self, false);

					switch(selected_treatment.action) {
					case 'missing':
						if ($("#" + $(this).attr('id')).attr('class') == "teeth") {
							// $($("#" + $(this).attr('id')).attr('src', "/pragtech_dental_management/static/src/img/images.png").attr('class', 'blank'));
							$($("#" + $(this).attr('id')).attr('class', 'blank'));
							$($("#" + $(this).attr('id'))).css('visibility', 'hidden');
							$("#view_" + $(this).attr('id') + "_top,#view_" + $(this).attr('id') + "_left,#view_" + $(this).attr('id') + "_bottom,#view_" + $(this).attr('id') + "_right,#view_" + $(this).attr('id') + "_center").attr('visibility', 'hidden');
						} else {
							$($("#" + $(this).attr('id')).css('visibility', 'visible').attr('class', 'teeth'));
							$("#view_" + $(this).attr('id') + "_top,#view_" + $(this).attr('id') + "_left,#view_" + $(this).attr('id') + "_bottom,#view_" + $(this).attr('id') + "_right,#view_" + $(this).attr('id') + "_center").attr('visibility', 'visible');
							for (var op_id = 1; op_id <= operation_id; op_id++) {
								if (self.$('#operation_'+op_id)[0]) {
									var got_op_id = (self.$('#operation_'+op_id)[0].id).substr(10);
									if (parseInt(self.$('#tooth_'+got_op_id)[0].innerHTML) == parseInt(this.id)) {
										var tr = document.getElementById('operation_' + got_op_id);
										var desc_class = $("#desc_" + got_op_id).attr('class');
										tr.parentNode.removeChild(tr);
										for (var index = 0; index < treatment_lines.length; index++) {
											if (treatment_lines[index].teeth_id == this.id) {
												for (var i2 = 0; i2 < treatment_lines[index].values.length; i2++) {
													if (treatment_lines[index].values[i2].categ_id == parseInt(desc_class)) {
														treatment_lines.splice(index, 1);
														operation_id += 1;
														return;
													}
												}
											}
										}
										break;
									}
								}
							}
						}
						break;
					case 'composite':
						break;
					default :
						break;
					};

				});

				function removeA(arr) {
					var what, a = arguments, L = a.length, ax;
					while (L > 1 && arr.length) {
						what = a[--L];
						while ((ax= arr.indexOf(what)) !== -1) {
							arr.splice(ax, 1);
						}
					}
					return
				}

				var map1 = document.getElementById("toothmapupper");
				var map2 = document.getElementById("toothmaplower");
				map1.addEventListener("click", toothmapFunction);
				map2.addEventListener("click", toothmapFunction);
                function toothmapFunction(e){
                	var keyList= 'none';
                	var t = new Array();
            		var lst_tooth_number = new Array();
                	selected_tooth = '';
                	toothmap_id = ''
                	if(e.target !== e.currentTarget){
                		tid = e.target.id;
                		var new_tid = self.convert_surface_toothmap_based_numbering(type, tid);
        				tid = new_tid;
//						zzzzzzzzzzz start
                        var sel_table = document.getElementById('selected_list_table');
                        var sel_rows = sel_table.getElementsByTagName('tr');
                        var sel_i, sel_j, sel_cells, customerId;
                        var row_exists = 0
                        for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                            if(sel_rows[sel_i]){
                                sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                                if (!sel_cells.length) {
                                    continue;
                                }
                                customerId = sel_cells[0].innerHTML;
                                if(customerId==tid){
                                    row_exists = 1;
                                }
                            }
                        }
                        if (row_exists){
                            var sel_rows = sel_table.getElementsByTagName('tr');
                            var sel_i, sel_j, sel_cells, customerId;
                            for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                                if(sel_rows[sel_i]){
                                    sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                                    if (!sel_cells.length) {
                                        continue;
                                    }
                                    customerId = sel_cells[0].innerHTML;
                                    if(customerId==tid){
                                        sel_rows[sel_i].remove();
                                    }
                                }
                            }
                        }
                        else{
                            var table_selected_str = '';
                            table_selected_str += '<tr id="toothmap_selected">';
                            table_selected_str += '<td>' + tid + '</td>';
                            table_selected_str += '</tr>';
                            $('#selected_list_tbody').append(table_selected_str);
                        }
//                      zzzzzzzzzzz end
						if (lst_tooth.includes(tid)) {
							removeA(lst_tooth, tid);
						}
						else {
							lst_tooth.push(tid);
						}
						for (var i = 0; i < lst_tooth.length; i++) {
							t = lst_tooth[i].split('_');
	            			if (t[1] && t[1].length>2){
	            				lst_tooth_number.push(t[0]);
	            			}
	            			else{
	            				lst_tooth_number.push(t[1]);
	            			}
		            	}
						tid = lst_tooth.join();
						toothmap_id = lst_tooth_number.join();
//						console.log("1027:::::::::toothmap_id::::::::::::",toothmap_id)
						selected_tooth = toothmap_id;
						if (toothmap_id!=0){
							tooth_by_part = 1;
						}
						else{
							tooth_by_part = 0;
						}
                    }
                    e.stopPropagation();
                }

                var map3 = document.getElementById("childmapupper");
                var map4 = document.getElementById("childmaplower");
                map3.addEventListener("click", childtoothmapFunction);
                map4.addEventListener("click", childtoothmapFunction);
                function childtoothmapFunction(e) {
                	var t = new Array();
                	var lst_tooth_number = new Array();
                	selected_tooth = '';
                	toothmap_id = ''

                	if(e.target !== e.currentTarget) {
                		tid = e.target.id;
                        var new_tid = self.convert_surface_toothmap_based_numbering(type, tid);
        				tid = new_tid;
//						zzzzzzzzzzz start
                        var sel_table = document.getElementById('selected_list_table');
                        var sel_rows = sel_table.getElementsByTagName('tr');
                        var sel_i, sel_j, sel_cells, customerId;
                        var row_exists = 0
                        for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                            if(sel_rows[sel_i]){
                                sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                                if (!sel_cells.length) {
                                    continue;
                                }
                                customerId = sel_cells[0].innerHTML;
                                if(customerId==tid){
                                    row_exists = 1;
                                }
                            }
                        }
                        if (row_exists){
                            var sel_rows = sel_table.getElementsByTagName('tr');
                            var sel_i, sel_j, sel_cells, customerId;
                            for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                                if(sel_rows[sel_i]){
                                    sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                                    if (!sel_cells.length) {
                                        continue;
                                    }
                                    customerId = sel_cells[0].innerHTML;
                                    if(customerId==tid){
                                        sel_rows[sel_i].remove();
                                    }
                                }
                            }
                        }
                        else{
                            var table_selected_str = '';
                            table_selected_str += '<tr id="toothmap_selected">';
                            table_selected_str += '<td>' + tid + '</td>';
                            table_selected_str += '</tr>';
                            $('#selected_list_tbody').append(table_selected_str);
                        }
//                      zzzzzzzzzzz end
						if (lst_tooth.includes(tid)) {
							removeA(lst_tooth, tid);
						}
						else {
							lst_tooth.push(tid);
						}
						for (var i = 0; i < lst_tooth.length; i++) {
							t = lst_tooth[i].split('_');
		            		if (lst_tooth_number.includes(parseInt(t[1]))) {
		            			removeA(lst_tooth_number, parseInt(t[1]));
		            		}
		            		else {
		            			lst_tooth_number.push(parseInt(t[1]));
		            		}
		            	}
						tid = lst_tooth.join();
						toothmap_id = lst_tooth_number.join();
						selected_tooth = toothmap_id;
						if (toothmap_id !=0){
							tooth_by_part = 1;
						}
						else{
							tooth_by_part = 0;
						}
                	}
                	e.stopPropagation();
            	}
//            	console.log(222);
				$(".view").click(function() {
					tooth_by_part = 0;
					var lst_tooth_number = new Array();
					var surf = selected_surface;
					selected_surface = []
					var chksurf= surf.slice(0,-3);

					if ((chksurf=='root')||(chksurf=='crown')||(chksurf=='toothcap')){
				       selected_surface = [];
				    }
					if(!tooth_by_part){
					if (!cont || update) {
						selected_surface.length = 0;
						cont = true;
					} else {
					  if (selected_surface[0]) {
							var tooth = (selected_surface[0].split('_'))[1];
							var current_tooth = ((this.id).split('_'))[1];
							if (current_tooth != tooth) {
								for (var i = 0; i < selected_surface.length; i++) {
									$("#" + selected_surface[i]).attr('fill', 'white');
								}
								selected_surface.length = 0;
							}
						  }
					    }
					}
					var found_selected_operation = self.$el.find('.selected_operation');
					if (found_selected_operation[0]) {
						var op_id = ((found_selected_operation[0].id).split('_'))[1];
						if ($('#status_' + op_id)[0].innerHTML == 'Completed'){
							alert('Cannot update Completed record');
							$('#operation_' + op_id).removeClass('selected_operation');
							return;
						}
						var s = (($("#" + this.id).attr('class')).split(' '))[1];
						if (((this.id).split('_'))[1] == $('#tooth_' + op_id).attr('class')) {
							update = true;
							var surf_old_list = ($('#surface_'+op_id)[0].innerHTML).split(' ');
							var got = 0;
							for (var in_list = 0; in_list < surf_old_list.length; in_list++) {
								if (surf_old_list[in_list] == s) {
									got = 1;
									var index = selected_surface.indexOf(this.id);
									selected_surface.splice(index, 1);
									$('#surface_' + op_id).empty();
									_.each(surf_old_list, function(sol) {
										if (sol != s)
											$('#surface_'+op_id)[0].innerHTML += sol + ' ';
									});
									self.decrement_thread([this.id]);
									break;
								}
							}
							if (got == 0) {
								$('#surface_'+op_id)[0].innerHTML += s + ' ';
								selected_surface.push(this.id);
								self.increment_thread([this.id]);
							}
						} else {
							update = false;
						}
					}
					selected_tooth = ((this.id).split('_'))[1];
//					console.log("1159::::::selected surface********",selected_tooth,(this.id),(this.id).split('_'));
					if (1) {
						if ($("#" + $(this).attr('id')).attr('fill') == 'white') {
							$("#" + $(this).attr('id')).attr('fill', 'orange');
							var available = selected_surface.indexOf(this.id);
							if(available == -1 && is_tooth_select == false){
								selected_surface.push(this.id);
							}
						} else if (parseInt(($("#" + $(this).attr('id')).attr('class')).split(' ')[3]) == 0){
							is_tooth_select = false
							$("#" + $(this).attr('id')).attr('fill', 'white');
							var index = selected_surface.indexOf(this.id);
							selected_surface.splice(index, 1);
						} else {
							if ($("#" + $(this).attr('id')).attr('fill') == 'orange') {
							$("#" + $(this).attr('id')).attr('fill', 'white');
							is_tooth_select = true
							var current_tooth_id = this.id.lastIndexOf("_")
							var res = this.id.slice(current_tooth_id, this.id.length);
							}
							else{
								selected_surface.push(this.id);
							}
						}
					}
					function removeA(arr) {
					    var what, a = arguments, L = a.length, ax;
					    while (L > 1 && arr.length) {
					        what = a[--L];
					        while ((ax= arr.indexOf(what)) !== -1) {
					            arr.splice(ax, 1);
					        }
					    }
					    return arr;
					}
					var cls = this.getAttribute('class').split(' ')[2];
					var new_cls = self.convert_surface_toothmap_based_numbering(type, cls);
					cls = new_cls;
					if(jQuery.inArray(cls, final_plus) == -1) {
						final_plus.push(cls);
//						zzzzzzzzzzz start
						if(! full_mouth_selected){
						    var table_selected_str = '';
                            table_selected_str += '<tr id="surface_selected">';
                            table_selected_str += '<td>' + cls + '</td>';
                            table_selected_str += '</tr>';
                            $('#selected_list_tbody').append(table_selected_str);
						}
//						zzzzzzzzzzz end
					}
					else{
						removeA(final_plus, cls);
//						zzzzzzzzzzz start
                        var sel_table = document.getElementById('selected_list_table');
                        var sel_rows = sel_table.getElementsByTagName('tr');
                        var sel_i, sel_j, sel_cells, customerId;
                        for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                            if(sel_rows[sel_i]){
                                sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                                if (!sel_cells.length) {
                                    continue;
                                }
                                customerId = sel_cells[0].innerHTML;
                                if(customerId==cls){
                                    sel_rows[sel_i].remove();
                                }
                            }
                        }
//                      zzzzzzzzzzz end
                    }
					if (final_plus === undefined || final_plus.length == 0){
						tooth_by_part =0;
						toothmap_id="";
					}else{
						tooth_by_part = 1;
						toothmap_id=selected_tooth;
					}
//					console.log("1159:::::::::::lst tooth :::::::selected_tooth",selected_surface)
					tid = final_plus.join();
					if(jQuery.inArray(tid, lst_tooth) == -1) {
//	                    zzzzzzzzzzz start
						lst_tooth.pop();
//						zzzzzzzzzzz end
						lst_tooth.push(tid);
					}
					if (final_plus==[]){
						tooth_by_part =0;
						toothmap_id="";
					}
//					toothmap_id = lst_tooth.join();
//					console.log("1165::::::::::toothmap_id:::::::final_plus",tooth_by_part,tid,final_plus);
				});

				self.get_treatment_cats().then(function(res) {
				    toastr.options = {
                      "closeButton": false,
                      "debug": false,
                      "newestOnTop": false,
                      "progressBar": false,
                      "preventDuplicates": false,
                      "onclick": null,
                      "showDuration": "300",
                      "hideDuration": "1000",
                      "timeOut": "2000",
                      "extendedTimeOut": "1000",
                      "showEasing": "swing",
                      "hideEasing": "linear",
                      "showMethod": "fadeIn",
                      "hideMethod": "fadeOut"
                    }
					var treatment_list = res;
					var total_list_div = '';

					for (var j = 0; j < treatment_list.length; j++) {
						total_list_div += '<div class="panel-heading"><h4 class="panel-title"><a id="categ_' + treatment_list[j].treatment_categ_id + '"data-toggle="collapse" href="#collapse' + treatment_list[j].treatment_categ_id + '">' + treatment_list[j].name + '</a></h4></div>';
						total_list_div += '<div id="collapse' + treatment_list[j].treatment_categ_id + '" class="panel-collapse collapse"><div class="panel-body">';
						_.each(treatment_list[j].treatments, function(each_one) {
							if (each_one.action == 'missing') {
								missing = each_one.treatment_id;
							}
							total_list_div += '<li id = "treat_' + treatment_list[j].treatment_categ_id +
							    '_' + each_one['treatment_id'] + '"data-id=' + each_one['highlight_color'] +
							    '">' + each_one['treatment_name'] + '</li>';
						});
						total_list_div += '</div></div>';

					}
					$('#total_list_div').append(total_list_div);
//					console.log("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG ",localStorage)

					self.categ_list = treatment_list;
					for (var i = 0; i < self.categ_list.length; i++) {

						/*following variable defined for avoid at time multiple treatment added same operation*/
						var inside_one_time=true
						var assigned_categ_no
						$('#categ_' + self.categ_list[i].treatment_categ_id).click(function(e) {
							if (selected_surface) {
//							    console.log("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG ",localStorage)

								var found_selected_categ = self.$el.find('.selected_category');
								if (found_selected_categ) {
									found_selected_categ.removeClass("selected_category");
								}
								selected_treatment = '';
								$('#' + this.id).attr('class', 'selected_category');
								var categ_no = parseInt(this.id.substr(6));

								/* Checked category are same or different */
								if (assigned_categ_no!=categ_no){
									inside_one_time=true;
								}
								self.$('#treatments_list').empty();
								if (inside_one_time==true){
									for (var k = 0; k < self.categ_list.length; k++) {
										if (self.categ_list[k].treatment_categ_id == categ_no) {
											assigned_categ_no=categ_no;
											inside_one_time=false;
											_.each(self.categ_list[k].treatments, function(each_treatment) {
												$('#treat_' + categ_no + '_' + each_treatment.treatment_id).attr('data-selected', 'false');
												$('#treat_' + categ_no + '_' + each_treatment.treatment_id).click(function() {
//													console.log("GGGG 2222 ",localStorage)

													var found_selected_tooth;
													if (full_mouth_selected == 1) {
//													    zzzzzzzzzzz start
													    var new_surface_name = false;
                                                        var new_tooth_selected =  false;
                                                        var new_surface_tooth = self.get_new_surface_tooth();
                                                        if(new_surface_tooth){
                                                            new_surface_name = new_surface_tooth[0];
                                                            new_tooth_selected =  new_surface_tooth[1];
                                                        }
                                                        if (!new_surface_name || !new_tooth_selected) {
                                                            alert('Please select the surface first !!!   ');
                                                            return;
                                                        }
														self.put_data_full_mouth(self, new_tooth_selected,
															full_mouth_selected, each_treatment,
															'planned', new_surface_name,
															false, false, false, false, false, 0,
															 "draft", false,
															session.uid,
															user_name
														);
														self.deselect_upper_lower_full_mouth();
//														zzzzzzzzzzz end
														toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
														rpc.query({
	                                                        model: 'medical.patient',
	                                                        method: 'is_warning_needed',
	                                                        args: [self.patient_id, each_treatment],
	                                                    })
	                                                    .then(function(res) {
	                                                       if (res == true){
	                                                        toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
	                                                       }
	                                                    });

														full_mouth_selected = 0;
														return;
													}
													if (upper_mouth_selected == 1) {
	                                                    var upper_mouth = new Array();
	                                                    for (var select_up_tooth = 1; select_up_tooth <= 16; select_up_tooth++) {
	                                                    upper_mouth.push(select_up_tooth);}
//	                                                    zzzzzzzzzzz start
													    var new_surface_name = false;
                                                        var new_tooth_selected =  false;
                                                        var new_surface_tooth = self.get_new_surface_tooth();
                                                        if(new_surface_tooth){
                                                            new_surface_name = new_surface_tooth[0];
                                                            new_tooth_selected =  new_surface_tooth[1];
                                                        }
                                                        if (!new_surface_name || !new_tooth_selected) {
                                                            alert('Please select the surface first !!!   ');
                                                            return;
                                                        }
                                                        self.put_data_full_mouth(self, new_tooth_selected,
															upper_mouth_selected, each_treatment,
															'planned', new_surface_name,false,
															false, false, false, false, 0,
															 "draft", false,
															session.uid,
															user_name);
												        self.deselect_upper_lower_full_mouth();
//														zzzzzzzzzzz end
													    toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
													    rpc.query({
	                                                        model: 'medical.patient',
	                                                        method: 'is_warning_needed',
	                                                        args: [self.patient_id, each_treatment],
	                                                    })
	                                                    .then(function(res) {
	                                                       if (res == true){
	                                                        toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
	                                                       }
	                                                    });

														upper_mouth_selected = 0;
														return;
													}
													if (lower_mouth_selected == 1) {
													    var lower_mouth = new Array();
	                                                    for (var select_up_tooth = 1; select_up_tooth <= 16; select_up_tooth++) {
	                                                    lower_mouth.push(select_up_tooth);}
														/*add argument for amount*/
//	                                                    zzzzzzzzzzz start
													    var new_surface_name = false;
                                                        var new_tooth_selected =  false;
                                                        var new_surface_tooth = self.get_new_surface_tooth();
                                                        if(new_surface_tooth){
                                                            new_surface_name = new_surface_tooth[0];
                                                            new_tooth_selected =  new_surface_tooth[1];
                                                        }
                                                        if (!new_surface_name || !new_tooth_selected) {
                                                            alert('Please select the surface first !!!   ');
                                                            return;
                                                        }
                                                        self.put_data_full_mouth(self, new_tooth_selected,
															lower_mouth_selected,
															each_treatment,
															'planned', new_surface_name,
															false, false, false,
															false, false, 0, "draft",
															false,
															session.uid,
															user_name
														);
														self.deselect_upper_lower_full_mouth();
//														zzzzzzzzzzz end
														toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
														rpc.query({
	                                                        model: 'medical.patient',
	                                                        method: 'is_warning_needed',
	                                                        args: [self.patient_id, each_treatment],
	                                                    })
	                                                    .then(function(res) {
	                                                       if (res == true){
	                                                        toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
	                                                       }
	                                                    });

														lower_mouth_selected = 0;
														return;
													}

	                                                if (tooth_by_part == 1) {
	                                                selected_surface = tid;
	                                                if (selected_surface){
	                                                	found_selected_tooth = toothmap_id;
	                                                }
//													console.log("1308::::::::::********************",toothmap_id,tid,typeof(found_selected_tooth))
													var initial = false;
													if (localStorage.getItem('initial_exam') == 'true') {
														initial = true;
													}
//													zzzzzzzzzzz start
                                                    var new_surface_name = false;
													var new_tooth_selected =  false;
													var new_surface_tooth = self.get_new_surface_tooth();
													if(new_surface_tooth){
													    new_surface_name = new_surface_tooth[0];
													    new_tooth_selected =  new_surface_tooth[1];
													}
													if (!new_surface_name || !new_tooth_selected) {
														alert('Please select the surface first !!!   ');
														return;
													}
													self.put_data_toothpart(self_var, new_tooth_selected,
	                                                    new_surface_name, tooth_by_part,
	                                                    each_treatment,'planned', false, false,
	                                                    false, initial
	                                                );
//	                                                zzzzzzzzzzz end
	                                                if(toothmap_id==null)
                                                        {
                                                        return false
                                                        }
	                                                toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
	                                                //TO DO task for upper jaw and low jwa selection
	//                                                upkey = localStorage.getItem('upperkeys');
	//                                                console.log('..........upperkeyset.....',upkey)
	//                                                console.log("^^^^^^^^^%%%%%%%%%",selected_surface,found_selected_tooth)
	//                                                localStorage.removeItem('upperkeys');
	                                                rpc.query({
	                                                    model: 'medical.patient',
	                                                    method: 'is_warning_needed',
	                                                    args: [self.patient_id, each_treatment],
	                                                })
	                                                .then(function(res) {
	                                                   if (res == true){
	                                                    toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
	                                                   }
	                                                });


	                                                tooth_by_part == 0;
	                                                selected_surface == '';

	                                                return;
													}

													cont = false;
													var found_selected_tooth = self.$el.find('.selected_tooth');
													if (found_selected_tooth[0]) {
														selected_surface.length = 0;
													}
													is_tooth_select = false
													if (selected_surface[0]) {
														if(each_treatment.action != 'missing'){
															var found = self.$el.find('.selected_treatment');
															if (found) {
																found.removeClass("selected_treatment");
															}
															$('#treat_' + categ_no + '_' + each_treatment.treatment_id).attr('class', 'selected_treatment');
															selected_treatment = each_treatment;
	//														console.log("Execute Create 22222222222  ",selected_surface);
															self.execute_create(true, self, selected_surface);
														}
														else{
															var answer = confirm('Complete tooth has to be missing, not the selected surfaces.\nClick OK to remove the complete tooth')
															if(answer){
																var tooth_id = selected_surface[0].split('_')[1]
																$('#'+tooth_id).attr('class','selected_tooth')
																found_selected_tooth = self.$el.find('.selected_tooth');
															}
														}
													}

													if (found_selected_tooth[0]) {
														if (!found_selected_tooth[0])
															alert('Please select the surface first !');
														else {
															var found = self.$el.find('.selected_treatment');
															if (found) {
																found.removeClass("selected_treatment");
															}
															$('#treat_' + categ_no + '_' + each_treatment.treatment_id).attr('class', 'selected_treatment');
	                                                        selected_treatment = each_treatment;
															_.each(found_selected_tooth, function(each_found_selected_tooth) {
																selected_tooth = each_found_selected_tooth.id;
																selected_surface.length = 0;
																if($("#" +'view_' + selected_tooth + '_top').attr('fill') == 'orange'){
																	selected_surface.push('view_' + selected_tooth + '_top');
																}
																if($("#" +'view_' + selected_tooth + '_bottom').attr('fill') == 'orange'){
																	selected_surface.push('view_' + selected_tooth + '_bottom');
																}
																if($("#" +'view_' + selected_tooth + '_center').attr('fill') == 'orange'){
																	selected_surface.push('view_' + selected_tooth + '_center');
																}
																if($("#" +'view_' + selected_tooth + '_right').attr('fill') == 'orange'){
																	selected_surface.push('view_' + selected_tooth + '_right');
																}
																if($("#" +'view_' + selected_tooth + '_left').attr('fill') == 'orange'){
																	selected_surface.push('view_' + selected_tooth + '_left');
																}

																if (each_treatment.action == 'missing') {
																	Missing_Tooth.push(parseInt(selected_tooth));
																	self.perform_missing_action([selected_tooth]);
																}
																self.execute_create(true, self, false);
																$(each_found_selected_tooth).removeClass('selected_tooth');
															});
															selected_surface.length = 0;
														}
													}
													if (!found_selected_tooth[0] && !selected_surface[0]) {
														alert('Please select the surface first !  ');
														return;
													}
													$('#' + this.id).removeClass('selected_treatment');
													selected_treatment = '';
												});
											});
											break;
										}
									}
									}
								} else {
									alert('Select a tooth first!!');
								}

						});

					}
                    /*preparing the data to use for the autocomplete
                    i.e, for the treatment search*/
                    var temp_line = {}, treatments_search_list = [];
					for (var t=0;t<treatment_list.length;t++) {
					    for (var tl=0;tl<treatment_list[t].treatments.length;tl++) {
					        var t_lines = treatment_list[t].treatments[tl];
					        temp_line = {
					            label: t_lines.treatment_name,
					            value: t_lines.treatment_name,
					            id: t_lines.treatment_id,
					            categ: treatment_list[t].treatment_categ_id,
					            action: t_lines.action
					        };
					        treatments_search_list.push(temp_line);
					    }
					}
					/*jquery autocomplete feature for treatment selection*/
					$('#treatment_search').autocomplete({
						select: function (event, ui) {
//							console.log(2221);
							var terms = split(this.value);
							// remove the current input
							terms.pop();
							// add the selected item
							terms.push(ui.item.label);
							this.value = terms;
							var each_treatment = {
							    action: ui.item.action,
							    treatment_id: ui.item.id,
							    treatment_name: ui.item.label
							};

							var found_selected_tooth;
                            if (full_mouth_selected == 1) {
    //							zzzzzzzzzzz start
                                var new_surface_name = false;
                                var new_tooth_selected =  false;
                                var new_surface_tooth = self.get_new_surface_tooth();
                                if(new_surface_tooth){
                                    new_surface_name = new_surface_tooth[0];
                                    new_tooth_selected =  new_surface_tooth[1];
                                }
                                if (!new_surface_name || !new_tooth_selected) {
                                    alert('Please select the surface first !!!   ');
                                    return;
                                }
                                self.put_data_full_mouth(self, new_tooth_selected,
                                    full_mouth_selected, each_treatment,
                                    'planned', new_surface_name,
                                    false, false, false, false, false, 0,
                                     "draft", false,
                                    session.uid,
                                    user_name
                                );
                                self.deselect_upper_lower_full_mouth();
//							zzzzzzzzzzz end
                                toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
                                rpc.query({
                                    model: 'medical.patient',
                                    method: 'is_warning_needed',
                                    args: [self.patient_id, each_treatment],
                                })
                                .then(function(res) {
                                   if (res == true){
                                    toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
                                   }
                                });

                                full_mouth_selected = 0;
                                return;
                            }
                            if (upper_mouth_selected == 1) {
                                var upper_mouth = new Array();
                                for (var select_up_tooth = 1; select_up_tooth <= 16; select_up_tooth++) {
                                    upper_mouth.push(select_up_tooth);
                                }
//	                            zzzzzzzzzzz start
                                var new_surface_name = false;
                                var new_tooth_selected =  false;
                                var new_surface_tooth = self.get_new_surface_tooth();
                                if(new_surface_tooth){
                                    new_surface_name = new_surface_tooth[0];
                                    new_tooth_selected =  new_surface_tooth[1];
                                }
                                if (!new_surface_name || !new_tooth_selected) {
                                    alert('Please select the surface first !!!   ');
                                    return;
                                }
                                self.put_data_full_mouth(self, new_tooth_selected,
                                    upper_mouth_selected, each_treatment,
                                    'planned', new_surface_name,false,
                                    false, false, false, false, 0,
                                    "draft", false,
                                    session.uid,
                                    user_name
                                );
                                self.deselect_upper_lower_full_mouth();
//								zzzzzzzzzzz end
                                toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
                                rpc.query({
                                    model: 'medical.patient',
                                    method: 'is_warning_needed',
                                    args: [self.patient_id, each_treatment],
                                })
                                .then(function(res) {
                                   if (res == true){
                                    toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
                                   }
                                });

                                upper_mouth_selected = 0;
                                return;
                            }
                            if (lower_mouth_selected == 1) {
                                var lower_mouth = new Array();
                                for (var select_up_tooth = 1; select_up_tooth <= 16; select_up_tooth++) {
                                lower_mouth.push(select_up_tooth);}
                                /*add argument for amount*/
//	                            zzzzzzzzzzz start
                                var new_surface_name = false;
                                var new_tooth_selected =  false;
                                var new_surface_tooth = self.get_new_surface_tooth();
                                if(new_surface_tooth){
                                    new_surface_name = new_surface_tooth[0];
                                    new_tooth_selected =  new_surface_tooth[1];
                                }
                                if (!new_surface_name || !new_tooth_selected) {
                                    alert('Please select the surface first !!!   ');
                                    return;
                                }
                                self.put_data_full_mouth(self, new_tooth_selected,
                                    lower_mouth_selected,
                                    each_treatment,
                                    'planned', new_surface_name,
                                    false, false, false,
                                    false, false, 0, "draft",
                                    false,
                                    session.uid,
                                    user_name
                                );
                                self.deselect_upper_lower_full_mouth();
//								zzzzzzzzzzz end
                                toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
                                rpc.query({
                                    model: 'medical.patient',
                                    method: 'is_warning_needed',
                                    args: [self.patient_id, each_treatment],
                                })
                                .then(function(res) {
                                   if (res == true){
                                    toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
                                   }
                                });

                                lower_mouth_selected = 0;
                                return;
                            }

                            if (tooth_by_part == 1) {
                                found_selected_tooth = toothmap_id;
                                selected_surface = tid;
                                var initial = false;
                                if (localStorage.getItem('initial_exam') == 'true') {
                                	initial = true;
                                }
                                var new_surface_name = false;
                                var new_tooth_selected =  false;
                                var new_surface_tooth = self.get_new_surface_tooth();
                                if(new_surface_tooth){
                                    new_surface_name = new_surface_tooth[0];
                                    new_tooth_selected =  new_surface_tooth[1];
                                }
                                if (!new_surface_name || !new_tooth_selected) {
                                    alert('Please select the surface first !!!   ');
                                    return;
                                }
                                self.put_data_toothpart(self_var, new_tooth_selected,
                                    new_surface_name, tooth_by_part, each_treatment,
                                    'planned', false, false, false, initial);
                                toastr.success("Treatment Line Added Successfully.", "TREATMENT STATUS");
                                rpc.query({
                                    model: 'medical.patient',
                                    method: 'is_warning_needed',
                                    args: [self.patient_id, each_treatment],
                                })
                                .then(function(res) {
                                   if (res == true){
                                    toastr.success("Selected treatment is not covered by the insurance policy.", "INSURANCE STATUS");
                                   }
                                });
                                    tooth_by_part == 0;
                                    selected_surface == '';
                                return;
                            }

                            cont = false;

                            var found_selected_tooth = self.$el.find('.selected_tooth');
                            if (found_selected_tooth[0]) {
                                selected_surface.length = 0;
                            }
                            is_tooth_select = false

                            if (selected_surface[0]) {
                                if(each_treatment.action != 'missing'){
                                    var found = self.$el.find('.selected_treatment');
                                    if (found) {
                                        found.removeClass("selected_treatment");
                                    }
                                    $('#treat_' + ui.item.categ + '_' + ui.item.value).attr(
                                        'class', 'selected_treatment');
                                    selected_treatment = each_treatment;
                                    self.execute_create(true, self, selected_surface);
                                }
                                else{
                                    var answer = confirm('Complete tooth has to be missing,' +
                                        'not the selected surfaces.\nClick OK to remove the complete tooth')
                                    if(answer){
                                        var tooth_id = selected_surface[0].split('_')[1]
                                        $('#'+tooth_id).attr('class','selected_tooth')
                                        found_selected_tooth = self.$el.find('.selected_tooth');
                                    }
                                }
                            }

                            if (found_selected_tooth[0]) {
                                if (!found_selected_tooth[0])
                                    alert('Please select the surface first !');
                                else {
                                    var found = self.$el.find('.selected_treatment');
                                    if (found) {
                                        found.removeClass("selected_treatment");
                                    }
                                    $('#treat_' + ui.item.categ + '_' + ui.item.value).attr(
                                        'class', 'selected_treatment');
                                    selected_treatment = each_treatment;
                                    _.each(found_selected_tooth, function(each_found_selected_tooth) {
                                        selected_tooth = each_found_selected_tooth.id;
                                        selected_surface.length = 0;
                                        if($("#" +'view_' + selected_tooth + '_top').attr('fill') == 'orange'){
                                            selected_surface.push('view_' + selected_tooth + '_top');
                                        }
                                        if($("#" +'view_' + selected_tooth + '_bottom').attr('fill') == 'orange'){
                                            selected_surface.push('view_' + selected_tooth + '_bottom');
                                        }
                                        if($("#" +'view_' + selected_tooth + '_center').attr('fill') == 'orange'){
                                            selected_surface.push('view_' + selected_tooth + '_center');
                                        }
                                        if($("#" +'view_' + selected_tooth + '_right').attr('fill') == 'orange'){
                                            selected_surface.push('view_' + selected_tooth + '_right');
                                        }
                                        if($("#" +'view_' + selected_tooth + '_left').attr('fill') == 'orange'){
                                            selected_surface.push('view_' + selected_tooth + '_left');
                                        }

                                        if (each_treatment.action == 'missing') {
                                            Missing_Tooth.push(parseInt(selected_tooth));
                                            self.perform_missing_action([selected_tooth]);
                                        }
                                        self.execute_create(true, self, false);
                                        $(each_found_selected_tooth).removeClass('selected_tooth');
                                    });
                                    selected_surface.length = 0;
                                }
                            }
                            if (!found_selected_tooth[0] && !selected_surface[0]) {
                                alert('  Please select the surface first !');
                                return;
                            }
                            $('#treat_' + ui.item.categ + '_' + ui.item.value).removeClass('selected_treatment');
                            selected_treatment = '';

							return false;
						},
						source: function (request, response) {
							var res = $.ui.autocomplete.filter(
								treatments_search_list, extractLast(request.term));
							response(res);
						},
						position: {
						    collision: "flip"
                        }
					});
                    /*autocomplete end*/
				});

				self.add_tooltip('svg');
			});
		},
        start:function(){
            var self = this;
            var history_diff = rpc.query({
                method: 'read',
                model: 'medical.patient',
                args: [self.patient_id, ['patient_name', 'patient_id']]
            });

            $.when.apply($, [this._super(), history_diff])
                .then(function (start_super, res) {
                    var pat_details = "<span>Patient Id: " + res[0]['patient_id'] + "</span><br />";
                    pat_details += "<span>Patient Name: " + res[0]['patient_name'] + "</span>";
                    pat_details = $(pat_details);
                    $('.patient_details').append(pat_details);
                    self._resize_table_columns();
                });
        },
		perform_missing_action : function(missing_tooth_ids) {
			_.each(missing_tooth_ids, function(each_of_missing_tooth_ids) {
				// $('#' + String(each_of_missing_tooth_ids)).attr('src', "/pragtech_dental_management/static/src/img/images.png");
				$('#' + String(each_of_missing_tooth_ids)).css('visibility', 'hidden').attr('class', 'blank');
				$('#view_' + String(each_of_missing_tooth_ids) + '_top').attr('visibility', 'hidden');
				$('#view_' + String(each_of_missing_tooth_ids) + '_bottom').attr('visibility', 'hidden');
				$('#view_' + String(each_of_missing_tooth_ids) + '_left').attr('visibility', 'hidden');
				$('#view_' + String(each_of_missing_tooth_ids) + '_right').attr('visibility', 'hidden');
				$('#view_' + String(each_of_missing_tooth_ids) + '_center').attr('visibility', 'hidden');
			});
		},

		remove_missing_action : function(missing_tooth_ids) {
			_.each(missing_tooth_ids, function(each_of_missing_tooth_ids) {
				$('#' + String(each_of_missing_tooth_ids)).css('visibility', 'visible').attr('class', 'teeth');
				;
				$('#view_' + String(each_of_missing_tooth_ids) + '_top').attr('visibility', 'visible');
				$('#view_' + String(each_of_missing_tooth_ids) + '_bottom').attr('visibility', 'visible');
				$('#view_' + String(each_of_missing_tooth_ids) + '_left').attr('visibility', 'visible');
				$('#view_' + String(each_of_missing_tooth_ids) + '_right').attr('visibility', 'visible');
				$('#view_' + String(each_of_missing_tooth_ids) + '_center').attr('visibility', 'visible');
			});
		},

		remove_selection_action : function(nonselection_ids) {
		    var tmp;
			_.each(nonselection_ids, function(each_of_nonselection_ids) {
			    try {
                    tmp = document.getElementById('view_'+String(each_of_nonselection_ids)+"_top").classList[3];
                    if (tmp == '0')
                        $('#view_' + String(each_of_nonselection_ids) + '_top').attr('fill', 'white');
                    tmp = document.getElementById('view_'+String(each_of_nonselection_ids)+"_bottom").classList[3];
                    if (tmp == '0')
                        $('#view_' + String(each_of_nonselection_ids) + '_bottom').attr('fill', 'white');
                    tmp = document.getElementById('view_'+String(each_of_nonselection_ids)+"_left").classList[3];
                    if (tmp == '0')
                        $('#view_' + String(each_of_nonselection_ids) + '_left').attr('fill', 'white');
                    tmp = document.getElementById('view_'+String(each_of_nonselection_ids)+"_right").classList[3];
                    if (tmp == '0')
                        $('#view_' + String(each_of_nonselection_ids) + '_right').attr('fill', 'white');
                    tmp = document.getElementById('view_'+String(each_of_nonselection_ids)+"_center").classList[3];
                    if (tmp == '0')
                        $('#view_' + String(each_of_nonselection_ids) + '_center').attr('fill', 'white');
                }
                catch (err) {}
			});
		},
		add_selection_action : function(selection_ids) {
			_.each(selection_ids, function(each_of_selection_ids) {
				$('#view_' + String(each_of_selection_ids) + '_top').attr('fill', 'orange');
				$('#view_' + String(each_of_selection_ids) + '_bottom').attr('fill', 'orange');
				$('#view_' + String(each_of_selection_ids) + '_left').attr('fill', 'orange');
				$('#view_' + String(each_of_selection_ids) + '_right').attr('fill', 'orange');
				$('#view_' + String(each_of_selection_ids) + '_center').attr('fill', 'orange');
			});
		},
		color_surfaces : function(svg_var, surface_to_color, tooth_id, self_var) {
			_.each(surface_to_color, function(each_surface_to_color) {
				if (each_surface_to_color) {
					var found_surface_to_color = $(svg_var).find("." + tooth_id + "_" + each_surface_to_color);
					if (found_surface_to_color.length != 0) {
						$('#' + found_surface_to_color[0].id).attr('fill', 'orange');
						self_var.increment_thread([found_surface_to_color[0].id]);
					}
				}
			});
		},
		write_patient_history : function(self_var, res) {
			var is_prev_record_from_write = false;
			_.each(res, function(each_operation) {

				selected_treatment = {
					'treatment_id' : each_operation['desc']['id'],
					'treatment_name' : each_operation['desc']['name'],
					'action' : each_operation['desc']['action']
				};
				is_prev_record_from_write = false;
				if (each_operation['status'] == 'completed') {

					is_prev_record_from_write = true;
				}
				if (each_operation['status'] == 'in_progress')
					each_operation['status'] = 'in_progress';
				if (each_operation['tooth_id']){
					imageMapList = each_operation['surface'];
					var ts = imageMapList ;
                    var tooth_surface = ts.slice(0,-3);
                    var surface_chk =((tooth_surface == 'root')||(tooth_surface == 'crown')||(tooth_surface == 'toothcap'));
					if((tooth_surface == 'root')||(tooth_surface == 'crown')||(tooth_surface == 'toothcap')) {
						keyList.push(imageMapList);
						var mapkeystr = keyList +',';
						localStorage.setItem('test', mapkeystr);
					}
					self_var.put_data(
						self_var,
						each_operation['surface'].split(' '),
						each_operation['tooth_id'], false,
						each_operation['status'], each_operation['created_date'],
						is_prev_record_from_write, each_operation['other_history'],
						each_operation['dignosis'],each_operation['dignosis_description'],
						each_operation['amount'],
						each_operation['inv_status'],
						each_operation['id'],
						each_operation['dentist'][0], //doctor id
						each_operation['dentist'][1], //doctor name
						each_operation['initial'],
						each_operation['desc']['highlight_color'],
						each_operation['unit_price'],
						each_operation['discount_fixed_percent'],
						each_operation['discount'],
						each_operation['discount_value']
					);
				}
				else {
					self_var.put_data_full_mouth(
						self_var,
						each_operation.multiple_teeth,
						1,
						selected_treatment,
						each_operation['status'],
						each_operation['surface'],
						each_operation['created_date'],
						is_prev_record_from_write,
						each_operation['other_history'],
						each_operation['dignosis'],
						each_operation['dignosis_description'],
						each_operation['amount'],
						each_operation['inv_status'], //invoice status
						each_operation['id'], //treatment line id
						each_operation['dentist'][0], //doctor id
						each_operation['dentist'][1], // doctor name
						each_operation['initial'],
						each_operation['desc']['highlight_color'],
						each_operation['unit_price'],
						each_operation['discount_fixed_percent'],
						each_operation['discount'],
						each_operation['discount_value']
					);

				}
			});
			selected_treatment = '';
		},
		exists_in_selected_surface : function(selected_tooth_part) {
		    var exists_surface = false;
		    var sel_table = document.getElementById('selected_list_table');
            var sel_rows = sel_table.getElementsByTagName('tr');
            var sel_i, sel_j, sel_cells, customerId;
            for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                if(sel_rows[sel_i]){
                    sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                    if (!sel_cells.length) {
                        continue;
                    }
                    customerId = sel_cells[0].innerHTML;
                    if(customerId==selected_tooth_part){
                        var exists_surface = true;
                    }
                }
            }
            return exists_surface;

		},
		exists_in_operations_table : function( customerId) {
		    var op_table = document.getElementById('progres_table');
            var op_rows = op_table.getElementsByTagName('tr');
            var op_i, op_j, op_cells, customerId;
            var row_exists = 0
            var is_already_exists_below = false;
            for (op_i = 0, op_j = op_rows.length; op_i < op_j; ++op_i) {
                if(op_rows[op_i]){
                    op_cells = op_rows[op_i].getElementsByTagName('td');
                    if(document.getElementById('surface_' + op_i)){
                      var table_surface = document.getElementById('surface_' + op_i).textContent;
                      if(table_surface.includes(customerId)){
                            is_already_exists_below = true;
                        }
                    }
                }
            }
            return is_already_exists_below;
		},
		count_exists_in_operations_table : function( customerId) {
		    var op_table = document.getElementById('progres_table');
            var op_rows = op_table.getElementsByTagName('tr');
            var op_i, op_j, op_cells, customerId;
            var count_exists = 0
            for (op_i = 0, op_j = op_rows.length; op_i < op_j; ++op_i) {
                if(op_rows[op_i]){
                    op_cells = op_rows[op_i].getElementsByTagName('td');
                    if(document.getElementById('surface_' + op_i)){
                      var table_surface = document.getElementById('surface_' + op_i).textContent;
                      if(table_surface.includes(customerId)){
                            count_exists += 1;
                        }
                    }
                }
            }
            return count_exists;
		},
		fill_color_full_mouth : function( adult_child, color_fill) {
		    if(adult_child == 'child'){
		        for (var selected_all_tooth = 1; selected_all_tooth <= 20; selected_all_tooth++) {
                    self.$('#childview_' + selected_all_tooth + "_center").attr('fill', color_fill);
                    self.$('#childview_' + selected_all_tooth + "_top").attr('fill', color_fill);
                    self.$('#childview_' + selected_all_tooth + "_right").attr('fill', color_fill);
                    self.$('#childview_' + selected_all_tooth + "_left").attr('fill', color_fill);
                    self.$('#childview_' + selected_all_tooth + "_bottom").attr('fill', color_fill);
                }
		    }
		    if(adult_child == 'adult'){
		        for (var selected_all_tooth = 1; selected_all_tooth <= 32; selected_all_tooth++) {
                    self.$('#view_' + selected_all_tooth + "_center").attr('fill', color_fill);
                    self.$('#view_' + selected_all_tooth + "_top").attr('fill', color_fill);
                    self.$('#view_' + selected_all_tooth + "_right").attr('fill', color_fill);
                    self.$('#view_' + selected_all_tooth + "_left").attr('fill', color_fill);
                    self.$('#view_' + selected_all_tooth + "_bottom").attr('fill', color_fill);
                }
		    }
		},
		fill_color_upper_lower_mouth : function( adult_child, UpperLower, color_state ,color_fill) {
		    var image1 = $('#UT');
            var image2 = $('#LT');
            var image3 = $('#childUT');
            var image4 =$('#childLT');
		    var keystr = '';
		    var surf_color_fill = color_fill;
		    if(UpperLower == 'Upper'){
		        if(adult_child == 'child'){
                    for (var i=1; i<11; i++) {
                        keystr += ',chcap_'+i;
                    }
                }
                if(adult_child == 'adult'){
                    for (var i=1; i<17;i++) {
                        keystr += ',toothcap_'+i;
                    }
                }
		    }
		    if(UpperLower == 'Lower'){
		        if(adult_child == 'child'){
                    for (var i=11; i<=20; i++) {
                        keystr += ',chcap_'+i;
                    }
                }
                if(adult_child == 'adult'){
                    for (var i=17; i<=33;i++) {
                        keystr += ',toothcap_'+i;
                    }
                }
		    }
		    var each_slf_id =  String(keystr);
		    if(color_state == 'reset'){
                image1.mapster('set', false, String(each_slf_id), {fillColorMask: surf_color_fill});
                image2.mapster('set', false, String(each_slf_id), {fillColorMask: surf_color_fill});
                image3.mapster('set', false, String(each_slf_id), {fillColorMask: surf_color_fill});
                image4.mapster('set', false, String(each_slf_id), {fillColorMask: surf_color_fill});
            }
            else{
                image1.mapster('set', true, String(each_slf_id));
                image2.mapster('set', true, String(each_slf_id));
                image3.mapster('set', true, String(each_slf_id));
                image4.mapster('set', true, String(each_slf_id));
            }

		},
		full_mouth_select_deselect_action : function(self) {
		    var sel_table = document.getElementById('selected_list_table');
            var sel_rows = sel_table.getElementsByTagName('tr');
            var sel_i, sel_j, sel_cells;
            var full_mouth_selected = self.exists_in_selected_surface('Full_mouth');
            if(! full_mouth_selected){
                 for (sel_i = 1, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                     $('#surface_selected').remove();
                 }
                 var table_selected_str = '';
                 table_selected_str += '<tr id="surface_Full_mouth">';
                 table_selected_str += '<td>' + 'Full_mouth' + '</td>';
                 table_selected_str += '</tr>';
                 $('#selected_list_tbody').append(table_selected_str);
            }
            else{
                for (sel_i = 1, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                     if(sel_rows[sel_i] && sel_rows[sel_i].id == 'surface_Full_mouth'){
                         sel_rows[sel_i].remove();
                    }
                }
            }
		},
		upper_mouth_select_deselect_action : function(self) {
		    var upper_mouth_selected = self.exists_in_selected_surface('Upper_Jaw');
            if(! upper_mouth_selected){
                var sel_table = document.getElementById('selected_list_table');
                var sel_rows = sel_table.getElementsByTagName('tr');
                var sel_i, sel_j, sel_cells, customerId;
                 for ( var m=1; m<17;m++){
                    var toothcap_str = 'toothcap_'+m;
                    for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                        if(sel_rows[sel_i]){
                            sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                            if (!sel_cells.length) {
                                continue;
                            }
                            customerId = sel_cells[0].innerHTML;
                            if(customerId==toothcap_str){
                                sel_rows[sel_i].remove();
                            }
                            if(customerId=='Upper_Jaw'){
                                sel_rows[sel_i].remove();
                            }
                        }
                    }
                 }
                 var table_selected_str = '';
                 table_selected_str += '<tr id="toothmap_Upper_Jaw">';
                 table_selected_str += '<td>' + 'Upper_Jaw' + '</td>';
                 table_selected_str += '</tr>';
                 $('#selected_list_tbody').append(table_selected_str);
            }
            else{
                var sel_table = document.getElementById('selected_list_table');
                var sel_rows = sel_table.getElementsByTagName('tr');
                var sel_i, sel_j, sel_cells;
                    for (sel_i = 1, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                         if(sel_rows[sel_i] && sel_rows[sel_i].id == 'toothmap_Upper_Jaw'){
                             sel_rows[sel_i].remove();
                        }
                    }
            }
		},
		lower_mouth_select_deselect_action : function(self) {
		    var upper_mouth_selected = self.exists_in_selected_surface('Lower_Jaw');
            if(! upper_mouth_selected){
                var sel_table = document.getElementById('selected_list_table');
                var sel_rows = sel_table.getElementsByTagName('tr');
                var sel_i, sel_j, sel_cells, customerId;
                for ( var m=17; m<=33;m++){
                    var toothcap_str = 'toothcap_'+m;
                    for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                        if(sel_rows[sel_i]){
                            sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                            if (!sel_cells.length) {
                                continue;
                            }
                            customerId = sel_cells[0].innerHTML;
                            if(customerId==toothcap_str){
                                sel_rows[sel_i].remove();
                            }
                            if(customerId=='Lower_Jaw'){
                                sel_rows[sel_i].remove();
                            }
                        }
                    }
                 }
                 var table_selected_str = '';
                 table_selected_str += '<tr id="toothmap_Lower_Jaw">';
                 table_selected_str += '<td>' + 'Lower_Jaw' + '</td>';
                 table_selected_str += '</tr>';
                 $('#selected_list_tbody').append(table_selected_str);
            }
            else{
                var sel_table = document.getElementById('selected_list_table');
                var sel_rows = sel_table.getElementsByTagName('tr');
                var sel_i, sel_j, sel_cells;
                    for (sel_i = 1, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                         if(sel_rows[sel_i] && sel_rows[sel_i].id == 'toothmap_Lower_Jaw'){
                             sel_rows[sel_i].remove();
                        }
                    }
            }
		},
		clear_selected_surface_function  : function(self) {
			    self.deselect_upper_lower_full_mouth();
			    var sel_table = document.getElementById('selected_list_table');
                var sel_rows = sel_table.getElementsByTagName('tr');
                var sel_i, sel_j, sel_cells, customerId;
                for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                    if(sel_rows[sel_i]){
                        sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                        if (!sel_cells.length) {
                            continue;
                        }
                        var new_converted_tooth_map = "";
                        var new_number = "";
                        var new_customerId = "";
                        var is_surface = false;
                        var is_tooth_map = false;
                        customerId = sel_cells[0].innerHTML;
                        var tooth_map_nameArr = customerId.split('_')
                        if (customerId == 'Full_mouth') {is_surface=true;}
                        if (customerId == 'Upper_Jaw') {is_tooth_map=true;}
                        if (customerId == 'Lower_Jaw') {is_tooth_map=true;}
                        for(var i = 0; i < tooth_map_nameArr.length; i++) {
                            tooth_map_nameArr[i] = tooth_map_nameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                            if(!isNaN(tooth_map_nameArr[i])){
                                if (i == 0) {is_surface=true;}
                                if (i == 1) {is_tooth_map=true;}
                                if (type == 'palmer') {
                                  new_customerId = customerId.replace(tooth_map_nameArr[i], _.invert(Palmer)[tooth_map_nameArr[i]]);
                                  new_number = _.invert(Palmer)[tooth_map_nameArr[i]];
                                }
                                else if (type == 'iso') {
                                    new_customerId = customerId.replace(tooth_map_nameArr[i], _.invert(Iso)[tooth_map_nameArr[i]]);
                                    new_number = _.invert(Iso)[tooth_map_nameArr[i]];
                                }
                                else{
                                    new_customerId = customerId.replace(tooth_map_nameArr[i], tooth_map_nameArr[i]);
                                    new_number = tooth_map_nameArr[i];
                                }
                            }
                        }
                        var is_already_exists_below = self.exists_in_operations_table(customerId);
                        if(is_surface){
                            if (customerId == 'Full_mouth') {
                                var surf_color_fill = "white";
                                self.fill_color_full_mouth('child', surf_color_fill);
                                self.fill_color_full_mouth('adult', surf_color_fill);
                            }
                            else{
                                var class_surface = document.getElementsByClassName(String(new_customerId));
                                var surf_i;
                                for (surf_i = 0; surf_i < class_surface.length; surf_i++) {
                                  if(is_already_exists_below){
                                    var surf_color_fill = "orange";
                                    class_surface[surf_i].style.fill = surf_color_fill;
                                  }
                                  else{
                                    var surf_color_fill = "white";
                                    class_surface[surf_i].style.fill = surf_color_fill;
                                    }
                                }
                            }
                        }
                        if(is_tooth_map){
                            var image1 = $('#UT');
                            var image2 = $('#LT');
                            var image3 = $('#childUT');
                            var image4 =$('#childLT');
                            var white_color_fill = "FFFFFF";
                            var color_state = "reset";
                            if (customerId == 'Upper_Jaw') {
                                self.fill_color_upper_lower_mouth('child', 'Upper', color_state, white_color_fill);
                                self.fill_color_upper_lower_mouth('adult', 'Upper', color_state, white_color_fill);
                            }
                            else if (customerId == 'Lower_Jaw') {
                                self.fill_color_upper_lower_mouth('child', 'Lower', color_state, white_color_fill);
                                self.fill_color_upper_lower_mouth('adult', 'Lower', color_state, white_color_fill);
                            }
                            else{
                                if(is_already_exists_below){
                                    var tooth_map_color_fill = "FF000C";
                                    new_customerId = String(new_customerId);
                                    image1.mapster('set', true, new_customerId);
                                    image2.mapster('set', true, new_customerId);
                                    image3.mapster('set', true, new_customerId);
                                    image4.mapster('set', true, new_customerId);
                                }
                                else{
                                    var tooth_map_color_fill = "FFFFFF";
                                    new_customerId = String(new_customerId);
                                    image1.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                    image2.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                    image3.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                    image4.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                }
                            }
                        }
                    }
                }
			    $('#selected_list_tbody').empty();
			},
		renderElement : function(parent, options) {
			this._super(parent);
			var self = this;

            self.$('#select_full_mouth').change(function() {
        		if (this.checked) {
					full_mouth_selected = 1;
				} else {
					full_mouth_selected = 0;
				}
             	var miss = 0;
				var full_mouth = new Array();
//				zzzzzzzzzzz start
                self.full_mouth_select_deselect_action(self);
//              zzzzzzzzzzz end
				for (var select_all_tooth = 1; select_all_tooth <= 32; select_all_tooth++) {
					miss = 0;
					for (var each_from_missing = 0; each_from_missing < Missing_Tooth.length; each_from_missing++) {
						if (Missing_Tooth[each_from_missing] == parseInt(select_all_tooth)) {
							miss = 1;
							break;
						}
					}
					if (!miss && full_mouth_selected) {
						full_mouth.push(select_all_tooth);
						self.$('#view_' + select_all_tooth + "_center").attr('fill', 'orange');
						self.$('#view_' + select_all_tooth + "_top").attr('fill', 'orange');
						self.$('#view_' + select_all_tooth + "_right").attr('fill', 'orange');
						self.$('#view_' + select_all_tooth + "_left").attr('fill', 'orange');
						self.$('#view_' + select_all_tooth + "_bottom").attr('fill', 'orange');
					} else if (!miss) {
						full_mouth.push(select_all_tooth);
						if (document.getElementById('view_'+select_all_tooth+"_center").classList[3] == 0)
							self.$('#view_' + select_all_tooth + "_center").attr('fill', 'white');
						if (document.getElementById('view_'+select_all_tooth+"_top").classList[3] == 0)
							self.$('#view_' + select_all_tooth + "_top").attr('fill', 'white');
						if (document.getElementById('view_'+select_all_tooth+"_bottom").classList[3] == 0)
							self.$('#view_' + select_all_tooth + "_bottom").attr('fill', 'white');
						if (document.getElementById('view_' + select_all_tooth + "_right").classList[3] == 0)
							self.$('#view_' + select_all_tooth + "_right").attr('fill', 'white');
						if (document.getElementById('view_'+select_all_tooth+"_left").classList[3] == 0)
							self.$('#view_' + select_all_tooth + "_left").attr('fill', 'white');
					}
				}
				full_mouth_teeth = full_mouth;
			});
			self.$('#adult').click(function() {
                self.clear_selected_surface_function(self);
			});
			self.$('#child').click(function() {
			    self.clear_selected_surface_function(self);
			});
			self.$('#select_full_mouth_child').change(function() {
        		if (this.checked) {
					full_mouth_selected = 1;
				} else {
					full_mouth_selected = 0;
				}
             	var miss = 0;
				var full_mouth = new Array();
				self.full_mouth_select_deselect_action(self);
				for (var select_all_tooth = 1; select_all_tooth <= 20; select_all_tooth++) {
					miss = 0;
					for (var each_from_missing = 0; each_from_missing < Missing_Tooth.length; each_from_missing++) {
						if (Missing_Tooth[each_from_missing] == parseInt(select_all_tooth)) {
							miss = 1;
							break;
						}
					}
					if (!miss && full_mouth_selected) {
						full_mouth.push(select_all_tooth);
						self.$('#childview_' + select_all_tooth + "_center").attr('fill', 'orange');
						self.$('#childview_' + select_all_tooth + "_top").attr('fill', 'orange');
						self.$('#childview_' + select_all_tooth + "_right").attr('fill', 'orange');
						self.$('#childview_' + select_all_tooth + "_left").attr('fill', 'orange');
						self.$('#childview_' + select_all_tooth + "_bottom").attr('fill', 'orange');
					} else if (!miss) {
						full_mouth.push(select_all_tooth);
						if (document.getElementById('childview_'+select_all_tooth+"_center").classList[3] == 0)
							self.$('#childview_' + select_all_tooth + "_center").attr('fill', 'white');
						if (document.getElementById('childview_'+select_all_tooth+"_top").classList[3] == 0)
							self.$('#childview_' + select_all_tooth + "_top").attr('fill', 'white');
						if (document.getElementById('childview_'+select_all_tooth+"_bottom").classList[3] == 0)
							self.$('#childview_' + select_all_tooth + "_bottom").attr('fill', 'white');
						if (document.getElementById('childview_' + select_all_tooth + "_right").classList[3] == 0)
							self.$('#childview_' + select_all_tooth + "_right").attr('fill', 'white');
						if (document.getElementById('childview_'+select_all_tooth+"_left").classList[3] == 0)
							self.$('#childview_' + select_all_tooth + "_left").attr('fill', 'white');
					}
				}
				full_mouth_teeth = full_mouth;
			});
//	        zzzzzzzzzzz start
			self.$('#select_upper_mouth_child').change(function() {
			    self.upper_mouth_select_deselect_action(self);
			});
			self.$('#select_upper_mouth').change(function() {
			    self.upper_mouth_select_deselect_action(self);
			});
			self.$('#select_lower_mouth_child').change(function() {
			    self.lower_mouth_select_deselect_action(self);
			});
			self.$('#select_lower_mouth').change(function() {
			    self.lower_mouth_select_deselect_action(self);
			});
//          zzzzzzzzzzz end
            self.$('.jaw').click(function() {
                $('input:checkbox[name=mouthselection]').each(function() {
                	if($(this).is(':checked')) {
                		var selected_chkbox =($(this).val());
                		var keystr = 'tooth';
                		if (selected_chkbox == 'uppermouth_child') {
                            for (var i=1; i<11; i++)
                                keystr += ',chcap_'+i;
                            localStorage.setItem('childupperkeys', keystr);
                            upper_mouth_selected = 1;
                        }
                        if (selected_chkbox == 'lowermouth_child') {
                            for (var i=11; i<=20; i++)
                                keystr += ',chcap_'+i;
                            localStorage.setItem('childlowerkeys', keystr);
                            lower_mouth_selected = 1;
                        }
                		if (selected_chkbox == 'uppermouth'){
                			for ( var i=1; i<17;i++)
                				keystr += ',toothcap_'+i;
                			localStorage.setItem('upperkeys', keystr);
                			upper_mouth_selected = 1;
                		};
                		if (selected_chkbox == 'lowermouth'){
                			for ( var i=17; i<=33;i++)
                				keystr += ',toothcap_'+i;
                			localStorage.setItem('lowerkeys', keystr);
                			lower_mouth_selected = 1;
                		};
                	}
                });
            });

				/*change amount field to readonly based on status*/
                self.$('.myButton').click(function() {
					var current_obj = this;
					var found = $('.selected_operation').find('.progress_table_actions');
					_.each(found, function(each_found) {
						if (each_found.innerText != 'missing') {
							var actual_id = each_found.id.substr(7);

							$('#operation_'+actual_id).attr('line-change', 'update');
							$('#dentist_'+actual_id).text(user_name);
							if ($('#status_'+actual_id).attr('status_name') != 'completed') {
								if (($('#status_'+actual_id).attr('status_name') == 'in_progress') &&
									(current_obj.id == 'in_progress')) {
									$('#status_'+actual_id).attr('line_status', 'old');
								}
								$('#status_'+actual_id).attr('status_name', current_obj.id)
								$('#status_'+actual_id)[0].innerHTML = (current_obj.innerHTML).trim();
								if ($('#inv_status_'+actual_id).attr("value") == "draft") {
								    $('#inv_status_'+actual_id).attr("value", "to_invoice");
								}
								$('#amount_'+actual_id+' input').attr('readonly', true);

							}
							else if($('#status_'+actual_id).attr('status_name') == 'completed') {
								$('#status_'+actual_id)[0].innerHTML = $('#completed').text().trim();
							}
						}
						if ($('#status_'+actual_id).attr('status_name') != 'planned')
    						self._setDiscountReadonly($(each_found).parent());
					});
					if (!found.length) {
						alert('Please select a record!')
					}

				});

			self.$('#heading').click(function() {
				var found = self.$el.find('.selected_operation');
				if (found) {
					found.removeClass("selected_operation");
				}
			});
			self.$('#close_screen').click(function() {
				self.perform_action().then(function() {
				self.window_close();
             });
			});

			self.$('#back_screen').click(function() {
				self.window_close();
			});

			self.$('#save_screen').click(function() {
				self.perform_action().then(function() {
				location.reload();
             });
			});

			self.$('#take_screenshot').click(function() {
				if ($('#teethchart_child').hasClass("hidden")) {
					html2canvas(document.getElementById('teethchart_adult')).then(function(canvas) {
						var tooth_base64URL = canvas.toDataURL('image/jpeg').replace('image/jpeg', 'image/octet-stream');
						self.$('#img_adult_tooth').attr('href', tooth_base64URL);
						if (self.$('#img_adult_tooth').hasClass("hidden")) {
							self.$('#img_adult_tooth').removeClass("hidden");
						}
						if (!self.$('#img_child_tooth').hasClass("hidden")) {
							self.$('#img_child_tooth').addClass("hidden");
						}
						rpc.query({
							model: 'medical.patient',
							method: 'medical_patient_teeth_attachment',
							args: [self.patient_id, self.appointment_id, tooth_base64URL, true],
						});
					});
				}
				else {
					html2canvas(document.getElementById('teethchart_child')).then(function(canvas) {
						var tooth_base64URL = canvas.toDataURL('image/jpeg').replace('image/jpeg', 'image/octet-stream');
						self.$('#img_child_tooth').attr('href', tooth_base64URL);
						if (self.$('#img_child_tooth').hasClass("hidden")) {
							self.$('#img_child_tooth').removeClass("hidden");
						}
						if (!self.$('#img_adult_tooth').hasClass("hidden")) {
							self.$('#img_adult_tooth').addClass("hidden");
						}
						rpc.query({
							model: 'medical.patient',
							method: 'medical_patient_teeth_attachment',
							args: [self.patient_id, self.appointment_id, tooth_base64URL, true],
						});
					});
				}
				html2canvas(document.getElementById('procedure_tab')).then(function(canvas) {
//					var toothline_base64URL = canvas.toDataURL('image/jpeg').replace('image/jpeg', 'image/octet-stream');
					var tooth_base64URL = canvas.toDataURL('image/jpeg').replace('image/jpeg', 'image/octet-stream');
					self.$('#img_tooth_line').attr('href', toothline_base64URL);
					if (self.$('#img_tooth_line').hasClass("hidden")) {
						self.$('#img_tooth_line').removeClass("hidden");
					}
					rpc.query({
						model: 'medical.patient',
						method: 'medical_patient_teeth_attachment',
						args: [self.patient_id, self.appointment_id, toothline_base64URL, false],
					});
					/*image2.onload = checkload;
					image2.src = toothline_base64URL;*/
				});

				/*var img1 = document.getElementById('img_adult_tooth');
				var img2 = document.getElementById('img_tooth_line');
				var canvas = document.getElementById('myCanvas');
				var context = canvas.getContext('2d');
				context.globalAlpha = 1.0;
				context.drawImage(img1, 0, 0);
				context.globalAlpha = 0.5; //Remove if pngs have alpha
				context.drawImage(img2, 0, 0);*/
			});
			self.$('#clear_selected_surface').click(function() {
			    self.clear_selected_surface_function(self);
			});
			self.$('#init_examination').click(function() {
				if (self.initial_exam == false) {
					self.initial_exam = true;
					$('#init_examination').css("background", "#5cb85c");
					$('#screen_shorts').removeClass("hidden");
				}
				else {
					self.initial_exam = false;
					$('#init_examination').css("background", "gainsboro");
					$('#screen_shorts').addClass("hidden");
					$('#img_child_tooth').addClass("hidden");
					$('#img_adult_tooth').addClass("hidden");
					$('#img_tooth_line').addClass("hidden");
				}
				localStorage.setItem('initial_exam', self.initial_exam);
				self.initial_examination(self.initial_exam);
			});

			rpc.query({
                model: 'teeth.code',
                method: 'get_teeth_code',
                args: [this.patient_id],
            })
            .then(function(res){
				var name = "";
				var j = 0;
				var k = 7;
				var l = 0;

				if (type == 'universal') {
					for (var i = 0; i < 16; i++) {
						if (i<10){
							name = "<td  width = '46px' id='teeth_" + i + "'>" +res[i] + "</td>";
						}
						else{
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						}
						$('#upper_teeths').append(name);
					}
					for (var i = 31; i > 15; i--) {
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#lower_teeths').append(name);
					}
				} else if (type == 'palmer') {
					/*for (var i = 7; i >= 0; i--) {
						name = "<td  width = '47px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#upper_teeths').append(name);

					}*/
					for (var i = 0; i <= 15; i++) {
						name = "<td  width = '47px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#upper_teeths').append(name);
					}
					/*for (var i = 23; i > 15; i--) {

						name = "<td  width = '47px' id='teeth_" + i + "'>" + res[k] + "</td>";
						$('#lower_teeths').append(name);
						k--;
					}*/
					for (var i = 16; i < 32; i++) {
						name = "<td  width = '47px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#lower_teeths').append(name);
					}

				} else if (type == 'iso') {
					for (var i = 0; i <= 7; i++) {
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#upper_teeths').append(name);
					}
					for (var i = 8; i <= 15; i++) {
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#upper_teeths').append(name);
					}
					for (var i = 31; i >= 24; i--) {
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#lower_teeths').append(name);
					}
					for (var i = 23; i >= 16; i--) {
						name = "<td  width = '46px' id='teeth_" + i + "'>" + res[i] + "</td>";
						$('#lower_teeths').append(name);
					}
				}
			});
		},

		perform_action : function() {

			var $def = $.Deferred();
			var treatment_lines_2 = new Array();
			for (var op = 1; op <= operation_id; op++) {
				var op_id = document.getElementById('operation_' + op);
				if (op_id) {
					treatment_lines_2.push(this._process_surface_lines(op));
				}

			}
			rpc.query({
                model: 'medical.patient',
                method: 'create_lines',
                args: [this.patient_id, treatment_lines_2, this.patient_id, this.appointment_id],
            })
            .then(function(res) {
               treatment_lines_2 = new Array();
               $def.resolve(res);
            });

            for (var index = 0; index < list_delete_line_id.length; index++) {
                rpc.query({
                    model: 'medical.patient',
                    method: 'unlink_treatment',
                    args: [list_delete_line_id[index]]
                }).then(function (res) {
                    console.log("unlink_treatment status", list_delete_line_id[index], " ", res);
                });
            }
			return $def;
		},
		window_close : function() {
			close = true;
			localStorage.removeItem('test');
            localStorage.removeItem('upperkeys');
            localStorage.removeItem('lowerkeys');
            localStorage.removeItem('initial_exam');
            $(".navbar").removeClass('hidden');
            $(".o_sub_menu").removeClass('hidden');
            $(".breadcrumb").removeClass('hidden');
			$(".o_cp_searchview").removeClass('hidden');
			$(".o_cp_left").removeClass('hidden');
			$(".o_cp_right").removeClass('hidden');
			window.history.back();
			setTimeout(function(){ location.reload(); }, 5);
		},
		_onOpenEvent: function () {
            var self = this;

	        rpc.query({
	            model: 'medical.appointment',
	            method: 'get_formview_id',
	            args: []
	        }).then(function (viewId) {
	            self.do_action({
	                type:'ir.actions.act_window',
	                res_id: 112,
	                res_model: 'medical.appointment',
	                views: [[viewId || false, 'form']],
	                target: 'current',
	                context: event.context || self.context,
	            });
	        });
	        return;
	    },
		check_if_tooth_present : function(tooth_id) {
			for (var i = 0; i < treatment_lines.length; i++) {
				if (treatment_lines[i]['tooth_id'] == tooth_id) {
					return 1;
				}
			}
			return 0;
		},
		execute_create : function(attrs, self_var, selected_surface_temp) {
			console.log(" inside execute create ---Selected surface temp, selected tooth -- ",selected_surface_temp)
			if (!selected_surface_temp) {
				selected_surface_temp = selected_surface;
			}
			var self = this;

			var tooth_present = 0;


			 tooth_present = this.check_if_tooth_present(selected_tooth);

			var record = new Array();
			record['treatments'] = new Array();
			record['tooth_id'] = selected_tooth;
			var surfaces = new Array();
			if (!selected_tooth){
				alert('Please select the surface first !');
			}
			_.each(selected_surface_temp, function(each_surface) {
				if($('#'+each_surface).attr('class')){
				var surface = ($('#'+each_surface).attr('class')).split(' ')[1];
				surfaces.push(surface);
				}
			});
			var d = new Array();
			d = {
				'treatment_id' : selected_treatment['treatment_id'],
				'vals' : surfaces
			};
			var selected_tooth_temp = selected_tooth;

			if (attrs) {
				if(selected_tooth){
				if (!tooth_present) {
					record['treatments'].push(d);
					treatment_lines.push(record);
					/*CHANGED HERE*/
					this.put_data(self_var, surfaces,
						selected_tooth_temp,
						selected_surface_temp, 'planned',
						false, false,
						false,false,false,0,"draft",
						false,
						session.uid,
						user_name
					);
				} else {
					var treatment_present = 0;
					for (var i = 0; i < treatment_lines.length; i++) {
						if (treatment_lines[i]['tooth_id'] == parseInt(selected_tooth_temp)) {
							for (var each_trts = 0; each_trts < treatment_lines[i]['treatments'].length; each_trts++) {
								if (treatment_lines[i]['treatments'][each_trts].treatment_id == selected_treatment['treatment_id']) {
									treatment_present = 1;
									break;
								}
							}
							if (!treatment_present) {
								var x = treatment_lines;
								treatment_lines[i]['treatments'].push(d);
								/*CHANGED HERE*/
								var doc_name = self.doctor_name ? self.doctor_name : user_name;
								this.put_data(self_var, surfaces,
									selected_tooth_temp,
									selected_surface_temp,
									false, false,
									false, false,
									false, false, 0, "draft",
									false,
									session.uid,
									user_name
								);
							}
						}
					}

				}
			}
			} else {
				if (!tooth_present && !tooth_by_part) {
					record['treatments'].push(d);
					treatment_lines.push(record);
					surfaces.length = 0;
					/*CHANGED HERE*/
					var doc_name = self.doctor_name ? self.doctor_name : user_name;
					this.put_data(self_var,
						surfaces, selected_tooth_temp,
						false, false,
						false, false,
						false, false, false, 0, "draft",
						false,
						session.uid,
						user_name
					);
				} else {
				        record['treatments'].push(d);
					    treatment_lines.push(record);
					    surfaces.length = 0;
				        selected_tooth_temp = toothmap_id;

						surfaces.push(tid);
						/*CHANGED HERE*/
						var doc_name = self.doctor_name ? self.doctor_name : user_name;
						this.put_data(self_var, surfaces,
							selected_tooth_temp, '',
							'planned', false, false,
							false, false, false, 0, "draft",
							false,
							session.uid,
							user_name
						);


				}
			}
		},
		get_treatment_charge : function(treatment_id) {
			var $def = $.Deferred();
			rpc.query({
	                model: 'product.product',
	                method: 'get_treatment_charge',
	                args: [treatment_id],
	            })
	            .then(function(res){
	                $def.resolve(res);
	           });
			return $def;
		},

		decrement_thread : function(selected_surf) {
		    try {
                _.each(selected_surf, function(ss) {
                    var prev_cnt = ($('#'+ss).attr('class').split(' ')[3]);
                    var new_cnt = String(parseInt(prev_cnt) - 1);
                    document.getElementById(ss).classList.remove(prev_cnt);
                    document.getElementById(ss).classList.add(new_cnt);
                });
            }
            catch (err) {}
		},

		increment_thread : function(selected_surf) {
		    try {
                _.each(selected_surf, function(ss) {
                    var m = $('#' + ss).attr('class').split(' ');
                    var prev_cnt = ($('#'+ss).attr('class').split(' ')[3]);
                    var new_cnt = String(parseInt(prev_cnt) + 1);
                    document.getElementById(ss).classList.remove(prev_cnt);
                    document.getElementById(ss).classList.add(new_cnt);
                });
            }
            catch (err) {}
		},
		convert_surface_toothmap_based_numbering  : function(teeth_type, selected_surface_toothmap) {
              var new_surface_toothmap = "";
              var surfacenameArr = selected_surface_toothmap.split('_')
              for(var i = 0; i < surfacenameArr.length; i++) {
                surfacenameArr[i] = surfacenameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                if(!isNaN(surfacenameArr[i])){
                    if (teeth_type == 'palmer') {
                      new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i],Palmer[surfacenameArr[i]]);
                    }
                    else if (teeth_type == 'iso') {
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i],Iso[surfacenameArr[i]]);
                    }
                    else{
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i], surfacenameArr[i]);
                    }
                }
              }
              return new_surface_toothmap;
		},
		delete_color_remove  : function(self, type, surface_vals, tooth_id) {
                if(surface_vals.includes(',')){
                    var surfacenameArr = surface_vals.split(',')
                    var new_surface_vals = surface_vals;
                    for(var i = 0; i < surfacenameArr.length; i++) {
                        var new_single_surface_vals = self.convert_invert_surface_toothmap_based_numbering(type, surfacenameArr[i]);
                        new_surface_vals = new_surface_vals.replace(surfacenameArr[i], new_single_surface_vals);
                    }
                }
                else{
                    var new_single_surface_vals = self.convert_invert_surface_toothmap_based_numbering(type, surface_vals);
                    var new_surface_vals = new_single_surface_vals;
                }
                if(tooth_id.includes(',')){
                    var toothnameArr = tooth_id.split(',')
                    var new_tooth_id = tooth_id;
                    for(var i = 0; i < toothnameArr.length; i++) {
                        var new_single_tooth_vals = self.convert_invert_tooth_based_numbering(type, toothnameArr[i]);
                        new_tooth_id = new_tooth_id.replace(toothnameArr[i], new_single_tooth_vals);
                    }
                }
                else{
                    var new_single_tooth_vals = self.convert_invert_tooth_based_numbering(type, tooth_id);
                    var new_tooth_id = new_single_tooth_vals;
                }
                if(surface_vals.includes(',')){
                    var new_surface_valsArr = surface_vals.split(',')
                }
                else{
                    var new_surface_valsArr = [surface_vals];
                }
                var customerId;
                for (var surface_i = 0; surface_i < new_surface_valsArr.length; surface_i++) {
                    var new_number = "";
                    var new_customerId = "";
                    var is_surface = false;
                    var is_tooth_map = false;
                    customerId = new_surface_valsArr[surface_i];
                    var tooth_map_nameArr = customerId.split('_')
                    if (customerId == 'Full_mouth') {is_surface=true;}
                    if (customerId == 'Upper_Jaw') {is_tooth_map=true;}
                    if (customerId == 'Lower_Jaw') {is_tooth_map=true;}
                    for(var i = 0; i < tooth_map_nameArr.length; i++) {
                        tooth_map_nameArr[i] = tooth_map_nameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                        if(!isNaN(tooth_map_nameArr[i])){
                            if (i == 0) {is_surface=true;}
                            if (i == 1) {is_tooth_map=true;}
                            if (type == 'palmer') {
                              new_customerId = customerId.replace(tooth_map_nameArr[i], _.invert(Palmer)[tooth_map_nameArr[i]]);
                              new_number = _.invert(Palmer)[tooth_map_nameArr[i]];
                            }
                            else if (type == 'iso') {
                                new_customerId = customerId.replace(tooth_map_nameArr[i], _.invert(Iso)[tooth_map_nameArr[i]]);
                                new_number = _.invert(Iso)[tooth_map_nameArr[i]];
                            }
                            else{
                                new_customerId = customerId.replace(tooth_map_nameArr[i], tooth_map_nameArr[i]);
                                new_number = tooth_map_nameArr[i];
                            }
                        }
                    }
                    var count_exists = self.count_exists_in_operations_table(customerId);
                    if(is_surface){
                        if (customerId == 'Full_mouth') {
//                            var surf_color_fill = "white";
//                            self.fill_color_full_mouth('child', surf_color_fill);
//                            self.fill_color_full_mouth('adult', surf_color_fill);
                        }
                        else{
                            var class_surface = document.getElementsByClassName(String(new_customerId));
                            var surf_i;
                            for (surf_i = 0; surf_i < class_surface.length; surf_i++) {
                              if(count_exists>1){
                                var surf_color_fill = "orange";
                                class_surface[surf_i].style.fill = surf_color_fill;
                              }
                              else{
                                var surf_color_fill = "white";
                                class_surface[surf_i].style.fill = surf_color_fill;
                                }
                            }
                        }
                    }
                    if(is_tooth_map){
                        var image1 = $('#UT');
                        var image2 = $('#LT');
                        var image3 = $('#childUT');
                        var image4 =$('#childLT');
                        var white_color_fill = "FFFFFF";
                        var color_state = "reset";
                        if (customerId == 'Upper_Jaw') {
//                            self.fill_color_upper_lower_mouth('child', 'Upper', color_state, white_color_fill);
//                            self.fill_color_upper_lower_mouth('adult', 'Upper', color_state, white_color_fill);
                        }
                        else if (customerId == 'Lower_Jaw') {
//                            self.fill_color_upper_lower_mouth('child', 'Lower', color_state, white_color_fill);
//                            self.fill_color_upper_lower_mouth('adult', 'Lower', color_state, white_color_fill);
                        }
                        else{
                            if(count_exists>1){
                                var tooth_map_color_fill = "FF000C";
                                new_customerId = String(new_customerId);
                                image1.mapster('set', true, new_customerId);
                                image2.mapster('set', true, new_customerId);
                                image3.mapster('set', true, new_customerId);
                                image4.mapster('set', true, new_customerId);
                            }
                            else{
                                var tooth_map_color_fill = "FFFFFF";
                                new_customerId = String(new_customerId);
                                image1.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                image2.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                image3.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                                image4.mapster('set', false, new_customerId, {fillColorMask: tooth_map_color_fill});
                            }
                        }
                    }
                }

		},
		convert_invert_surface_toothmap_based_numbering  : function(teeth_type, selected_surface_toothmap) {
              var new_surface_toothmap = selected_surface_toothmap;
              var surfacenameArr = selected_surface_toothmap.split('_')
              for(var i = 0; i < surfacenameArr.length; i++) {
                surfacenameArr[i] = surfacenameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                if(!isNaN(surfacenameArr[i])){
                    if (teeth_type == 'palmer') {
                      new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i], _.invert(Palmer)[surfacenameArr[i]]);
                    }
                    else if (teeth_type == 'iso') {
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i],_.invert(Iso)[surfacenameArr[i]]);
                    }
                    else{
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i], surfacenameArr[i]);
                    }
                }
              }
              return new_surface_toothmap;
		},
		convert_invert_tooth_based_numbering : function(teeth_type, selected_surface_toothmap) {
              var new_surface_toothmap = selected_surface_toothmap;
              var surfacenameArr = selected_surface_toothmap.split(',')
              for(var i = 0; i < surfacenameArr.length; i++) {
                if(!isNaN(surfacenameArr[i])){
                    if (teeth_type == 'palmer') {
                      new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i], _.invert(Palmer)[surfacenameArr[i]]);
                    }
                    else if (teeth_type == 'iso') {
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i],_.invert(Iso)[surfacenameArr[i]]);
                    }
                    else{
                        new_surface_toothmap = selected_surface_toothmap.replace(surfacenameArr[i], surfacenameArr[i]);
                    }
                }
              }
              return new_surface_toothmap;
		},
		get_teeth_type_based_numbering  : function(teeth_type, selected_tooth_temp) {
              var tooth_selected_arrays = new Array();
              var toothnameArr = selected_tooth_temp.split(',')
              for(var i = 0; i < toothnameArr.length; i++) {
                toothnameArr[i] = toothnameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                if(!isNaN(toothnameArr[i])){
                    if (teeth_type == 'palmer') {
                      if(!tooth_selected_arrays.includes(toothnameArr[i])){
                        tooth_selected_arrays.push(toothnameArr[i]);
                      }
                    }
                    if (teeth_type == 'iso') {
                        if(!tooth_selected_arrays.includes(toothnameArr[i])){
                            tooth_selected_arrays.push(toothnameArr[i]);
                        }
                    }
                }
                if (toothnameArr[i].includes('Full Mouth') || toothnameArr[i].includes('Full_mouth')){
                    if(!tooth_selected_arrays.includes('Full Mouth')){
                        tooth_selected_arrays.push('Full Mouth');
                    }
                }
                if (toothnameArr[i].includes('Upper Jaw') || toothnameArr[i].includes('Upper_Jaw')){
                    if(!tooth_selected_arrays.includes('Upper Jaw')){
                        tooth_selected_arrays.push('Upper Jaw');
                    }
                }
                if (toothnameArr[i].includes('Lower Jaw') || toothnameArr[i].includes('Lower_Jaw')){
                    if(!tooth_selected_arrays.includes('Lower Jaw')){
                        tooth_selected_arrays.push('Lower Jaw');
                    }
                }
              }
              return tooth_selected_arrays;
		},
		deselect_upper_lower_full_mouth  : function() {
            document.getElementById("select_full_mouth").checked = false;
            document.getElementById("select_full_mouth_child").checked = false;
            document.getElementById("select_upper_mouth").checked = false;
            document.getElementById("select_upper_mouth_child").checked = false;
            document.getElementById("select_lower_mouth").checked = false;
            document.getElementById("select_lower_mouth_child").checked = false;
		},
		put_data_full_mouth : function(self_var, full_mouth_teeth_temp,
									   full_mouth, selected_treatment_temp,
									   status_to_define, mouth_part,
									   created_date, is_prev_record,
									   other_history, dignosis, dignosis_description,
									   amount, inv_status, line_id,
									   doctor_id, doc_name, initial, highlight_color,
									   unit_price, discount_fixed_percent, discount, discount_value) {
            var options = {
                'treatment_id': selected_treatment_temp.treatment_id,
                'unit_price': unit_price,
                'discount_fixed_percent': discount_fixed_percent,
                'discount': discount,
                'discount_value': discount_value,
            };
			if (selected_treatment_temp.action == 'missing') {
				self_var.perform_missing_action(full_mouth_teeth_temp);
			}
			if (full_mouth) {
				var panned_text = $('#planned').text().trim();
				var status_to_define_temp = panned_text;
				var completed_text = $('#completed').text().trim();
				var inprogress_text = $('#in_progress').text().trim();
				var status_defined = status_to_define_temp.toLowerCase();
				if (status_to_define){
					if(status_to_define == 'completed'){
						status_to_define_temp = completed_text;
					} else if(status_to_define == 'in_progress'){
						status_to_define_temp = inprogress_text;
					} else if(status_to_define == 'planned'){
						status_to_define_temp = panned_text;
					}
				}
				var today = new Date();
				if (created_date) {
//				    today = formatDate(today);
					today = created_date;
				}
				var table_str = '';
				var self = this;
				var original_amount = 0;
				this.get_treatment_charge(selected_treatment_temp.treatment_id).then(function(t_charge) {
				    var apply_quantity_on_payment_lines = t_charge[1]
			        var t_charge = t_charge[0]
			        options.unit_price = t_charge;
					if (!t_charge) {
						t_charge = '0.0';
					}
					original_amount = t_charge;
					if (amount > 0) {
						t_charge = amount;
					}
					operation_id += 1;
					var total_teeth = '';
					var surf_list = new Array();
					if (mouth_part == 'Full_mouth') {
					    _.each(full_mouth_teeth_temp, function(each_full_mouth_teeth_temp) {
                            total_teeth += '_' + each_full_mouth_teeth_temp;
                            surf_list.push('view_' + each_full_mouth_teeth_temp + '_center');
                            surf_list.push('view_' + each_full_mouth_teeth_temp + '_right');
                            surf_list.push('view_' + each_full_mouth_teeth_temp + '_left');
                            surf_list.push('view_' + each_full_mouth_teeth_temp + '_top');
                            surf_list.push('view_' + each_full_mouth_teeth_temp + '_bottom');
                        });
                        if(surf_list){
                            self_var.increment_thread(surf_list);
                        }
					}
					total_teeth = total_teeth.substr(1);
					if (other_history)
						table_str += '<tr id="operation_' + operation_id + '" ' +
							'line-change="initial" class="' +
						 total_teeth + '" style="display:none" data-id="'+ line_id +'">';
					else
					    table_str += '<tr id="operation_' + operation_id + '" ' +
							'line-change="initial" class="' +
						    total_teeth + '" data-id="'+ line_id +'">';
					table_str += '<td id = "date_time_' + operation_id + '">' + today + '</td>';
					var initial_checked = '';
					var cls = '';
	                if (localStorage.getItem('initial_exam') == 'true') {
	                	initial_checked += 'checked="checked"';
	                	cls += 'true';
	                }
	                table_str += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
					table_str += '<td class = "' + selected_treatment_temp.treatment_id + '" ' + 'id = "desc_' + operation_id + '">' + selected_treatment_temp.treatment_name + '</td>';
					/*CHANGED HERE - added below line*/
                    /*var multi_tooth = "", multi_surface = "";
                    var selected_surfaces = [];
                    if (self.find_length(self.cached_teeth_list) > 0) {
                        var res = self.get_tooth_surface();
                        multi_tooth = res[0].slice(0, -1);
                        multi_surface = res[1].slice(0, -1);
                    }*/
					/*building diagnosis code and description values*/
					var dignosis_rec, dig_data = "", diag_desc = "", data_id="";
					if (dignosis) {
						try {
							dignosis_rec = dignosis_records_by_id[dignosis.id];
							data_id = dignosis.id;
							dig_data += dignosis_rec.code;
							dig_data += "/" + dignosis_rec.description;
						}
						catch (err) {}
					}
					if(dignosis_description) {
						diag_desc = dignosis_description;
					}
					data_id = (data_id == false) ? '' : data_id;
					table_str += '<td id = "dignosis_' + operation_id + '"><input ' +
						'class="diagnosis_code" id = "dignosis_code_' + operation_id + '" ' +
						' value="'+ dig_data +'" data-id="'+ data_id +'"/>' +
						'</td>';
                    table_str += '<td id = "dignosis_' + operation_id + '"><input ' +
						'class="diagnosis_note" id = "dignosis_note_' + operation_id + '" ' +
						' value="'+ diag_desc +'"/>' +
						'</td>';
					table_str += '<td class = "' + 'all' + '" id = "tooth_' + operation_id + '">' + full_mouth_teeth_temp + '</td>';
					table_str += '<td class="col_stat" id = "status_' + operation_id +
					    '" status_name = "'+status_to_define+'">' +
					    status_to_define_temp + '</td>';
					table_str += '<td id = "surface_' + operation_id + '">'+mouth_part+'</td>';
					table_str += '<td id = "dentist_' + operation_id + '" ' +
						'data-id="' + doctor_id + '">' + doc_name + '</td>';
                    /*setting up input field for amount and will be editable in planned state*/
					if(self.settings_qty_for_teeth && apply_quantity_on_payment_lines){
                        var qty_tooth = full_mouth_teeth_temp.split(',')
                        t_charge = t_charge * qty_tooth.length;
                        original_amount = t_charge;
                    }
                    var amount_input;
					if (status_to_define_temp == 'Planned') {
						amount_input = '<input type="number" ' +
							' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
					}
					else {
						amount_input = '<input type="number" readonly="True"' +
							' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
					}
					table_str += '<td class="col_amt" id = "amount_' + operation_id + '">' + amount_input + '</td>';
					table_str += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' +
					    selected_treatment_temp.action + '</td>';
					table_str += '<td class = "delete_td" id = "delete_' + operation_id + '">' +
					    '<img src = "/pragtech_dental_management/static/src/img/delete.png" height = "20px" width = "20px"/>' + '</td>';
					table_str += '<td class = "copy_td" id = "copy_' + operation_id + '">' +
					    '<img src = "/pragtech_dental_management/static/src/img/copy.png" height = "20px" width = "20px"/>' +
					    '</td>';
					table_str += '<td style = "display:none" id = "previous_' +
					    operation_id + '">' + is_prev_record + '</td>';
//					inv_status = "'"+inv_status+"'";
					table_str += '<td style = "display:none"' +
					     '><input value="' + inv_status + '" id="inv_status_'+operation_id+'" /></td>';

					table_str += '</tr>';
					table_str = self._process_table_row(table_str, options);
					$('#progres_table').append(table_str);
					$('#selected_list_tbody').empty();
                    self.$el.find('.selected_operation').each(function() {
                    	$(this).removeClass('selected_operation');
                    });
                    /*$('#dignosis_code_' + operation_id).focus();
                    $('#operation_' + operation_id).addClass('selected_operation');*/
					/*event for line selection*/
					$('#operation_' + operation_id).click(function() {
						var found = $('#progres_table').find('.selected_operation');
						if (found) {
							found.removeClass("selected_operation");
						}
						var old_class = $(this).attr('class');
						var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';
						$(this).attr('class', new_class);
					});

					if (highlight_color) {
						colormap.push({
							surfaces:   mouth_part,
							color: highlight_color.slice(1)
						});
					}
					var image1 = $('#UT');
				    var image2 = $('#LT');
				    var image3 = $('#childUT');
				    var image4 =$('#childLT');
				    if (highlight_color) {
					    image1.mapster('set', true, mouth_part, {fillColor: highlight_color.slice(1)});
						image2.mapster('set', true, mouth_part, {fillColor: highlight_color.slice(1)});
						image3.mapster('set', true, mouth_part, {fillColor: highlight_color.slice(1)});
						image4.mapster('set', true, mouth_part, {fillColor: highlight_color.slice(1)});
				    }
				    else {
				    	image1.mapster('set', true, mouth_part);
						image2.mapster('set', true, mouth_part);
						image3.mapster('set', true, mouth_part);
						image4.mapster('set', true, mouth_part);
				    }
				    var aarry_mount=[];
				    aarry_mount.push(mouth_part)
					for (var s = 0; s < aarry_mount.length; s++) {
						var surf = aarry_mount[s].split(',')
						for (var k = 0; k < surf.length; k++) {
							if(jQuery.inArray(surf[k], final_surfaces) == -1) {
								$('.' + surf[k]).each(function() {
									var selected_chart;
									var slf = this
									$('.charttype input').each(function() {
										if (this.checked) {
											selected_chart = this.value
											if(highlight_color){
											   var surface_color = highlight_color;
											}
											else{
											    var surface_color = 'orange';
											}
											if(surface_color == 'ff000c'){
											    surface_color = 'orange';
											}
											$('#' + slf.id).attr('fill', surface_color);
										}
									});
							    });
								final_surfaces.push(surf[k]);
							}
						}
					}

					/*CHANGED HERE */
					/*jquery autocomplete feature for diagnosis code*/
					$('#dignosis_code_'+operation_id).autocomplete({
						select: function (event, ui) {
							var terms = split(this.value);
							// remove the current input
							terms.pop();
							// add the selected item
							terms.push(ui.item.label);
							this.value = terms;
							$('#dignosis_code_'+operation_id).attr('data-id', ui.item.value);
							return false;
						},
						source: function (request, response) {
							var res = $.ui.autocomplete.filter(
								dignosis_records, extractLast(request.term));
							response(res);
						},
						position: {
						    collision: "flip"
                        			}
					});

                    /*autocomplete diag code end*/

					$('#delete_' + operation_id).click(function() {
						var x = window.confirm("Are you sure you want to delete?1");
						if (x) {
							update = false;
							cont = false;
							var delStr = '';
							var actual_id = String(this.id).substr(7);
							actual_id = parseInt(actual_id);
							var line_id = $('#operation_' + actual_id).attr('data-id');
							var tabel = document.getElementById('operations');
							var tr = document.getElementById('operation_' + actual_id);
							var tooth = document.getElementById('tooth_' + actual_id);
							var desc_class = $("#desc_" + actual_id).attr('class');
//                            //console.log('the tr is ',tr )


							var status = document.getElementById('status_' + actual_id);
							var status_name = $(status).attr('status_name')
							if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
								alert('Cannot delete');
							}
							else {
                                var action = document.getElementById('action_' + actual_id);
								var action_id = action.innerHTML;
								var tooth_id = $(tooth).text();
								var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
								self.delete_color_remove(self, type, surface_vals, tooth_id);

//								if(mouth_part == 'Full_mouth') {
//								    var tooth_id = tr.className.split('_');
//									var surf_list = new Array();
//									_.each(full_mouth_teeth_temp, function(tooth_id) {
//										surf_list.push('view_' + tooth_id + '_center');
//										surf_list.push('view_' + tooth_id + '_right');
//										surf_list.push('view_' + tooth_id + '_left');
//										surf_list.push('view_' + tooth_id + '_top');
//										surf_list.push('view_' + tooth_id + '_bottom');
//									});
//									self_var.decrement_thread(surf_list);
//
//								    self_var.remove_selection_action(tooth_id);
//                                    if (action_id == 'missing') {
//                                        self_var.remove_missing_action(tooth_id);
//                                    }
//
////									self.excluded_tooth['full_mouth'].push(parseInt(line_id));
//							    }

								tr.parentNode.removeChild(tr);

//								if(mouth_part =='Upper_Jaw') {
//									var u_count = 0;
//									delStr = localStorage.getItem('upperkeys');
//									for (var op = 1; op <= operation_id; op++) {
//										var op_id = document.getElementById('operation_' + op), surface;
//										if (op_id) {
//											surface = document.getElementById('surface_' + op);
//											if ($(surface).text() == "Upper_Jaw") {
//												u_count++;
//											}
//											else {
//											    var tmp = $(surface).text().split("_");
//											    // no upperjaw , but toothcap selected
//											    if (tmp[0] == 'toothcap' && delStr) {
//											        delStr = delStr.replace(","+tmp[0]+"_"+parseInt(tmp[1]), '');
//											    }
//											}
//										}
//									}
//									if (u_count > 0) {
//										delStr = "";
//									}
//								}
//								else if(mouth_part =='Lower_Jaw') {
//									var l_count = 0;
//									delStr = localStorage.getItem('lowerkeys');
//									for (var op = 1; op <= operation_id; op++) {
//										var op_id = document.getElementById('operation_' + op), surface;
//										// $('#operation_' + op).css('display')
//										if (op_id) {
//											surface = document.getElementById('surface_' + op);
//											if ($(surface).text() == "Lower_Jaw") {
//												l_count++;
//											}
//											else {
//											    var tmp = $(surface).text().split("_");
//											    // no upperjaw , but toothcap selected
//											    if (tmp[0] == 'toothcap' && delStr) {
//											        delStr = delStr.replace(","+tmp[0]+"_"+parseInt(tmp[1]), '');
//											    }
//											}
//										}
//									}
//									if (l_count > 0) {
//										delStr = "";
//									}
//								}
								// this.$el.find('#UT,#LT').mapster('set', false, delStr)

//								localStorage.setItem('toDel',delStr);
//                                console.log("PPPPPP ", localStorage)
								/*if (delStr) {
									localStorage.removeItem('upperkeys');
			                    	localStorage.removeItem('lowerkeys');
								}*/
			                    /*Remove treatment line from db*/
			                    list_delete_line_id.push(line_id);
							}
						}

					});
					$('#copy_' + operation_id).click(function() {
						var x = window.confirm("Are you sure you want to copy?");
						if (x) {
						    var actual_id = $(this).attr('id').split('_');
						    try {
						        actual_id = parseInt(actual_id[1]);
						    }
						    catch (err) {
						        actual_id = operation_id;
						    }
						    var old_op = actual_id;

						    operation_id += 1;
						    var table_strr = '';
						    table_strr += '<tr class="' + total_teeth + '" ' +
								'id="operation_' + operation_id + '" line-change="initial">';
                            table_strr += '<td id = "date_time_' + operation_id + '">' + formatDate(today) + '</td>';

                            var initial_checked = '';
                            var cls = '';
			                if (localStorage.getItem('initial_exam') == 'true') {
			                	initial_checked += 'checked="checked"';
			                	cls += 'true';
			                }

			                table_strr += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
                            table_strr += '<td class = "' + selected_treatment_temp.treatment_id + '" ' + 'id = "desc_' + operation_id + '">' + selected_treatment_temp.treatment_name + '</td>';

                            // parent line values
                            var old_diag_val = $('#dignosis_code_'+old_op).val();
                            old_diag_val = old_diag_val ? old_diag_val : '';
                            var old_diag_id = $('#dignosis_code_'+old_op).attr('data-id');
                            old_diag_id = old_diag_id ? old_diag_id : 'false';
                            var old_note = $('#dignosis_note_'+old_op).val();
                            old_note = old_note ? old_note : '';

                            table_strr += '<td id = "dignosis_' + operation_id + '"><input ' +
                                'class="diagnosis_code" id = "dignosis_code_' + operation_id + '" ' +
                                ' value="'+ old_diag_val +'" data-id="'+
                                 old_diag_id +'"/>' +
                                '</td>';
                            table_strr += '<td id = "dignosis_' + operation_id + '"><input ' +
                                'class="diagnosis_note" id = "dignosis_note_' + operation_id + '" ' +
                                ' value="'+ old_note +'"/>' +
                                '</td>';

                            table_strr += '<td class = "' + 'all' + '" id = "tooth_' + operation_id + '">' + '-' + '</td>';

                            table_strr += '<td class="col_stat" id = "status_' + operation_id +
                                '" status_name = "'+status_to_define+'">' +
                                status_to_define_temp + '</td>';
                            table_strr += '<td id = "surface_' + operation_id + '">'+mouth_part+'</td>';

                            table_strr += '<td id = "dentist_' + operation_id + '"' +
								' data-id="' + doctor_id + '">' + doc_name + '</td>';

                            /*setting up input field for amount and will be editable in planned state*/
                            var amount_input;
                            if (status_to_define_temp == 'Planned') {
                                amount_input = '<input type="number"' +
                                    ' value="'+ t_charge +'" />';
                            }
                            else {
                                amount_input = '<input type="number" readonly="True"' +
                                    ' value="'+ t_charge +'" />';
                            }

                            table_strr += '<td class="col_amt" id = "amount_' + operation_id +
                                '">' + amount_input + '</td>';

                            table_strr += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' +
                                selected_treatment_temp.action + '</td>';
                            table_strr += '<td class = "delete_td" id = "delete_' + operation_id + '">' +
                                '<img src = "/pragtech_dental_management/static/src/img/delete.png" height = "20px" width = "20px"/>' + '</td>';
                            table_strr += '<td style="display:none;" class = "copy_td" id = "copy_' + operation_id + '">' +
                                '<img src = "/pragtech_dental_management/static/src/img/copy.png" height = "20px" width = "20px"/>' +
                                '</td>';
                            table_strr += '<td style = "display:none" id = "previous_' +
                                operation_id + '">' + is_prev_record + '</td>';

//							inv_status = "'" + inv_status + "'";
							table_strr += '<td style = "display:none" ><input value="' + inv_status
								+ '" id = "inv_status_' +
					            operation_id + '" /></td>';
                            table_strr += '</tr>';

                            let old_options = self.parse_line($("#operation_" + old_op));
                            table_strr = self._process_table_row(table_strr, old_options);
                            old_options.treatment_id = selected_treatment_temp.treatment_id;
                            $('#progres_table').append(table_strr);
                            $('#dignosis_code_' + operation_id).focus();
                            $('#operation_' + operation_id).addClass('selected_operation');

                            $('#dignosis_code_'+operation_id).autocomplete({
                                select: function (event, ui) {
                                    var terms = split(this.value);
                                    // remove the current input
                                    terms.pop();
                                    // add the selected item
                                    terms.push(ui.item.label);
                                    this.value = terms;
                                    $(this).attr('data-id', ui.item.value);
                                    return false;
                                },
                                source: function (request, response) {
                                    var res = $.ui.autocomplete.filter(
                                        dignosis_records, extractLast(request.term));
                                    response(res);
                                },
                                position: {
                                    collision: "flip"
                                }
                            });

                            $('#operation_' + operation_id).click(function() {
                                var found = $('#progres_table').find('.selected_operation');
                                if (found) {
                                    found.removeClass("selected_operation");
                                }
                                var old_class = $(this).attr('class');
                                var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';
                                $(this).attr('class', new_class);
                            });

                            /*autocomplete diag code end*/
                            $('#delete_' + operation_id).click(function() {
                                var x = window.confirm("Are you sure you want to delete?");
                                if (x) {
                                    update = false;
                                    cont = false;
                                    var delStr = '';
                                    var actual_id = String(this.id).substr(7);
                                    actual_id = parseInt(actual_id);
                                    var line_id = $('#operation_' + actual_id).attr('data-id');
                                    var tabel = document.getElementById('operations');
                                    var tr = document.getElementById('operation_' + actual_id);
                                    var tooth = document.getElementById('tooth_' + actual_id);
                                    var desc_class = $("#desc_" + actual_id).attr('class');
        //                            //console.log('the tr is ',tr )


                                    var status = document.getElementById('status_' + actual_id);
                                    var status_name = $(status).attr('status_name')
                                    if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
                                        alert('Cannot delete');
                                    }
                                    else {
                                        var action = document.getElementById('action_' + actual_id);
                                        var action_id = action.innerHTML;
                                        var tooth_id = $(tooth).text();
                                        var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
                                        self.delete_color_remove(self, type, surface_vals, tooth_id);

//                                        if(mouth_part == 'Full_mouth') {
//                                            var tooth_id = tr.className.split('_');
//        //								    //console.log('the tr ,tooth_idis ',tr ,tooth_id)
//                                            var surf_list = new Array();
//                                            _.each(full_mouth_teeth_temp, function(tooth_id) {
//                                                surf_list.push('view_' + tooth_id + '_center');
//                                                surf_list.push('view_' + tooth_id + '_right');
//                                                surf_list.push('view_' + tooth_id + '_left');
//                                                surf_list.push('view_' + tooth_id + '_top');
//                                                surf_list.push('view_' + tooth_id + '_bottom');
//                                            });
//                                            self_var.decrement_thread(surf_list);
//
//                                            self_var.remove_selection_action(tooth_id);
//                                            if (action_id == 'missing') {
//                                                self_var.remove_missing_action(tooth_id);
//                                            }
//
//        //									self.excluded_tooth['full_mouth'].push(parseInt(line_id));
//                                        }

                                        tr.parentNode.removeChild(tr);

//                                        if(mouth_part =='Upper_Jaw') {
//                                            var u_count = 0;
//                                            delStr = localStorage.getItem('upperkeys');
//                                            for (var op = 1; op <= operation_id; op++) {
//                                                var op_id = document.getElementById('operation_' + op), surface;
//                                                if (op_id) {
//                                                    surface = document.getElementById('surface_' + op);
//                                                    if ($(surface).text() == "Upper_Jaw") {
//                                                        u_count++;
//                                                    }
//                                                    else {
//                                                        var tmp = $(surface).text().split("_");
//                                                        // no upperjaw , but toothcap selected
//                                                        if (tmp[0] == 'toothcap' && delStr) {
//                                                            delStr = delStr.replace(","+tmp[0]+"_"+parseInt(tmp[1]), '');
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                            if (u_count > 0) {
//                                                delStr = "";
//                                            }
//                                        }
//                                        else if(mouth_part =='Lower_Jaw') {
//                                            var l_count = 0;
//                                            delStr = localStorage.getItem('lowerkeys');
//                                            for (var op = 1; op <= operation_id; op++) {
//                                                var op_id = document.getElementById('operation_' + op), surface;
//                                                // $('#operation_' + op).css('display')
//                                                if (op_id) {
//                                                    surface = document.getElementById('surface_' + op);
//                                                    if ($(surface).text() == "Lower_Jaw") {
//                                                        l_count++;
//                                                    }
//                                                    else {
//                                                        var tmp = $(surface).text().split("_");
//                                                        // no upperjaw , but toothcap selected
//                                                        if (tmp[0] == 'toothcap' && delStr) {
//                                                            delStr = delStr.replace(","+tmp[0]+"_"+parseInt(tmp[1]), '');
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                            if (l_count > 0) {
//                                                delStr = "";
//                                            }
//                                        }
                                        // this.$el.find('#UT,#LT').mapster('set', false, delStr)

//                                        localStorage.setItem('toDel',delStr);
                                        /*if (delStr) {
                                            localStorage.removeItem('upperkeys');
                                            localStorage.removeItem('lowerkeys');
                                        }*/

                                        /*Remove treatment line from db*/
                                        list_delete_line_id.push(line_id);
                                    }
                                }

                            });
						}
					});

				});
				if (selected_treatment_temp.action == false) {
				}
			}
		},
//		zzzzzzzzzzz start
		get_new_surface_tooth : function() {
            var sel_table = document.getElementById('selected_list_table');
            var sel_rows = sel_table.getElementsByTagName('tr');
            var sel_i, sel_j, sel_cells, customerId;
            var new_surface_name = ""
            var new_tooth_selected = ""
            var new_tooth_selected_array = new Array();
            for (sel_i = 0, sel_j = sel_rows.length; sel_i < sel_j; ++sel_i) {
                if(sel_rows[sel_i]){
                    sel_cells = sel_rows[sel_i].getElementsByTagName('td');
                    if (!sel_cells.length) {
                        continue;
                    }
                    customerId = sel_cells[0].innerHTML;
                    if(customerId){
                        if (new_surface_name != "") {
                            new_surface_name += ",";
                        }
                        new_surface_name += customerId
                        if (customerId.includes('_')){
                            var mouth_v_v_0 = customerId.split('_')[0]
                            var mouth_v_v_1 = customerId.split('_')[1]
                            if(!isNaN(mouth_v_v_0)){
                                if(!new_tooth_selected_array.includes(mouth_v_v_0)){
                                    new_tooth_selected_array.push(mouth_v_v_0);
                                }
                            }
                            if(!isNaN(mouth_v_v_1)){
                                if(!new_tooth_selected_array.includes(mouth_v_v_1)){
                                    new_tooth_selected_array.push(mouth_v_v_1);
                                }
                            }
                        }
                        if (customerId.includes('Full_mouth')){
                            if(!new_tooth_selected_array.includes('Full_mouth')){
                                new_tooth_selected_array.push('Full_mouth');
                            }
                        }
                        if (customerId.includes('Upper_Jaw')){
                            if(!new_tooth_selected_array.includes('Upper_Jaw')){
                                new_tooth_selected_array.push('Upper_Jaw');
                            }
                        }
                        if (customerId.includes('Lower_Jaw')){
                            if(!new_tooth_selected_array.includes('Lower_Jaw')){
                                new_tooth_selected_array.push('Lower_Jaw');
                            }
                        }

                    }
                }
            }
            for (var nw_tooth_cnt = 0; nw_tooth_cnt < new_tooth_selected_array.length; nw_tooth_cnt++) {
                if (new_tooth_selected != "") {
                    new_tooth_selected += ",";
                }
                new_tooth_selected += new_tooth_selected_array[nw_tooth_cnt];
            }
            return [new_surface_name, new_tooth_selected];
		},
//		zzzzzzzzzzz stop

		put_data_toothpart : function(
			self_var, selected_tooth_temp, selected_surface ,tooth_by_part,
			selected_treatment_temp, status_to_define, created_date,
			is_prev_record, other_history, initial
		) {

			var doctor_id = session.uid;
			var doc_name = user_name;
			if (tooth_by_part) {
			    var surfacepart = selected_surface;
                var tooth_surface = surfacepart;
				var panned_text = $('#planned').text().trim();
				var status_to_use = panned_text;
				var initial_exam="Initial Examination"
				var status_to_define_temp = panned_text;
				var completed_text = $('#completed').text().trim();
				var inprogress_text = $('#in_progress').text().trim();
				var status_defined = status_to_define_temp.toLowerCase();
				if (status_to_define){
					if(status_to_define == 'completed'){
						status_to_define_temp = completed_text;
					}else if(status_to_define == 'in_progress'){
						status_to_define_temp = inprogress_text;
					}else if(status_to_define == 'planned'){
						status_to_define_temp = panned_text;
					}
				}

				var today = new Date();
				if (created_date) {
//				     today = formatDate(today);
					today = created_date;
				}
				var table_str = '';
				var self = this;
				var original_amount = 0;
				this.get_treatment_charge(selected_treatment_temp.treatment_id).then(function(t_charge) {
					 var apply_quantity_on_payment_lines = t_charge[1]
			        var t_charge = t_charge[0]
					if (!t_charge) {
						t_charge = '0.0';
					}
					original_amount = t_charge;
					operation_id += 1;

				var line_id = false;
				var initial_checked = '';
				var color = '';
				var cls = '';
				var colormap=[];
				if (initial == true) {
					initial_checked += 'checked="checked"';
					color += 'examinationcolor';
					cls += 'true';
				}
				if (other_history)
					table_str += '<tr id = operation_' + operation_id + ' style= "display:none" line-change="initial" data-id="'+ line_id +'" ' + 'class="'+selected_tooth_temp+' '+color+'">';
				else
				    table_str += '<tr id = operation_' + operation_id + ' ' + 'data-id="' + line_id + '" line-change="initial" class="' + selected_tooth_temp+' '+color+'">';
				table_str += '<td id = "date_time_' + operation_id + '">' + formatDate(today) + '</td>';
				table_str += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
				table_str += '<td class = "' + selected_treatment_temp.treatment_id + '" ' + 'id = "desc_' + operation_id + '">' + selected_treatment_temp.treatment_name + '</td>';
				table_str += '<td id = "dignosis_' + operation_id + '">'+ '<input class="diagnosis_code" type="text" id="dignosis_code_'+operation_id+'" />'+ '</td>';
				table_str += '<td id = "dignosis_note_td' + operation_id + '">' + '<input type="text" id="dignosis_note_'+operation_id+'"/>'+ '</td>';
                if(selected_tooth_temp==null)
                    {
                    alert("Please select the surface first !    ");
                    return false

                    }
                if(!selected_tooth_temp==null)
                {
                if (selected_tooth_temp.split(',').length > 1) {
                	selected_tooth_temp = '-';
                }
                }
//                console.log("eeeeeeee normal tooth treatment selected")
                var tooth_selected_array = self.get_teeth_type_based_numbering(type, selected_tooth_temp);
                var unitPrice = t_charge;
                if(self.settings_qty_for_teeth && apply_quantity_on_payment_lines){
                    var qty_tooth = selected_tooth_temp.split(',')
                    t_charge = t_charge * qty_tooth.length;
                    original_amount = t_charge;
                }
                if (type == 'palmer') {
                    table_str += '<td  class="' + tooth_selected_array + '"id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';

                }
                else if (type == 'universal') {
                    table_str += '<td class = "' + selected_tooth_temp + '" id = "tooth_' + operation_id + '">' + selected_tooth_temp + '</td>';
                } else if (type == 'iso') {
                    if(document.getElementById('child').checked){
					    var iso_tooth_selected_array = new Array();
//                        rpc.query({
//                            model: 'teeth.code',
//                            method: 'get_child_correct_teeth_code',
//                            args: [this.patient_id],
//                        }).then(function(res){
//                                for (var i_tooth = 0; i_tooth < tooth_selected_array.length; i_tooth++) {
//                                    var wrong_teeth_no = tooth_selected_array[i_tooth];
//                                    iso_tooth_selected_array.push(res[wrong_teeth_no]);
//                                }
//                                console.log(iso_tooth_selected_array)
//                                table_str += '<td class="' + iso_tooth_selected_array + '" id = "tooth_' + operation_id + '">' + iso_tooth_selected_array + '</td>';
//                        });
                        for (var i_tooth = 0; i_tooth < tooth_selected_array.length; i_tooth++) {
                            var wrong_teeth_no = tooth_selected_array[i_tooth];
                            var dict_teeth_no = {
                                '18': '55',
                                '17': '54',
                                '16': '53',
                                '15': '52',
                                '14': '51',
                                '13': '61',
                                '12': '62',
                                '11': '63',
                                '21': '64',
                                '22': '65',
                                '23': '75',
                                '24': '74',
                                '25': '73',
                                '26': '72',
                                '27': '71',
                                '28': '81',
                                '38': '82',
                                '37': '83',
                                '36': '84',
                                '35': '85',
                            }
                            iso_tooth_selected_array.push(dict_teeth_no[wrong_teeth_no]);
                        }
                        tooth_selected_array = iso_tooth_selected_array;
					}
					table_str += '<td class="' + tooth_selected_array + '" id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
                    }
                /*Add filter of initial Examination */
                var status_of_initial="initial_examination"
                if (initial == true) {
                	table_str += '<td class="col_stat" id = "status_' + operation_id +
                	    '" status_name = "'+status_of_initial+'">' + initial_exam + '</td>';
                }
                else{
                	table_str += '<td class="col_stat" id = "status_' + operation_id +
                	    '" status_name = "'+status_defined+'">'+ status_to_use +'</td>';

                }
                table_str += '<td id = "surface_' + operation_id + '">' + tooth_surface + '</td>';
                table_str += '<td id = "dentist_' + operation_id + '" ' +
					' data-id="' + doctor_id + '">' + doc_name + '</td>';


				 /*Add filter of initial Examination */
				var amount_input=0.0;
				if (initial == true) {
					table_str += '<td id = "amount_' + operation_id + '">'+ amount_input +'</td>';
				}
				else{
				/*input textbox for amount*/
				if (status_to_use == 'Planned') {
					amount_input = '<input type="number" ' +
						' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
				}
				else {
					amount_input = '<input type="number" readonly="True"' +
						' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
				}
				table_str += '<td class="col_amt" id = "amount_' + operation_id + '">' + amount_input + '</td>';
				}
				table_str += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' + selected_treatment_temp.action + '</td>';
				table_str += '<td class = "delete_td" id = "delete_' + operation_id + '">' + '<img src = "/pragtech_dental_management/static/src/img/delete.png" height = "20px" width = "20px"/>' + '</td>';
				table_str += '<td class = "copy_td" id = "copy_' + operation_id + '">' +
					    '<img src = "/pragtech_dental_management/static/src/img/copy.png" height = "20px" width = "20px"/>' +
					    '</td>';
				table_str += '<td style = "display:none" id = "previous_' + operation_id + '">' + is_prev_record + '</td>';
				table_str += '</tr>';
				var surfaces_as=[]
				surfaces_as.push(tooth_surface)
//				console.log(33);
                let t_id = selected_treatment.treatment_id ? selected_treatment.treatment_id : selected_treatment_temp.treatment_id;
                table_str = self._process_table_row(table_str, {
                    'unit_price': unitPrice,
                    'treatment_id': t_id
                });
                $('#progres_table').append(table_str);
//                zzzzzzzzzzz start
                $('#selected_list_tbody').empty();
//                zzzzzzzzzzz end
                lst_tooth = []
                final_plus = []
                $('#dignosis_code_' + operation_id).focus();
                self.$el.find('.selected_operation').each(function() {
                	$(this).removeClass('selected_operation');
                });
                $('#operation_' + operation_id).addClass('selected_operation');

				/*event for line selection*/
				$('#operation_' + operation_id).click(function() {
					var found = $('#progres_table').find('.selected_operation');
					if (found) {
						found.removeClass("selected_operation");
					}
					var old_class = $(this).attr('class');
                    var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';
                    $(this).attr('class', new_class);
				});

				/*CHANGED HERE */
				$('#dignosis_code_'+operation_id).autocomplete({
					select: function (event, ui) {
						var terms = split(this.value);
						// remove the current input
						terms.pop();
						// add the selected item
						terms.push(ui.item.label);
						this.value = terms;
						$(this).attr('data-id', ui.item.value);
						return false;
					},
					source: function (request, response) {
						// delegate back to autocomplete, but extract the last term
//                        if (reg_patient === true) {
						var res = $.ui.autocomplete.filter(
							dignosis_records, extractLast(request.term));
						response(res);
					},
					position: { collision: "flip" }
				});

				$('#delete_' + operation_id).click(function() {
					var x = window.confirm("Are you sure you want to delete?");

					if (x) {
						update = false;
						cont = false;
						var actual_id = String(this.id).substr(7);
//							//console.log(String(this.id).substr(7))
						actual_id = parseInt(actual_id);
						var line_id = $('#operation_' + actual_id).attr('data-id');
						var tabel = document.getElementById('operations');
						var tr = document.getElementById('operation_' + actual_id);
						var tooth = document.getElementById('tooth_' + actual_id);

						var desc_class = $("#desc_" + actual_id).attr('class');
						var tooth_id = tr.className.split('_');
						var status = document.getElementById('status_' + actual_id);
						var status_name = $(status).attr('status_name')
						if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
							alert('Cannot delete');
						}
						else {
						    var tooth_id = $(tooth).text();
                            var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
                            self.delete_color_remove(self, type, surface_vals, tooth_id);
							tr.parentNode.removeChild(tr);
//							var t_count = 0, upper_jaw_flag = false, lower_jaw_flag = false;
//							for (var op = 1; op <= operation_id; op++) {
//                                var op_id = document.getElementById('operation_' + op), surface;
//                                // $('#operation_' + op).css('display')
//                                if (op_id) {
//                                    surface = document.getElementById('surface_' + op);
//                                    if ($(surface).text() == selected_surface) {
//                                        t_count++;
//                                    }
//                                    var tmp3 = $(surface).text().split(' ')[0];
//                                    if (selected_surface.split("_")[0] == 'toothcap') {
//                                        if (tmp3 == 'Upper_Jaw') {
//                                            upper_jaw_flag = true;
//                                        }
//                                        else if (tmp3 == 'Lower_Jaw') {
//                                            lower_jaw_flag = true;
//                                        }
//                                    }
//                                }
//                            }

//							if (t_count > 0) {
//								selected_surface = null;
//							}
//							else if (selected_surface.split("_")[0] == 'toothcap') {
//							    var temp1 = parseInt(selected_surface.split('_')[1]);
//                                if (temp1 < 17 && upper_jaw_flag == true) {
//                                    selected_surface = null;
//                                }
//                                else if (temp1 > 16 && temp1 <=32 && lower_jaw_flag == true) {
//                                    selected_surface = null;
//                                }
//                                else {
//                                    var val, new_val;
//                                    try {
//                                        new_val = selected_surface.split("_");
//                                        val = new_val[1];
//                                        if (new_val[0] == 'toothcap' &&
//                                            val && parseInt(val) < 10) {
//                                            selected_surface = new_val[0] + "_" + parseInt(val);
//                                        }
//                                    }
//                                    catch (err) {}
//                                }
//							}
//							else {
//                                var val, new_val;
//                                try {
//                                    new_val = selected_surface.split("_");
//                                    val = new_val[1];
//                                    if (new_val[0] == 'toothcap' &&
//                                        val && parseInt(val) < 10) {
//                                        selected_surface = new_val[0] + "_" + parseInt(val);
//                                    }
//                                }
//                                catch (err) {}
//                            }
//							localStorage.setItem('toDel',selected_surface);
                            /*Remove treatment line from db*/
                            list_delete_line_id.push(line_id);
//                            rpc.query({
//                                model: 'medical.patient',
//                                method: 'unlink_treatment',
//                                args: [line_id]
//                            }).then(function (res) {
//                               toothmap_id=null;
//                            });
						}

					}
				});

				$('#copy_' + operation_id).click(function() {
					var x = window.confirm("Are you sure you want to copy?");
					if (x) {
					    var actual_id = $(this).attr('id').split('_');
                        try {
                            actual_id = parseInt(actual_id[1]);
                        }
                        catch (err) {
                            actual_id = operation_id;
                        }
                        var old_op = actual_id;
					    operation_id += 1;
					    var table_strr = '';
					    table_strr += '<tr id = operation_' + operation_id +
							' line-change="initial">';
                        var initial_checked = '';
                        var cls = '';
                        if (localStorage.getItem('initial_exam') == 'true') {
                        	initial_checked += 'checked="checked"'
                        	cls += 'true';
                        }
//                        console.log(4)
                        table_strr += '<td id = "date_time_' + operation_id + '">' + today + '</td>';
                        table_strr += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
                        table_strr += '<td class = "' + selected_treatment_temp.treatment_id + '" ' + 'id = "desc_' +
                                      operation_id + '">' + selected_treatment_temp.treatment_name + '</td>';

                        // parent line values
                        var old_diag_val = $('#dignosis_code_'+old_op).val();
                        old_diag_val = old_diag_val ? old_diag_val : '';
                        var old_diag_id = $('#dignosis_code_'+old_op).attr('data-id');
                        old_diag_id = old_diag_id ? old_diag_id : 'false';
                        var old_note = $('#dignosis_note_'+old_op).val();
                        old_note = old_note ? old_note : '';

                        table_strr += '<td id = "dignosis_' + operation_id + '"><input ' +
                                'class="diagnosis_code" id = "dignosis_code_' + operation_id + '" ' +
                                ' value="'+ old_diag_val +'" data-id="'+
                                 old_diag_id +'"/>' +
                                '</td>';
                        table_strr += '<td id = "dignosis_' + operation_id + '"><input ' +
                                'class="diagnosis_note" id = "dignosis_note_' + operation_id + '" ' +
                                ' value="'+ old_note +'"/>' +
                                '</td>';
//                        console.log("eeeeeeee copy no idea")
                        var tooth_selected_array = self.get_teeth_type_based_numbering(type, selected_tooth_temp);
                        if (type == 'palmer') {
                            table_strr += '<td class="' + tooth_selected_array + '" id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
                        }
                        else if (type == 'universal') {
                            table_strr += '<td class = "' + selected_tooth_temp + '" id = "tooth_' + operation_id + '">' + selected_tooth_temp + '</td>';
                        } else if (type == 'iso') {
                                table_strr += '<td class="' + tooth_selected_array + '" id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
                            }
                        table_strr += '<td class="col_stat" id = "status_' + operation_id +
                            '" status_name = "'+status_defined+'">' + status_to_use + '</td>';
                        table_strr += '<td id = "surface_' + operation_id + '">' + tooth_surface + '</td>';
                        table_strr += '<td id = "dentist_' + operation_id + '" ' +
							'data-id="' + doctor_id + '">' + doc_name + '</td>';

                        /*input textbox for amount*/
                        var amount_input;
                        if (status_to_use == 'Planned') {
                            amount_input = '<input type="number" ' +
                                ' value="'+ t_charge +'" />';
                        }
                        else {
                            amount_input = '<input type="number"  readonly="True"' +
                                ' value="'+ t_charge +'" />';
                        }

                        table_strr += '<td class="col_amt" id = "amount_' + operation_id + '">' + amount_input + '</td>';

                        table_strr += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' + selected_treatment_temp.action + '</td>';
                        table_strr += '<td class = "delete_td" id = "delete_' + operation_id + '">' + '<img src = "/pragtech_dental_management/static/src/img/delete.png" height = "20px" width = "20px"/>' + '</td>';
                        table_strr += '<td style="display:none;" class = "copy_td" id = "copy_' + operation_id + '">' +
                                '<img src = "/pragtech_dental_management/static/src/img/copy.png" height = "20px" width = "20px"/>' +
                                '</td>';
                        table_strr += '<td style = "display:none" id = "previous_' + operation_id + '">' + is_prev_record + '</td>';

						table_strr += '<td style = "display:none" ><input value="draft" id="inv_status_' +
							operation_id + '" /></td>';
                        table_strr += '</tr>';

//                        console.log(44);
                        let old_options = self.parse_line($("#operation_" + old_op));
                        old_options.treatment_id = selected_treatment_temp.treatment_id;
                        table_strr = self._process_table_row(table_strr, old_options);
                        $('#progres_table').append(table_strr);
                        $('#dignosis_code_' + operation_id).focus();
                        $('#operation_' + operation_id).addClass('selected_operation');

                        $('#dignosis_code_'+operation_id).autocomplete({
                            select: function (event, ui) {
                                var terms = split(this.value);
                                // remove the current input
                                terms.pop();
                                // add the selected item
                                terms.push(ui.item.label);
                                this.value = terms;
                                $(this).attr('data-id', ui.item.value);
                                return false;
                            },
                            source: function (request, response) {
                                // delegate back to autocomplete, but extract the last term
        //                        if (reg_patient === true) {
                                var res = $.ui.autocomplete.filter(
                                    dignosis_records, extractLast(request.term));
                                response(res);
                            },
                            position: {
                                collision: "flip"
                            }
                        });

                        $('#operation_' + operation_id).click(function() {
                            var found = $('#progres_table').find('.selected_operation');
                            if (found) {
                                found.removeClass("selected_operation");
                            }
                            var old_class = $(this).attr('class');
                            var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';
                            $(this).attr('class', new_class);
                        });

				        $('#delete_' + operation_id).click(function() {
                            var x = window.confirm("Are you sure you want to delete?");

                            if (x) {
                                update = false;
                                cont = false;
                                var actual_id = String(this.id).substr(7);
        //							//console.log(String(this.id).substr(7))
                                actual_id = parseInt(actual_id);
                                var line_id = $('#operation_' + actual_id).attr('data-id');
                                var tabel = document.getElementById('operations');
                                var tr = document.getElementById('operation_' + actual_id);
                                var tooth = document.getElementById('tooth_' + actual_id);

                                var desc_class = $("#desc_" + actual_id).attr('class');

                                var tooth_id = tr.className.split('_');
        //                            //console.log("document.getElementById('tooth_' + actual_id);  and tooth_id in del" + tooth +','+tooth_id)
                                var status = document.getElementById('status_' + actual_id);
                                var status_name = $(status).attr('status_name')
                                if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
                                    alert('Cannot delete');
                                }
                                else {
                                    var tooth_id = $(tooth).text();
                                    var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
                                    self.delete_color_remove(self, type, surface_vals, tooth_id);
                                    tr.parentNode.removeChild(tr);

//                                    var t_count = 0, upper_jaw_flag = false, lower_jaw_flag = false;
//                                    for (var op = 1; op <= operation_id; op++) {
//                                        var op_id = document.getElementById('operation_' + op), surface;
//                                        // $('#operation_' + op).css('display')
//                                        if (op_id) {
//                                            surface = document.getElementById('surface_' + op);
//                                            if ($(surface).text() == selected_surface) {
//                                                t_count++;
//                                            }
//                                            var tmp3 = $(surface).text().split(' ')[0];
//                                            if (selected_surface.split("_")[0] == 'toothcap') {
//                                                if (tmp3 == 'Upper_Jaw') {
//                                                    upper_jaw_flag = true;
//                                                }
//                                                else if (tmp3 == 'Lower_Jaw') {
//                                                    lower_jaw_flag = true;
//                                                }
//                                            }
//                                        }
//                                    }
//
//                                    if (t_count > 0) {
//                                        selected_surface = null;
//                                    }
//                                    else if (selected_surface.split("_")[0] == 'toothcap') {
//                                        var temp1 = parseInt(selected_surface.split('_')[1]);
//                                        if (temp1 < 17 && upper_jaw_flag == true) {
//                                            selected_surface = null;
//                                        }
//                                        else if (temp1 > 16 && temp1 <=32 && lower_jaw_flag == true) {
//                                            selected_surface = null;
//                                        }
//                                        else {
//                                            var val, new_val;
//                                            try {
//                                                new_val = selected_surface.split("_");
//                                                val = new_val[1];
//                                                if (new_val[0] == 'toothcap' &&
//                                                    val && parseInt(val) < 10) {
//                                                    selected_surface = new_val[0] + "_" + parseInt(val);
//                                                }
//                                            }
//                                            catch (err) {}
//                                        }
//                                    }
//                                    else {
//                                        var val, new_val;
//                                        try {
//                                            new_val = selected_surface.split("_");
//                                            val = new_val[1];
//                                            if (new_val[0] == 'toothcap' &&
//                                                val && parseInt(val) < 10) {
//                                                selected_surface = new_val[0] + "_" + parseInt(val);
//                                            }
//                                        }
//                                        catch (err) {}
//                                    }
//                                    localStorage.setItem('toDel',selected_surface);

                                    /*Remove treatment line from db*/
                                    list_delete_line_id.push(line_id);
                                }

                            }
                        });

					}
				});

				});
				if (selected_treatment_temp.action == false) {
				}

			}
		 tooth_by_part = 0;
		 selected_surface == '';
		},
		/*CHANGED HERE*/
		put_data : function(self_var, surfaces, selected_tooth_temp, selected_surface_temp,
							status_defined, created_date, is_prev_record, other_history,
							dignosis,dignosis_description, amount, inv_status,
							line_id, doctor_id, doc_name, initial, highlight_color,
							unit_price, discount_fixed_percent, discount, discount_value) {
            var options = {
                'unit_price': unit_price,
                'discount_fixed_percent': discount_fixed_percent,
                'discount': discount,
                'discount_value': discount_value,
                'treatment_id': selected_treatment.treatment_id
            };
            if (inv_status == 'false') {
                inv_status = 'draft';
            }
			if (!selected_tooth_temp) {
				selected_tooth_temp = '-';
			}
			var selected_treatment_temp = selected_treatment;
			var table_str = '';
			var today = new Date();
			if (created_date) {
				today = created_date;
//				 today = formatDate(today);

			}
			var panned_text = $('#planned').text().trim();
			var status_to_use = panned_text;
			var completed_text = $('#completed').text().trim()
			var inprogress_text = $('#in_progress').text().trim()
			if (status_defined)
				if(status_defined == 'completed'){
					status_to_use = completed_text;
				}else if(status_defined == 'in_progress'){
					status_to_use = inprogress_text;
				}else if(status_defined == 'planned'){
					status_to_use = panned_text;
				}
				/*}else(status_defined == 'initial_examination'){
					status_to_use = "Initial Examination";
				}*/
			if (status_to_use == 'planned'){
				status_to_use = panned_text;
			}
            var self = this;
            var original_amount = 0;
//            console.log(3);
			this.get_treatment_charge(selected_treatment_temp.treatment_id).then(function(t_charge) {
			    var apply_quantity_on_payment_lines = t_charge[1]
			    var t_charge = t_charge[0]
			    if (!t_charge) {
					t_charge = '0.0';
				}
				original_amount = t_charge;
				if (amount > 0) {
					t_charge = amount;
				}
				/*Dec*/
				operation_id += 1;
				var found = self_var.$el.find('.selected_operation');
				if (found) {
					found.removeClass("selected_operation");
				}
				var initial_checked = '';
				var cls = '';
				var color = '';
                if (initial == true) {
                	initial_checked += 'checked="checked"';
                	color += 'examinationcolor';
                	cls += 'true';
                }
                if (other_history)
					table_str += '<tr id = operation_' + operation_id + ' ' +
						'style= "display:none" line-change="initial" data-id="' +
						line_id + '" class="'+selected_tooth_temp+' '+color+'">';
				else
					table_str += '<tr id = operation_' + operation_id + ' ' +
						'line-change="initial" data-id="'+
						line_id +'" class="'+selected_tooth_temp+' '+color+'">';

//                console.log(1);
                table_str += '<td id = "date_time_' + operation_id + '">' + formatDate(today) + '</td>';
                table_str += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
				table_str += '<td class = "' + selected_treatment_temp.treatment_id + '" ' +
				    'id = "desc_' + operation_id + '">' + selected_treatment_temp.treatment_name + '</td>';

				/*Change starts here*/
                /*autocomplete diag code start*/
				try {
					var d_code_data, desc_data = "", diag_disp = "", data_id = "";
					if (dignosis && dignosis.id) {
						d_code_data = dignosis_records_by_id[dignosis.id];
						data_id = dignosis.id;
						diag_disp += d_code_data.code + "/" + d_code_data.description;
					}
					else {
						diag_disp = "";
					}
				}
				catch (err) {
					diag_disp = "";
				}
				try {
					if (dignosis_description && dignosis_description != 'false') {
						desc_data = dignosis_description;
					}
				}
				catch (err) {
					desc_data = "";
				}
				data_id = (data_id == false) ? '' : data_id;

                table_str += '<td id="dignosis_' + operation_id +
								'"><input class="diagnosis_code" id="dignosis_code_' +
								operation_id + '" value="' + diag_disp +'" data-id="'+ data_id +'"/></td>';
                table_str += '<td id = "dignosis_note_td' + operation_id +
								'"><input class="dignosis_note" autocomplete="off" id="dignosis_note_' +
								operation_id + '" value="'+ desc_data +'"/></td>';

                /*autocomplete diag code end*/
                /*var multi_tooth = "", multi_surface = "";
                var history_data = true;
                if (self.find_length(self.cached_teeth_list) > 0) {
                    var res = self.get_tooth_surface();
                    multi_tooth = res[0].slice(0, -1);
                    multi_surface = res[1].slice(0, -1);
                    history_data = false;
                }
                else {
                    var res = self.get_tooth_surface_data(surfaces);
                    multi_tooth = res[0].slice(0, -1);
                    multi_surface = res[1].slice(0, -1);
                }*/
//                console.log("eeeeeeee while_opening_chart loading existing btable")
                var tooth_selected_array = self_var.get_teeth_type_based_numbering(type, selected_tooth_temp);
                if(self.settings_qty_for_teeth && apply_quantity_on_payment_lines){
                    var qty_tooth = selected_tooth_temp.split(',')
                    original_amount = original_amount * qty_tooth.length;
                }
				if (type == 'palmer') {
					table_str += '<td  class="' + tooth_selected_array + '"id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
				} else if (type == 'universal') {
					table_str += '<td class = "' + selected_tooth_temp + '" id = "tooth_' + operation_id + '">' + selected_tooth_temp + '</td>';
				} else if (type == 'iso') {
                    table_str += '<td  class="' + tooth_selected_array + '" id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
				}
				var status_of_initial="initial_examination";
				var state_initial_exam="Initial Examination"
		        if (initial == true) {
		            	 table_str += '<td class="col_stat" id = "status_' + operation_id +
		            	    '" status_name = "'+status_of_initial+'">' + state_initial_exam + '</td>';
		             }
		             else{
		            	 table_str += '<td class="col_stat" id = "status_' + operation_id +
		            	    '" status_name = "'+status_defined+'">' + status_to_use + '</td>';
		             }
               if(!tooth_by_part){
				table_str += '<td id = "surface_' + operation_id + '">';
				_.each(surfaces, function(each_surf) {
					table_str += each_surf + ' ';
				});
				self_var.increment_thread(selected_surface_temp);
				table_str += '</td>';
                }else{
                table_str += '<td id = "surface_' + operation_id + '">' +surfaces+'</td>';

		        tooth_by_part == 0;
                }
				table_str += '<td id = "dentist_' + operation_id + '" ' +
					'data-id="' + doctor_id + '">' + doc_name + '</td>';

				/*input box for amount field*/
				var initial_amt=0
				if (initial == true) {
					table_str += '<td id = "amount_' + operation_id + '">' + initial_amt + '</td>';
				}
				else{
				var amount_input;
				if (status_to_use == 'Planned') {
					amount_input = '<input type="number"  ' +
						' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
				}
				else {
					amount_input = '<input type="number" readonly="True"' +
						' value="'+ t_charge +'" original_amount="' +
							 original_amount + '" class="amount_td" />';
				}

				table_str += '<td class="col_amt" id = "amount_' + operation_id + '">' + amount_input + '</td>';
				}
				table_str += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' +
					selected_treatment_temp.action + '</td>';
				table_str += '<td class = "delete_td" id = "delete_' + operation_id + '">' +
					'<img src = "/pragtech_dental_management/static/src/img/delete.png" height="20px" width="20px"/>'
					+ '</td>';
				table_str += '<td class = "copy_td" id = "copy_' + operation_id + '">' +
					    '<img src="/pragtech_dental_management/static/src/img/copy.png" height="20px" width="20px"/>' +
					    '</td>';
				table_str += '<td style="display:none" id="previous_' + operation_id + '">' + is_prev_record + '</td>';
//				inv_status = "'"+inv_status+"'";
				table_str += '<td style="display:none" ><input value="' +
				    inv_status + '" id="inv_status_' + operation_id + '" /></td>';
				table_str += '</tr>';
//				console.log(55);
				table_str = self._process_table_row(table_str, options);
				$('#progres_table').append(table_str);
				/*$('#dignosis_code_' + operation_id).focus();
				$('#operation_' + operation_id).addClass('selected_operation');*/

				$('#operation_' + operation_id).click(function() {
					var found = self_var.$el.find('.selected_operation');
					if (found) {
						found.removeClass("selected_operation");
					}
					var old_class = $(this).attr('class');
                    var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';

                    $(this).attr('class', new_class);
				});
				if (highlight_color) {
					colormap.push({
						surfaces:   surfaces.join(),
						color: highlight_color.slice(1)
					});
				}
//				console.log(66);
				var image1 = $('#UT');
			    var image2 = $('#LT');
			    var image3 = $('#childUT');
			    var image4 =$('#childLT');
			    var each_slf_id = surfaces.join();
                var all_nameArr = each_slf_id.split(',');
                for(var e = 0; e < all_nameArr.length; e++) {
                    var tooth_map_nameArr = all_nameArr[e].split('_')
                    for(var i = 0; i < tooth_map_nameArr.length; i++) {
                        tooth_map_nameArr[i] = tooth_map_nameArr[i].replace(/^\s*/, "").replace(/\s*$/, "");
                        if(!isNaN(tooth_map_nameArr[i])){
                            if (type == 'palmer') {
                              each_slf_id = each_slf_id.replace(tooth_map_nameArr[i], _.invert(Palmer)[tooth_map_nameArr[i]]);
                            }
                            else if (type == 'iso') {
                                each_slf_id = each_slf_id.replace(tooth_map_nameArr[i], _.invert(Iso)[tooth_map_nameArr[i]]);
                            }
                            else{
                                each_slf_id = each_slf_id.replace(tooth_map_nameArr[i], tooth_map_nameArr[i]);
                            }
                        }
                    }
                }
                if (highlight_color) {
                    image1.mapster('set', true, each_slf_id, {fillColor: highlight_color.slice(1)});
					image2.mapster('set', true, each_slf_id, {fillColor: highlight_color.slice(1)});
					image3.mapster('set', true, each_slf_id, {fillColor: highlight_color.slice(1)});
					image4.mapster('set', true, each_slf_id, {fillColor: highlight_color.slice(1)});
			    }
			    else {
			        image1.mapster('set', true, each_slf_id);
					image2.mapster('set', true, each_slf_id);
					image3.mapster('set', true, each_slf_id);
					image4.mapster('set', true, each_slf_id);
			    }
			    var new_surfaces = new Array();
			    new_surfaces.push(each_slf_id)
			    for (var s = 0; s < new_surfaces.length; s++) {
					var surf = new_surfaces[s].split(',')
					for (var k = 0; k < surf.length; k++) {
						if(jQuery.inArray(surf[k], final_surfaces) == -1) {
						    $('.' + surf[k]).each(function() {
								var selected_chart;
								var slf = this;
								$('.charttype input').each(function() {
									if (this.checked) {
										selected_chart = this.value;
										var slf_id = slf.id;
                                        rpc.query({
                                            model: 'medical.teeth.treatment',
                                            method: 'get_is_child',
                                            args: [line_id]
                                        }).then(function (is_child) {
                                            if(highlight_color){
											   var surface_color = highlight_color;
											}
											else{
											    var surface_color = 'orange';
											}
											if(surface_color == 'ff000c'){
											    surface_color = 'orange'
											}
											if(is_child && slf_id.includes('child')){
                                                $('#' + slf_id).attr('fill', surface_color);
                                            }
                                            if(! is_child && !slf_id.includes('child')){
                                               $('#' + slf_id).attr('fill', surface_color);
                                            }
                                        });

									}
								});
						    });
							final_surfaces.push(surf[k]);
						}
					}
				}
				/*CHANGED HERE */
//				console.log(77);
				$('#dignosis_code_'+operation_id).autocomplete({
					select: function (event, ui) {
						var terms = split(this.value);
						// remove the current input
						terms.pop();
						// add the selected item
						terms.push(ui.item.label);
						this.value = terms;
						$(this).attr('data-id', ui.item.value);
						return false;
					},
					source: function (request, response) {
						// delegate back to autocomplete, but extract the last term
//                        if (reg_patient === true) {
						var res = $.ui.autocomplete.filter(
							dignosis_records, extractLast(request.term));
						response(res);
					},
					position: {
					    collision: "flip"
                    }
				});

//				console.log(88);
				/*autocomplete diag code end*/
				$('#delete_' + operation_id).click(function() {
					var x = window.confirm("Are you sure you want to delete?");
					if (x) {
						update = false;
						cont = false;
						var actual_id = String(this.id).substr(7);
						actual_id = parseInt(actual_id);
						var line_id = $('#operation_' + actual_id).attr('data-id');
						var tabel = document.getElementById('operations');
						var tr = document.getElementById('operation_' + actual_id);
						var tooth = document.getElementById('tooth_' + actual_id);
						var desc_class = $("#desc_" + actual_id).attr('class');
//						var tooth_id = $(tooth).attr('class');
						var status = document.getElementById('status_' + actual_id);
						var status_name = $(status).attr('status_name')
						if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
							alert('Cannot delete');
						}
						else {
							var action = document.getElementById('action_' + actual_id);
							var action_id = action.innerHTML;
							var tooth_id = $(tooth).text();
                            var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
                            self.delete_color_remove(self, type, surface_vals, tooth_id);
//							{
//								var surface_vals = ($('#surface_' + actual_id).text()).split(' ');
//								var surf_list = new Array();
//								_.each(surface_vals, function(sv) {
//									if ($('#view_' + tooth_id + '_center').attr('class').split(' ')[1] == sv) {
//										surf_list.push('view_' + tooth_id + '_center');
//									}
//									if ($('#view_' + tooth_id + '_right').attr('class').split(' ')[1] == sv) {
//										surf_list.push('view_' + tooth_id + '_right');
//									}
//									if ($('#view_' + tooth_id + '_left').attr('class').split(' ')[1] == sv) {
//										surf_list.push('view_' + tooth_id + '_left');
//									}
//									if ($('#view_' + tooth_id + '_top').attr('class').split(' ')[1] == sv) {
//										surf_list.push('view_' + tooth_id + '_top');
//									}
//									if ($('#view_' + tooth_id + '_bottom').attr('class').split(' ')[1] == sv) {
//										surf_list.push('view_' + tooth_id + '_bottom');
//									}
//								});
//								self_var.decrement_thread(surf_list);
//							}
//							var new_surfaces = surfaces, upper_jaw_flag = false, lower_jaw_flag = false;
//							if (action_id == 'missing') {
//								$($("#" + $('#' + tooth_id).attr('id')).css('visibility', "visible").attr('class', 'teeth'));
//								$("#view_" + $('#' + tooth_id).attr('id') + "_top,#view_" + $('#' + tooth_id).attr('id') + "_left,#view_" + $('#' + tooth_id).attr('id') + "_bottom,#view_" + $('#' + tooth_id).attr('id') + "_right,#view_" + $('#' + tooth_id).attr('id') + "_center").attr('visibility', 'visible');
//								$("#view_" + $('#' + tooth_id).attr('id') + "_top,#view_" + $('#' + tooth_id).attr('id') + "_left,#view_" + $('#' + tooth_id).attr('id') + "_bottom,#view_" + $('#' + tooth_id).attr('id') + "_right,#view_" + $('#' + tooth_id).attr('id') + "_center").attr('fill', 'white');
//							} else {
//                                self.excluded_tooth['tooth_ids'] = {};
//                                _.each(surface_vals, function(surf_val) {
//                                    if (!surf_val) {}
//                                    else {
//                                        for (var op = 1; op <= operation_id; op++) {
//                                            var op_id = document.getElementById('operation_' + op), surface;
//                                            if (op_id) {
//                                                surface = document.getElementById('surface_' + op);
//                                                var keys = $.map(self.excluded_tooth['tooth_ids'], function(v, i){
//                                                  return i;
//                                                });
//                                                var tmp2 = $(surface).text().split(' ')[0];
//                                                if (tmp2 == surf_val) {
//                                                    if (keys.includes(surf_val)) {
//                                                        self.excluded_tooth['tooth_ids'][surf_val]++;
//                                                     }
//                                                     else {
//                                                        self.excluded_tooth['tooth_ids'][surf_val] = 0;
//                                                     }
//                                                }
//                                                if (surf_val.split('_')[0] == 'toothcap') {
//                                                    if (tmp2 == 'Upper_Jaw') {
//                                                        upper_jaw_flag = true;
//                                                    }
//                                                    else if (tmp2 == 'Lower_Jaw') {
//                                                        lower_jaw_flag = true;
//                                                    }
//                                                }
//                                            }
//                                        }
//                                    }
//                                });
//
//
//                                if (parseInt(($('#view_' + tooth_id + '_bottom').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_bottom').attr('id')).attr('fill', 'white');
//                                if (parseInt(($('#view_' + tooth_id + '_right').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_right').attr('id')).attr('fill', 'white');
//                                if (parseInt(($('#view_' + tooth_id + '_center').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_center').attr('id')).attr('fill', 'white');
//                                if (parseInt(($('#view_' + tooth_id + '_left').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_left').attr('id')).attr('fill', 'white');
//                                if (parseInt(($('#view_' + tooth_id + '_top').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_top').attr('id')).attr('fill', 'white');
//
//                                new_surfaces = [];
//                                _.each(surfaces, function (surf_val) {
//                                    if (self.excluded_tooth['tooth_ids'][surf_val] > 0) {}
//                                    else if (surf_val.split('_')[0] == 'toothcap') {
//                                        var temp1 = parseInt(surf_val.split('_')[1]);
//                                        if (temp1 < 17 && upper_jaw_flag == true) {}
//                                        else if (temp1 > 16 && temp1 <=32 && lower_jaw_flag == true) {}
//                                        else {
//                                            new_surfaces.push(surf_val);
//                                        }
//                                    }
//                                    else {
//                                        new_surfaces.push(surf_val);
//                                    }
//                                });
//							}
//							console.log("De;eted:::::::::4644:::::",new_surfaces)
//                            localStorage.setItem('toDel', new_surfaces);

							tr.parentNode.removeChild(tr);
							for (var index = 0; index < treatment_lines.length; index++) {
								if (treatment_lines[index].tooth_id == tooth_id) {
									for (var i2 = 0; i2 < treatment_lines[index].treatments.length; i2++) {
										if (treatment_lines[index].treatments[i2].treatment_id == parseInt(desc_class)) {
											treatment_lines.splice(index, 1);
											operation_id += 1;
											var found = self_var.$el.find('.selected_treatment_temp');
											if (found) {
												found.removeClass("selected_treatment_temp");
											}
											return;
										}
									}
								}
							}
                            /*Remove treatment line from db*/
                            list_delete_line_id.push(line_id);
						}

					}
				});
//				console.log(99);
				$('#copy_' + operation_id).click(function() {
					var x = window.confirm("Are you sure you want to copy?");
					if (x) {
					    var actual_id = $(this).attr('id').split('_');
                        try {
                            actual_id = parseInt(actual_id[1]);
                        }
                        catch (err) {
                            actual_id = operation_id;
                        }
                        var old_op = actual_id;

						operation_id += 1;
						var table_strr = '';
						table_strr += '<tr id = operation_' + operation_id + ' line-change="initial">';
						table_strr += '<td id = "date_time_' + operation_id + '">' + today + '</td>';

						var initial_checked = '';
						var cls = '';
		                if (localStorage.getItem('initial_exam') == 'true') {
		                	initial_checked += 'checked="checked"';
		                	cls += 'true';
		                }

//		                console.log(6)
		                table_strr += '<td id = "initial_' + operation_id + '" class="text-center ' + cls + '"><input disabled="disabled" type="checkbox" name="initial_' + operation_id + '" ' + initial_checked + '></td>';
						table_strr += '<td class = "' + selected_treatment_temp.treatment_id + '" '
							+ 'id = "desc_' + operation_id + '">' +
							selected_treatment_temp.treatment_name + '</td>';

                        // parent line values
                        var old_diag_val = $('#dignosis_code_'+old_op).val();
                        old_diag_val = old_diag_val ? old_diag_val : '';
                        var old_diag_id = $('#dignosis_code_'+old_op).attr('data-id');
                        old_diag_id = old_diag_id ? old_diag_id : 'false';
                        var old_note = $('#dignosis_note_'+old_op).val();
                        old_note = old_note ? old_note : '';

						table_strr += '<td id="dignosis_' + operation_id +
								'"><input class="diagnosis_code" id="dignosis_code_' +
								operation_id + '" value="' + old_diag_val +
								'" data-id="'+ old_diag_id +'"/></td>';
                		table_strr += '<td id = "dignosis_note_td' + operation_id +
								'"><input class="dignosis_note" autocomplete="off" id="dignosis_note_' +
								operation_id + '" value="'+ old_note +'"/></td>';
//                        console.log("eeeeeeee copy original fnctn ")
                        var tooth_selected_array = self.get_teeth_type_based_numbering(type, selected_tooth_temp);
                        if (type == 'palmer') {
						    table_strr += '<td  class="' + tooth_selected_array + '"id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
						} else if (type == 'universal') {
							table_strr += '<td class = "' + selected_tooth_temp + '" id = "tooth_' + operation_id + '">' + selected_tooth_temp + '</td>';
						} else if (type == 'iso') {
                            table_strr += '<td class="' + tooth_selected_array + '" id = "tooth_' + operation_id + '">' + tooth_selected_array + '</td>';
						}
						table_strr += '<td class="col_stat" id = "status_' + operation_id +
						    '" status_name = "'+status_defined+'">' + status_to_use + '</td>';

					   if(!tooth_by_part){
						table_strr += '<td id = "surface_' + operation_id + '">';
						_.each(surfaces, function(each_surf) {
							table_strr += each_surf + ' ';
						});
						self_var.increment_thread(selected_surface_temp);
						table_strr += '</td>';
						}else{
						table_strr += '<td id = "surface_' + operation_id + '">' +surfaces+'</td>';

						tooth_by_part == 0;
						}

						table_strr += '<td id = "dentist_' + operation_id + '" ' +
							'data-id="' + doctor_id + '">' + doc_name + '</td>';

						/*input box for amount field*/
						var amount_input;
						if (status_to_use == 'Planned') {
							amount_input = '<input type="number"  ' +
								' value="'+ t_charge +'" />';
						}
						else {
							amount_input = '<input type="number" readonly="True"' +
								' value="'+ t_charge +'" />';
						}

						table_strr += '<td class="col_amt" id = "amount_' + operation_id + '">' + amount_input + '</td>';

						table_strr += '<td style="display:none;" class="progress_table_actions" id="action_' + operation_id + '">' +
							selected_treatment_temp.action + '</td>';
						table_strr += '<td class = "delete_td" id = "delete_' + operation_id + '">' +
							'<img src = "/pragtech_dental_management/static/src/img/delete.png" height="20px" width="20px"/>'
							+ '</td>';
						table_strr += '<td style="display:none;" class="copy_td" id = "copy_' + operation_id + '">' +
								'<img src="/pragtech_dental_management/static/src/img/copy.png" height="20px" width="20px"/>' +
								'</td>';
						table_strr += '<td style="display:none" id="previous_' + operation_id + '">' + is_prev_record + '</td>';
//						inv_status = "'"+inv_status+"'";
						table_strr += '<td style="display:none" ><input value="'
						    + inv_status + '" id="inv_status_' + operation_id + '"/></td>';
						table_strr += '</tr>';

//						console.log(66);
                        let old_options = self.parse_line($("#operation_" + old_op));
                        old_options.treatment_id = selected_treatment_temp.treatment_id;
                        table_strr = self._process_table_row(table_strr, old_options);
						$('#progres_table').append(table_strr);
						$('#dignosis_code_' + operation_id).focus();
						$('#operation_' + operation_id).addClass('selected_operation');

                        $('#operation_' + operation_id).click(function() {
                            var found = self_var.$el.find('.selected_operation');
                            if (found) {
                                found.removeClass("selected_operation");
                            }
                            var old_class = $(this).attr('class');
                            var new_class = old_class ? old_class + ' selected_operation' : 'selected_operation';

                            $(this).attr('class', new_class);
                        });

                        $('#dignosis_code_'+operation_id).autocomplete({
                            select: function (event, ui) {
                                var terms = split(this.value);
                                // remove the current input
                                terms.pop();
                                // add the selected item
                                terms.push(ui.item.label);
                                this.value = terms;
                                $(this).attr('data-id', ui.item.value);
                                return false;
                            },
                            source: function (request, response) {
                                // delegate back to autocomplete, but extract the last term
        //                        if (reg_patient === true) {
                                var res = $.ui.autocomplete.filter(
                                    dignosis_records, extractLast(request.term));
                                response(res);
                            },
                            position: {
                                collision: "flip"
                            }
                        });
                        $('#delete_' + operation_id).click(function() {
                            var x = window.confirm("Are you sure you want to delete?");
                            if (x) {
                                update = false;
                                cont = false;
                                var actual_id = String(this.id).substr(7);
                                actual_id = parseInt(actual_id);
                                var line_id = $('#operation_' + actual_id).attr('data-id');
                                var tabel = document.getElementById('operations');
                                var tr = document.getElementById('operation_' + actual_id);
                                var tooth = document.getElementById('tooth_' + actual_id);
                                var desc_class = $("#desc_" + actual_id).attr('class');
                                var tooth_id = $(tooth).attr('class');
                                var status = document.getElementById('status_' + actual_id);
                                var status_name = $(status).attr('status_name')
                                if (!isNaN(line_id) && (status_name == 'completed' || status_name == 'in_progress')) {
                                    alert('Cannot delete');
                                }
                                else {
                                    var action = document.getElementById('action_' + actual_id);
                                    var action_id = action.innerHTML;
                                    var tooth_id = $(tooth).text();
                                    var surface_vals = ($('#surface_' + actual_id).text()).split(' ')[0];
                                    self.delete_color_remove(self, type, surface_vals, tooth_id);
//                                    {
//                                        var surface_vals = ($('#surface_' + actual_id).text()).split(' ');
//                                        var surf_list = new Array();
//                                        _.each(surface_vals, function(sv) {
//                                            if ($('#view_' + tooth_id + '_center').attr('class') && $('#view_' + tooth_id + '_center').attr('class').split(' ')[1] == sv) {
//                                                surf_list.push('view_' + tooth_id + '_center');
//                                            }
//                                            if ($('#view_' + tooth_id + '_right').attr('class') && $('#view_' + tooth_id + '_right').attr('class').split(' ')[1] == sv) {
//                                                surf_list.push('view_' + tooth_id + '_right');
//                                            }
//                                            if ($('#view_' + tooth_id + '_left').attr('class') && $('#view_' + tooth_id + '_left').attr('class').split(' ')[1] == sv) {
//                                                surf_list.push('view_' + tooth_id + '_left');
//                                            }
//                                            if ($('#view_' + tooth_id + '_top').attr('class') && $('#view_' + tooth_id + '_top').attr('class').split(' ')[1] == sv) {
//                                                surf_list.push('view_' + tooth_id + '_top');
//                                            }
//                                            if ($('#view_' + tooth_id + '_bottom').attr('class') && $('#view_' + tooth_id + '_bottom').attr('class').split(' ')[1] == sv) {
//                                                surf_list.push('view_' + tooth_id + '_bottom');
//                                            }
//                                        });
//                                        self_var.decrement_thread(surf_list);
//                                    }
//                                    var new_surfaces = surfaces, upper_jaw_flag = false, lower_jaw_flag = false;
//                                    if (action_id == 'missing') {
//                                        $($("#" + $('#' + tooth_id).attr('id')).css('visibility', "visible").attr('class', 'teeth'));
//                                        $("#view_" + $('#' + tooth_id).attr('id') + "_top,#view_" + $('#' + tooth_id).attr('id') + "_left,#view_" + $('#' + tooth_id).attr('id') + "_bottom,#view_" + $('#' + tooth_id).attr('id') + "_right,#view_" + $('#' + tooth_id).attr('id') + "_center").attr('visibility', 'visible');
//                                        $("#view_" + $('#' + tooth_id).attr('id') + "_top,#view_" + $('#' + tooth_id).attr('id') + "_left,#view_" + $('#' + tooth_id).attr('id') + "_bottom,#view_" + $('#' + tooth_id).attr('id') + "_right,#view_" + $('#' + tooth_id).attr('id') + "_center").attr('fill', 'white');
//                                    } else {
//                                        self.excluded_tooth['tooth_ids'] = {};
//                                        _.each(surface_vals, function(surf_val) {
//                                            if (!surf_val) {}
//                                            else {
//                                                for (var op = 1; op <= operation_id; op++) {
//                                                    var op_id = document.getElementById('operation_' + op), surface;
//                                                    if (op_id) {
//                                                        surface = document.getElementById('surface_' + op);
//                                                        var keys = $.map(self.excluded_tooth['tooth_ids'], function(v, i){
//                                                          return i;
//                                                        });
//                                                        var tmp2 = $(surface).text().split(' ')[0];
//                                                        if (tmp2 == surf_val) {
//                                                            if (keys.includes(surf_val)) {
//                                                                self.excluded_tooth['tooth_ids'][surf_val]++;
//                                                             }
//                                                             else {
//                                                                self.excluded_tooth['tooth_ids'][surf_val] = 0;
//                                                             }
//                                                        }
//                                                        if (surf_val.split('_')[0] == 'toothcap') {
//                                                            if (tmp2 == 'Upper_Jaw') {
//                                                                upper_jaw_flag = true;
//                                                            }
//                                                            else if (tmp2 == 'Lower_Jaw') {
//                                                                lower_jaw_flag = true;
//                                                            }
//                                                        }
//                                                    }
//                                                }
//                                            }
//                                        });
//                                if ($('#view_' + tooth_id + '_bottom').attr('class') && parseInt(($('#view_' + tooth_id + '_bottom').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_bottom').attr('id')).attr('fill', 'white');
//                                if ($('#view_' + tooth_id + '_right').attr('class') && parseInt(($('#view_' + tooth_id + '_right').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_right').attr('id')).attr('fill', 'white');
//                                if ($('#view_' + tooth_id + '_center').attr('class') && parseInt(($('#view_' + tooth_id + '_center').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + 17 + '_center').attr('id')).attr('fill', 'white');
//                                if ($('#view_' + tooth_id + '_left').attr('class') && parseInt(($('#view_' + tooth_id + '_left').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_left').attr('id')).attr('fill', 'white');
//                                if ($('#view_' + tooth_id + '_top').attr('class') && parseInt(($('#view_' + tooth_id + '_top').attr('class')).split(' ')[3]) == 0)
//                                    $("#" + $('#view_' + tooth_id + '_top').attr('id')).attr('fill', 'white');
//
//                                new_surfaces = [];
//                                _.each(surfaces, function (surf_val) {
//                                    if (self.excluded_tooth['tooth_ids'][surf_val] > 0) {}
//                                    else if (surf_val.split('_')[0] == 'toothcap') {
//                                        var temp1 = parseInt(surf_val.split('_')[1]);
//                                        if (temp1 < 17 && upper_jaw_flag == true) {}
//                                        else if (temp1 > 16 && temp1 <=32 && lower_jaw_flag == true) {}
//                                        else {
//                                            new_surfaces.push(surf_val);
//                                        }
//                                    }
//                                    else {
//                                        new_surfaces.push(surf_val);
//                                    }
//                                });
//							}
//                            localStorage.setItem('toDel', new_surfaces);

							tr.parentNode.removeChild(tr);
							for (var index = 0; index < treatment_lines.length; index++) {
								if (treatment_lines[index].tooth_id == tooth_id) {
									for (var i2 = 0; i2 < treatment_lines[index].treatments.length; i2++) {
										if (treatment_lines[index].treatments[i2].treatment_id == parseInt(desc_class)) {
											treatment_lines.splice(index, 1);
											operation_id += 1;
											var found = self_var.$el.find('.selected_treatment_temp');
											if (found) {
												found.removeClass("selected_treatment_temp");
											}
											return;
										}
									}
								}
							}
                            /*Remove treatment line from db*/
                            list_delete_line_id.push(line_id);
						}
					}
				});
			}
		});
		});
		},
		/*update_diag_code: function (id, value) {
		    $('#'+id).attr('data-id', dignosis_records[value].id);
		},*/
		process_cached_list: function (m_surf) {
            var self = this, teeth_str = "";
            var surf_string = "", temp_list = [], result;
            if (m_surf) {
                var surf_list = m_surf[1].split(',');
                var surfaces_list = m_surf[2] ? m_surf[2][0].split(','):[];
                var teeth_list = m_surf[0].split(',');

                for (var j in surfaces_list) {
                    if (!special_surfaces.includes(surfaces_list[j].split('_')[1])) {
                        teeth_str += surfaces_list[j] + ",";
                    }
                }
                for (var j in surf_list) {
                    var s_s = surf_list[j].split('_')[1];
                    if (special_surfaces.includes(s_s)) {
                        var t_id = surf_list[j].split('_')[0];
                        if (t_id >= 1 && t_id <= 5) {
                            /*CASE A*/
                            result = self.build_case_a(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                        else if (t_id >= 6 && t_id <= 11) {
                            /*CASE B*/
                            result = self.build_case_b(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                        else if (t_id >= 12 && t_id <= 16) {
                            /*CASE C*/
                            result = self.build_case_c(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                        else if (t_id >= 17 && t_id <= 21) {
                            /*CASE D*/
                            result = self.build_case_d(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                        else if (t_id >= 22 && t_id <= 27) {
                            /*CASE E*/
                            result = self.build_case_e(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                        else if (t_id >= 28 && t_id <= 32) {
                            /*CASE F*/
                            result = self.build_case_f(
                                s_s,
                                t_id);
                            temp_list.push(result);
                            surf_string += result + ",";
                        }
                    }
                }

                return [temp_list, surf_string, teeth_str];
            }

            /*for (var i_l in self.cached_teeth_list) {
                if (!special_surfaces.includes(self.cached_teeth_list[i_l][1])) {
                    teeth_str += i_l + ",";
                    continue;
                }
                var t_id = self.cached_teeth_list[i_l][0];

                if (t_id >= 1 && t_id <= 5) {
                    result = self.build_case_a(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
                else if (t_id >= 6 && t_id <= 11) {
                    result = self.build_case_b(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
                else if (t_id >= 12 && t_id <= 16) {
                    result = self.build_case_c(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
                else if (t_id >= 17 && t_id <= 21) {
                    result = self.build_case_d(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
                else if (t_id >= 22 && t_id <= 27) {
                    result = self.build_case_e(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
                else if (t_id >= 28 && t_id <= 32) {
                    result = self.build_case_f(
                        self.cached_teeth_list[i_l][1],
                        t_id);
                    temp_list.push(result);
                    surf_string += result + ",";
                }
            }
            return [temp_list, surf_string, teeth_str];*/
        },
		get_treatment_cats : function() {
			var $def = $.Deferred();
			var self = this;
//			new Model('product.category').call('get_treatment_categs', [self.patient_id]).then(function(treatment_list) {
//				$def.resolve(treatment_list);
//			});
			rpc.query({
                model: 'product.category',
                method: 'get_treatment_categs',
                args: [self.patient_id, self.insurance, self.doctor],
            })
            .then(function(treatment_list) {
            	$def.resolve(treatment_list);
            });
			return $def;
		},

		patient_history : function() {
			var $def = $.Deferred();
			var self = this;
			if (!self.patient_id) {
				alert('Session Expired!!');
				window.location = '/web';
			}

            var discount_diff = this.getSession().user_has_group(
			    'pragtech_dental_management.group_enable_discount_in_payment_lines');
            var treatment_diff = rpc.query({
                method: 'fetch_edit_status',
                model: 'product.product',
                args: [],
            });

            var history_diff = rpc.query({
                model: 'medical.patient',
                method: 'get_patient_history',
                args: [self.patient_id, self.appointment_id]
            });

            $.when.apply($, [treatment_diff, discount_diff, history_diff])
                .then(function (treatment_by_id, has_group, history_res) {
                    self.treatment_by_id = treatment_by_id;
                    self.manage_discount = has_group;
                    if (!has_group)
    			        self.$("td.col_disc").remove();

                    let patient_history = history_res[0];
                    Missing_Tooth = patient_history[0];
                    patient_history.splice(0, 1);
                    other_patient_history = patient_history;
                    self.treatment_by_surface = history_res[1];
                    self.add_tooltip('mapster');
                    $def.resolve(patient_history);
                });

			return $def;
		},
		// add_tooltip: function(map_type) {
		//     let history = this.treatment_by_surface;
		//     var self = this;
		//     var image1 = $('#UT');
		//     var image2 = $('#LT');
		//     var image3 = $('#childUT');
		//     var image4 = $('#childLT');

		//     var default_options = {
		//         fillOpacity: 0.5,
		//         render_highlight: {
		//             fillColor: '2aff00',
		//             stroke: true,
		//         },
		//         render_select: {
		//             fillColor: 'ff000c',
		//             stroke: false,
		//         },
		//         fadeInterval: 50,
		//         isSelectable: true,
		//         mapKey: 'data-key',
		//         showToolTip: true,

		//         onConfigured: function() {
		//             var csv = '';
		//             var toothkey = localStorage.getItem('test') || "";

		//             upkey = localStorage.getItem('upperkeys');
		//             lowkey = localStorage.getItem('lowerkeys');
		//             childupkey = localStorage.getItem('childupperkeys');
		//             childlowkey = localStorage.getItem('childlowerkeys');
		//             var temp = toothkey.split(","),
		//                 val, new_val, toothkey2 = "";
		//             for (var t = 0; t < temp.length; t++) {
		//                 try {
		//                     new_val = temp[t].split("_");
		//                     val = new_val[1];
		//                     if (new_val[0] == 'toothcap' && val && parseInt(val) < 10) {
		//                         temp[t] = new_val[0] + "_" + parseInt(val);
		//                     }
		//                 } catch (err) {}
		//                 toothkey2 += temp[t] + ",";
		//             }
		//             if (toothkey2) {
		//                 toothkey2 = toothkey2.slice(0, -1);
		//             }
		//             csv = toothkey2 ? csv + toothkey2 : csv;
		//             csv = upkey ? csv + upkey : csv;
		//             csv = lowkey ? csv + lowkey : csv;
		//             csv = childupkey ? csv + childupkey : csv;
		//             csv = childlowkey ? csv + childlowkey : csv;

		//             var setChk = (toothkey2 || upkey || lowkey);
		//             if (setChk) {
		//                 $('input:checkbox[name=mouthselection]').each(function(event) {
		//                     if ($(this).is(':checked')) {
		//                         console.log("____test1")
		//                         var selected_chkbox = ($(this).val());
		//                         if (selected_chkbox == 'uppermouth') {
		//                             image1.mapster('set', true, csv);
		//                         }
		//                         if (selected_chkbox == 'lowermouth') {
		//                             image2.mapster('set', true, csv);
		//                         }
		//                         if (selected_chkbox == 'uppermouth_child') {
		//                             image3.mapster('set', true, csv);
		//                         }
		//                         if (selected_chkbox == 'lowermouth_child') {
		//                             image4.mapster('set', true, csv);
		//                         }
		//                     }
		//                 });
		//             }
		//         }
		//     };
		//     console.log("____test2")
		//     if (map_type == 'mapster') {
		//         /*normal case: images and mapping using mapster*/
		//         let area_list = [];
		//         _.each(history, function(v, k) {
		//             let tool_tip = self._process_tooltip_msg(v);
		//             area_list.push({
		//                 key: self.get_actual_key(k),
		//                 toolTip: tool_tip
		//             });
		//         });

		//         let full_options = _.extend({}, default_options, {
		//             areas: area_list
		//         });
		//         console.log("____default_options" + default_options)
		//         console.log("__full_options__" + full_options)
		//         image1.mapster(full_options);
		//         image2.mapster(full_options);
		//         image3.mapster(full_options);
		//         image4.mapster(full_options);
		//     } else if (map_type == 'svg') {
		//         /*handling the svg path elements*/
		//         _.each(history, function(v, k) {
		//             /*there is elements with same class for child and adult. Hoping that they won't come together
		//             in a chart ?*/
		//             let $svg = $("path." + self.get_actual_key(k));
		//             let $tool_tip = self._process_tooltip_msg(history[k]);
		//             $svg.popover({
		//                 html: true,
		//                 content: function() {
		//                     return $tool_tip;
		//                 },
		//                 trigger: 'hover',
		//                 placement: 'top',
		//                 container: 'body'
		//             });
		//         });
		//     }
		// },
		get_user : function(uid) {
//			new Model('res.partner').call('get_user_name', [uid]).then(function(uname) {
//				user_name = uname;
//			});
			rpc.query({
                model: 'res.partner',
                method: 'get_user_name',
                args: [uid],
            })
            .then(function(uname) {
            	user_name = uname;
            });
		},
		/*CHANGED HERE, ADDED THIS FUNCTION*/
		get_diagnosis_records:function () {
			rpc.query({
                model: 'diagnosis',
                method: 'get_all_records',
                args: [],
            }).then(function(res) {
            	for(var i=0; i<res.length; i++){
            	    var temp = {
            	        label: res[i]['code'] + '/' + res[i]['description'],
            	        value: res[i]['id']
            	    };
					dignosis_records.push(temp);
					//dignosis_records[res[i]['code'] + '/' + res[i]['description']] = res[i];
					dignosis_records_by_id[res[i]['id']] = res[i];
				}
            });
		},
		getkeysFromTable : function(){
//		//console.log("sending keylist to set",keyList)
		return keyList;

		},

		initial_examination:function (initial_exam) {
			$('#progres_table tr').each(function() {
				if (!initial_exam) {
					if ($(this).hasClass('hidden')) {$(this).removeClass('hidden');}
				}
				else {
					var checkbox_initial = $(this).find("td[id*='initial']").children().is(":checked")
					if (!checkbox_initial) {
						if (!$(this).hasClass('hidden')) {$(this).addClass('hidden');}
					}
				}
		    });
		}


	});


	core.action_registry.add('dental_chart', DentalChartView);

	return {
		DentalChartView : DentalChartView,
	};

});

//var map = $('#UT'),
//// a map tracking the state of each area
//selStates = {},
//// rendering options for the 1st selected state
//selected1opts = {
//    fillColor: '00ff00',
//    stroke: true,
//    strokeColor: '000000',
//    strokeWidth: 2
//},
//// rendering options for the 2nd selected state
//selected2opts = {
//    fillColor: 'ff0000',
//    stroke: true,
//    strokeColor: '00ff00',
//    strokeWidth: 1
//};
//
//var renderOpts = [selected1opts, selected2opts];
//
//function onClick(data) {
//
//// get current state (0,1,2) -- default to zero which means unset
//console.log("On click*********************************",data);
//var cur = selStates[data.key] || 0,
//    next = (cur + 1) % 3;
//
//// always unset: if state 0, this is all we need to do. if state
//// 2, we have to unset first, since setting the state for an area
//// that's already selected will do nothing. If it happens to be going from
//// 0 to 1, then no harm done.
//
//map.mapster('set', false, data.key);
//
//if (next) {
//    // now set the area state using the correct options
//    map.mapster('set', true , data.key,renderOpts[cur]);
//}
//
//// update local store with current state
//// add 1, and apply a modulus of 3 to get new state
//
//selStates[data.key] = next;
//}
//
//map.mapster({
//mapKey: 'data-key',
//// setting isSelectable=false will prevent imagemapster from using its own click-select
//// handling. You could also return false from the onClick event to stop internal handling
//isSelectable: false,
//onClick: onClick
//});
