odoo.define('dental_chart_discount.ChartDiscount', function(require) {
	"use strict";

    var core = require("web.core");
    var session = require('web.session');
	var ChartAction = require('pragtech_dental_management.chart_action');

	var Qweb = core.qweb;

    ChartAction.DentalChartView.include({
        events: _.extend({}, ChartAction.DentalChartView.prototype.events, {
            'change .actual_amt_val .unit_price': '_onChangeDiscount',
            'change .disc_type_val .discount_fixed_percent': '_onChangeDiscount',
            'change .disc_perc_val .discount': '_onChangeDiscount',
            'change .disc_amt_val .discount_value': '_onChangeDiscount',
            'keydown .actual_amt_val .unit_price': 'onlyNumberKey',
            'keydown .disc_perc_val .discount': 'onlyNumberKey',
            'keydown .disc_amt_val .discount_value': 'onlyNumberKey',
        }),
        onlyNumberKey: function (evt) {
            // Only ASCII charactar in that range allowed
            var ASCIICode = (evt.which) ? evt.which : evt.keyCode;
            let to_exclude = [];
            let nav_keys = [37, 39, 38];
            let decimal_keys = [110, 190];
            let remove_keys = [8, 46];

            to_exclude = to_exclude.concat(nav_keys, decimal_keys, remove_keys);
            if (ASCIICode != 0 && ASCIICode > 31 &&
                    (ASCIICode < 48 || ASCIICode > 57) &&
                    (ASCIICode < 96 || ASCIICode > 105) &&
                    !to_exclude.includes(ASCIICode))
                return false;
            return true;
        },
        _format_amount: function (amount) {
            /*todo: expand later!*/
            return amount ? amount.toFixed(3) : amount;
        },
        _onChangeDiscount: function (e) {
            let $el = $(e.currentTarget);
            let $tr = $el.parent().parent();
            let discount_type = $tr.find("select.discount_fixed_percent").val() || '';
            let discount_percent = parseFloat($tr.find("input.discount").val() || 0);
            let discount_amount = parseFloat($tr.find("input.discount_value").val() || 0);
            let unit_price = parseFloat($tr.find("input.amount_after_discount").attr('original_amount') || 0)

            if (!this.validateDiscount($el, unit_price, discount_amount, discount_percent)) {
                alert("Invalid discount amount!")
                $el.val(0);
                discount_percent = 0, discount_amount = 0;
            }

            let amt_after_disc = this.find_line_price(
                unit_price, discount_type, discount_percent, discount_amount);

            let amount_fmt = this._format_amount(amt_after_disc);
            $tr.find("input.amount_after_discount").val(parseFloat(amount_fmt));
            if (discount_type == 'Fixed') {
                $tr.find("input.discount").val('');
                $tr.find("input.discount").attr("readonly", "readonly");
                $tr.find("input.discount_value").removeAttr("readonly");
            }
            else if (discount_type == 'Percent') {
                $tr.find("input.discount_value").val('');
                $tr.find("input.discount_value").attr("readonly", "readonly");
                $tr.find("input.discount").removeAttr("readonly");
            }
            else {
                $tr.find("input.discount").val('');
                $tr.find("input.discount").attr("readonly", "readonly");
                $tr.find("input.discount_value").val('');
                $tr.find("input.discount_value").attr("readonly", "readonly");
            }
        },

        validateDiscount: function ($el, unit_price, discount_value, discount) {
            let max_val = 0;
            if ($el.hasClass("discount")) {
                return discount > 100 ? false : true;
            }
            else if ($el.hasClass("discount_value")) {
                return discount_value > unit_price ? false : true;
            }
            else
                return true
        },
        find_line_price: function (unit_price, discount_type,
                                   discount_percent, discount_amount) {
            if (discount_type == 'Fixed') {
                return unit_price - discount_amount;
            }
            else if (discount_type == 'Percent') {
                return unit_price * (1 - (discount_percent / 100));
            }
            return unit_price
        },
        _resize_table_columns: function () {
            if (this.manage_discount) {
                let $tr = $("table#operations thead tr");

                // Description
                $tr.find("td:eq(2)").attr('width', '10%');
                // Diagnosis code
                $tr.find("td:eq(3)").attr('width', '7%');
                // Note
                $tr.find("td:eq(4)").attr('width', '8%');
                // Note
                $tr.find("td:eq(5)").attr('width', '7%');
                // surface
                $tr.find("td:eq(7)").attr('width', '15%');
                // dentist
                $tr.find("td:eq(8)").attr('width', '6%');
            }
        },
        _process_table_row: function (tr, options) {
		    var unit_price = 0;
		    options = options ? options : {};

            var $tr = $(tr);
            let $amt = $tr.find("td.col_amt").find("input");
            let status_name = $tr.find("td.col_stat").attr("status_name");

            $tr.addClass('color_' + status_name);

            if ($amt.length > 0) {
                $amt.addClass("amount_after_discount");
                if (this.manage_discount)
                    $amt.attr("readonly", "readonly");
                else if (!this.treatment_by_id[options.treatment_id]['amount_edit'])
                    $amt.attr("readonly", "readonly");

                unit_price = options.unit_price ? options.unit_price : $amt.val();
            }
            if (this.manage_discount) {
                var $discount_str = $(Qweb.render('dental_chart_discount.DiscountColumns', {}));
                /*setting default values*/
                $discount_str.find("input.unit_price").attr('value', unit_price);
                $discount_str.find(
                    "select.discount_fixed_percent option[value='" + options.discount_fixed_percent + "']"
                ).attr("selected", "selected");

                $discount_str.find("input.discount").attr('value', options.discount);
                $discount_str.find("input.discount_value").attr('value', options.discount_value);

                if (status_name == 'planned') {
                    switch (options.discount_fixed_percent) {
                        case 'Fixed': $discount_str.find("input.discount_value").removeAttr('readonly'); break;
                        case 'Percent': $discount_str.find("input.discount").removeAttr('readonly'); break;
                    };
                    if (this.treatment_by_id[options.treatment_id]['amount_edit'])
                        $discount_str.find("input.unit_price").removeAttr('readonly');
                }
                else {
                    this._setDiscountReadonly($discount_str);
                }
                /*insert into dom*/
                $tr.find("td.col_amt").before($discount_str);
            }

		    return $tr.prop('outerHTML');
		},
		_setDiscountReadonly: function ($el) {
		    $el.find("input.discount_value, input.discount, input.unit_price").attr("readonly", "readonly");
		    $el.find("select.discount_fixed_percent").attr("disabled", "disabled");
		},
		_process_surface_lines: function (l_id) {
		    var line_id, line_status, line_change, dentist_id, dignosis_code, diag_label;
		    var op_id = document.getElementById('operation_' + l_id);
		    $('#operation_' + l_id).removeClass('selected_operation');
            var initial = document.getElementById('initial_' + l_id);
            var teeth_id = document.getElementById('tooth_' + l_id);
            var created_date = document.getElementById('date_time_' + l_id);
            var prev_record = document.getElementById('previous_' + l_id);
            var status_id = document.getElementById('status_' + l_id);
            var status_name = $(status_id).attr('status_name');
            var dentist = document.getElementById('dentist_' + l_id);
            line_change = $(op_id).attr('line-change');
            if (line_change == 'initial') {
                /*the treatment line is changed from the chart*/
                dentist_id = $(dentist).attr("data-id");
            }
            else {
                /*the treatment line is not changed from the chart*/
                dentist_id = session.uid;
            }
            var surface = document.getElementById('surface_' + l_id);
            var desc = document.getElementById('desc_' + l_id);
            var categ_id = $(desc).attr('class');
            var surface_list = String(surface.innerHTML).split(' ');
            var tooth = $('#tooth_' + l_id).attr('class');
            var all_teeth = op_id.className;
            if ($(initial).hasClass("true")) {
                var all_teeth = op_id.className.replace(" examinationcolor", "");
            }
            var values = [];
            var vals = [];
            line_id = $(op_id).attr('data-id');
            line_status = 'new';
            if (status_name == 'in_progress' && line_id) {
                try {
                    var temp = $(status_id).attr('line_status');
                    if (temp && temp == 'old') {
                        line_status = 'old';
                    }
                }
                catch (err) {}
            }
            var amount = $('#amount_' + l_id + ' input').val();

            /*CHANGED HERE */
            dignosis_code = $('#dignosis_code_' + l_id).attr('data-id');
            diag_label = $('#dignosis_code_' + l_id).val();
            if (!diag_label) {
                dignosis_code = false;
            }
            var dignosis_note = $('#dignosis_note_' + l_id)[0].value;

            _.each(surface_list, function(each_surface) {
                vals.push(each_surface);
            });
            var categ_list = new Array();
            categ_list.push({
                'categ_id' : categ_id,
                'values' : vals
            });
            values.push(categ_list);
//					var actual_tooth = String(teeth_id.id);
            /*passing amount to the backend for updating to the database*/
            if (tooth == "-") { tooth = false; }
            var is_child = false;
            if(line_id=='false'){
                if(document.getElementById('child').checked){
                    is_child = true;
                }
            }
            let line_data = {
                'line_id': line_id,
                'status' : String(status_id.innerHTML),
                'status_name' : status_name,
                'teeth_id' : tooth,
                'dentist' : parseInt(dentist_id),
                'values' : categ_list,
                'prev_record' : prev_record.innerHTML,
                'multiple_teeth' : all_teeth,
                'dignosis_code': dignosis_code ? dignosis_code : false,
                'dignosis_description': dignosis_note,
                'amount': amount ? amount : false,
                'inv_status': $('#inv_status_' + l_id).attr('value'),
                'line_status': line_status,
                'initial': $(initial).hasClass("true"),
                'is_child': is_child,
            }
		    let $tr = $("#operation_" + l_id);
		    line_data = _.extend({}, line_data, this.parse_line($tr));
		    return line_data;
		},
		parse_line: function ($tr) {
		    return {
		        'unit_price': parseFloat($tr.find("input.unit_price").val() || 0),
		        'discount_fixed_percent': $tr.find("select.discount_fixed_percent").val() || '',
		        'discount': parseFloat($tr.find("input.discount").val() || 0),
		        'discount_value': parseFloat($tr.find("input.discount_value").val() || 0)
		    }
		}
    });
});
