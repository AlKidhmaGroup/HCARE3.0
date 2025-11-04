odoo.define('pragtech_dental_management.widgets', function(require) {
"use strict";
var core = require('web.core');
var Dialog = require('web.Dialog');
var FormView = require('web.FormView');
var rpc = require('web.rpc');
var _t = core._t;
var QWeb = core.qweb;
var FormRenderer = require('web.FormRenderer');
/*FormView.include({
	load_record: function(record) {
		this._super(record);
		var self = this;
		if(self.model === 'medical.patient'){
			var msg_alert = "<div><p>" + _t('Medical Alert: ') + _t(record.critical_info)+"</p>"+
	        "<p>" + _t('Medical History: ') + _t(record.medical_history)+"</p></div>"
	        Dialog.alert(self, msg_alert, {'$content':msg_alert,'title':_t("Medical Alert"),'size':'small'});
		}
	},

});
*/
FormRenderer.include({
	init: function (parent, state, params) {
		this._super(parent, state, params);
		var self = this;
		if (!state.data.show_only_dr_alert ){
		    if (state.data.patient_history || state.data.medical_history || state.data.critical_info){
                var med = ''
                var pat = ''
                if (state.data.medical_history) {
                    med = state.data.medical_history
                }
                if (state.data.patient_history) {
                    pat = state.data.patient_history
                }
                var msg_alert = "<div>"
                if(state.data.critical_info){
                    msg_alert += "<p>" + _t('Medical Alert: ') + _t(state.data.critical_info)+"</p>";
                }
                if(med || pat){
                    msg_alert += "<p>" + _t('Medical History: ') + _t(med)+ _t(pat)+"</p>";
                }
                msg_alert += "</div>"
                Dialog.alert(self, msg_alert, {'$content':msg_alert,'title':_t("Medical Alert"),'size':'small'});
            }
		}
		else{
		    if (state.data.patient_history || state.data.medical_history){
                var med = ''
                var pat = ''
                if (state.data.medical_history) {
                    med = state.data.medical_history
                }
                if (state.data.patient_history) {
                    pat = state.data.patient_history
                }
                var msg_alert = "<div><p>" + _t('Medical History: ') + _t(med)+ _t(pat)+"</p></div>"
                Dialog.alert(self, msg_alert, {'$content':msg_alert,'title':_t("Medical Alert"),'size':'small'});
            }
		}
        if (!isNaN(state.res_id))
            rpc.query({
                model: state.model,
                method: 'get_preview_messages',
                args: [[state.res_id]]
            }).then(function (msgs) {
                self.doPreviewMessages(msgs);
            });
    },
    doPreviewMessages: function (msgs) {
        if (!msgs || msgs.length == 0)
            return
        let $modal = $(QWeb.render('pragtech_dental_management.FormPreviewMessage', msgs[0]));
        $modal.modal().show();
        msgs = msgs.slice(1);
        var self = this;
        if (msgs.length > 0)
            $modal.find(".close_preview").click(function () {
                self.doPreviewMessages(msgs);
            });
    }
});

});