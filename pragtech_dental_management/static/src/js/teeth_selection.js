odoo.define('pragtech_dental_management.chart_action_ext', function(require) {
    "use strict";

    var chart_action = require("pragtech_dental_management.chart_action");

    $(document).ready(function() {
        var image1 = $('#UT');
        var image2 = $('#LT');
        var image3 = $('#childUT');
        var image4 =$('#childLT');

        var getKeySelectedArray = '';
        var upkey = '';
        var lowkey = '';
        var childupkey = '';
        var childlowkey = '';
        var status = '';

        status=localStorage.getItem('status');
        console.log("entering mapkeys document  ",status);
        if(!status)
        {
        localStorage.removeItem('test');
        localStorage.removeItem('upperkeys');
        localStorage.removeItem('lowerkeys');
        localStorage.setItem('status','0')
        }


        $(document).on('click', '.delete_td', function(){
            var toRemove = localStorage.getItem('toDel');
            if(toRemove){
                var val, new_val,point_sa, toRemove2=toRemove.split(","), temp = [];
                _.each(toRemove2, function(item) {
                    try {
                        new_val = item.split("_");
                        val = new_val[1];
                        if (new_val[0] == 'toothcap' &&
                            val && parseInt(val) < 10) {
                            var t = new_val[0] + "_" + parseInt(val);
                            temp.push(t);
                        }
                        /*For middle tooth images*/
                        else if (["buccal","mesial","lingual","distal","occlusal","labial","incisal"].includes(val)){
                            if (new_val[0] <= 5) {
                                if (["occlusal"].includes(val)){
                                    point_sa="center";
                                }
                                else if (["buccal"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["lingual"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="left";
                                }
                                    }
                            else if (new_val[0] <= 11) {

                                if (["labial"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["lingual"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="left";
                                }
                                else if (["incisal"].includes(val)){
                                    point_sa="center";
                                }
                            }
                            else if (new_val[0] <= 16) {
                                if (["buccal"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["lingual"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="left";
                                }
                                else if (["occlusal"].includes(val)){
                                    point_sa="center";
                                }
                            }
                            else if (new_val[0] <= 21) {
                                if (["lingual"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["buccal"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="left";
                                }
                                else if (["occlusal"].includes(val)){
                                    point_sa="center";
                                }

                            }
                            else if (new_val[0] <= 27) {
                                if (["lingual"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["labial"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="left";
                                }
                                else if (["incisal"].includes(val)){
                                    point_sa="center";
                                }
                           }
                            else{
                                if (["lingual"].includes(val)){
                                    point_sa="top";
                                }
                                else if (["mesial"].includes(val)){
                                    point_sa="right";
                                }
                                else if (["buccal"].includes(val)){
                                    point_sa="bottom";
                                }
                                else if (["distal"].includes(val)){
                                    point_sa="left";
                                }
                                else if (["occlusal"].includes(val)){
                                    point_sa="center";
                                }

                            }
                            item='view_'+new_val[0]+'_'+point_sa;
                            $("#" +item ).attr('fill', 'white')
                            temp.push(item);
                        }
                        else {
                            temp.push(item);
                        }

                    }
                    catch (err) {}
                });
                toRemove = temp;
                image1.mapster('set', false, toRemove);
                image2.mapster('set', false, toRemove);
                image3.mapster('set', false, toRemove);
                image4.mapster('set', false, toRemove);
            }
        });

        //$("input[name$='checkfield']").change(function() {alert('helooooooooo')});
        //
        //$("#mapchk").on('change', function() {
        //    alert("triggered!");
        //});



        $(document).on("change", "input[type=checkbox]", function(e) {
            var checked = $("input[type=checkbox]:checked");
            var checkedValues = checked.map(function(i) { return $(this).val() }).get()
            var chkstr = checkedValues.join();
            if ($('#select_upper_mouth:checked').length == 0) {
                upkey = localStorage.getItem('upperkeys');
                image1.mapster('set', false, upkey);
            }
            if ($('#select_lower_mouth:checked').length == 0) {
                lowkey = localStorage.getItem('lowerkeys');
                image2.mapster('set', false, lowkey);
            }
            if ($('#select_upper_mouth_child:checked').length == 0) {
                childupkey = localStorage.getItem('childupperkeys');
                image3.mapster('set', false, childupkey);
            }
            if ($('#select_lower_mouth_child:checked').length == 0) {
                childlowkey = localStorage.getItem('childlowerkeys');
                image4.mapster('set', false, childlowkey);
            }
            getKeySelectedArray = Object.values(checkedValues);
            _.each(getKeySelectedArray, function(sol) {
                if (sol == 'uppermouth') {
                    upkey = localStorage.getItem('upperkeys');
                    image1.mapster('set', true, upkey);
                }
                if (sol == 'uppermouth_child') {
                    childupkey = localStorage.getItem('childupperkeys');
                    image3.mapster('set', true, childupkey);
                }
                if (sol == 'lowermouth'){
                    lowkey = localStorage.getItem('lowerkeys');
                    image2.mapster('set', true, lowkey);
                }
                if (sol == 'lowermouth_child'){
                    childlowkey = localStorage.getItem('childlowerkeys');
                    image4.mapster('set', true, childlowkey);
                }
            });
        });

        var default_options = {
            fillOpacity: 0.5,
            render_highlight: {
                fillColor: '2aff00',
                stroke: true,
            },
            render_select: {
                fillColor: 'ff000c',
                stroke: false,
            },
            fadeInterval: 50,
            isSelectable: true,
            mapKey: 'data-key',
            showToolTip: true,

            onConfigured:  function() {
                var csv = '';
                var toothkey = localStorage.getItem('test') || "";

                upkey = localStorage.getItem('upperkeys');
                lowkey = localStorage.getItem('lowerkeys');
                childupkey = localStorage.getItem('childupperkeys');
                childlowkey = localStorage.getItem('childlowerkeys');
                var temp = toothkey.split(","), val, new_val, toothkey2 = "";
                for (var t=0;t<temp.length;t++) {
                    try {
                        new_val = temp[t].split("_");
                        val = new_val[1];
                        if (new_val[0] == 'toothcap' && val && parseInt(val) < 10) {
                            temp[t] = new_val[0] + "_" + parseInt(val);
                        }
                    }
                    catch (err) {}
                    toothkey2 += temp[t] + ",";
                }
                if (toothkey2) {
                    toothkey2 = toothkey2.slice(0, -1);
                }
                csv = toothkey2 ? csv + toothkey2 : csv;
                csv = upkey ? csv + upkey : csv;
                csv = lowkey ? csv + lowkey : csv;
                csv = childupkey ? csv + childupkey : csv;
                csv = childlowkey ? csv + childlowkey : csv;

                var setChk = (toothkey2||upkey||lowkey);
                if(setChk){
                    $('input:checkbox[name=mouthselection]').each(function(event) {
                        if($(this).is(':checked')) {
                            var selected_chkbox =($(this).val());
                            if (selected_chkbox == 'uppermouth') {
                                image1.mapster('set', true, csv);
                            }
                            if (selected_chkbox == 'lowermouth') {
                                image2.mapster('set', true, csv);
                            }
                            if (selected_chkbox == 'uppermouth_child') {
                                image3.mapster('set', true, csv);
                            }
                            if (selected_chkbox == 'lowermouth_child') {
                                image4.mapster('set', true, csv);
                            }
                        }
                    });
                }
            }
        };
        $.mapster.impl.init();

        //_.each([image1, image2, image3, image4], function (im) {
        //    let area_list = [];
        //    _.each(im.parent().find("area"), function (m_area) {
        //        let $a = $(m_area);
        //        area_list.push({
        //            key: $a.data('key'),
        //            toolTip: $("<div></div>")
        //        });
        //    });
        //
        //    let full_options = _.extend({}, default_options, {
        //        areas: area_list
        //    });
        //   im.mapster(full_options);
        //});

        $('#toothmapupper area, #lowermoutharea area, #child_uppermouth area, #child_lowermouth area').each(function() {
            $(this).mouseover(function() {
                var found = false;
                var description = ""
                var surface = $(this).attr('id');
                $('#progres_table tr').each(function() {
                    $(this).children().each(function() {
                        var table_surface = $(this).text().replace(" ", "").split(",")
                        for (var i = 0; i < table_surface.length; i++) {
                            if (surface == table_surface[i]) {
                                found = true;
                                description = $(this).parent().find("td[id*='desc']").text()
                            }
                        }
                    });
                });
//                if (found) {
//                    this.title = description
//                }
            });
        });


        //$('[data-toggle="tooltip"]').tooltip();
        chart_action.DentalChartView.include({
            get_actual_key: function (key) {
                let key_val = key;
                if (this.type == 'iso') {
                    let tmp = key.split("_");
                    let key_no = _.filter(tmp, function (t) { return !isNaN(t); })
                    key_val = key_val.replace(key_no[0], _.invert(this.Iso)[key_no[0]]);
                }
                return key_val
            },
            add_tooltip: function (map_type) {
                let history = this.treatment_by_surface;
                var self = this;

                if (map_type == 'mapster') {
                    /*normal case: images and mapping using mapster*/
                    let area_list = [];
                    _.each(history, function (v, k) {
                        let tool_tip = self._process_tooltip_msg(v);
                        area_list.push({
                            key: self.get_actual_key(k),
                            toolTip: tool_tip
                        });
                    });

                    let full_options = _.extend({}, default_options, {
                        areas: area_list
                    });
                    image1.mapster(full_options);
                    image2.mapster(full_options);
                    image3.mapster(full_options);
                    image4.mapster(full_options);
                }
                else if (map_type == 'svg') {
                    /*handling the svg path elements*/
                    _.each(history, function (v, k) {
                        /*there is elements with same class for child and adult. Hoping that they won't come together
                        in a chart ?*/
                        let $svg = $("path." + self.get_actual_key(k));
                        let $tool_tip = self._process_tooltip_msg(history[k]);
                        $svg.popover({
                            html: true,
                            content: function () {
                                return $tool_tip;
                            },
                            trigger: 'hover',
                            placement: 'top',
                            container: 'body'
                        });
                    });
                }
            },
            _process_tooltip_msg: function (data) {
                let $el = $("<div style='font-size:12px;width:100%;'>");
                let $ul = $("<ol class='treat_list'>");
                _.each(data, function (el) {
                    $ul.append($(
                        "<li>" + el.name + "<b>(" + el.state + ")</b>" + "</li>"
                    ));
                });
                $ul.appendTo($el);
                return $el
            },
        });
    });
});
//$('#toothmapupper area, #lowermoutharea area, #child_uppermouth area, #child_lowermouth area').each(function() {
//    $(this).click(function(e) {
//      e.preventDefault();
//      var image_as = $('#UT');
//      console.log("______________on click ____________________",this)
//      console.log("***********************************2",$(this).attr('data-key'),$(this).attr('title'))
//      console.log("\n data title^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",$(this).attr('data-original-title title'));
//        if ($(this).attr('title')){
//          console.log("___Already selected______________foundddddddddddddd",$(this).attr('data-key'));
//          var area_array=[]
//          area_array.push($(this).attr('data-key'))
//          console.log("Area array as=++++++++++++++++++++++++",area_array.join())
//
//
////            image_as.mapster({
//////                  set:true,
////                    areas: area_array.join(),
////                    fillColor:'00ffff'
////
////                });
//
//          var imagss_as=image_as.mapster({set: true, arear:area_array.join(), fillColor: '00ffff'});
//
//          var imagres_as=$(this).mapster('set', true, area_array.join(), {fillColor: '00ffff'});
//          console.log("******************11******************ENDDDDDDDD")
////            return false;
//        }
//        return false;
//    });

//});
