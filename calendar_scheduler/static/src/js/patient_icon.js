odoo.define('calendar_scheduler.PatientIcon', function (require) {
    'use strict';

    /**
     * This widget adds a widget that shows an icon.
     * icon in the path /calendar_scheduler/static/src/img/insurance.jpeg will be used
     */

    var fieldRegistry = require('web.field_registry');
    var BasicFields = require('web.basic_fields');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var QWeb = core.qweb;


    var PatientIconWidget = BasicFields.InputField.extend({
        className: 'o_field_pat_icon',
        supportedFieldTypes: ['char'],

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
            this.icon_url = this.attrs.icon_url;
        },
        _render: function () {
            this._super();
            this.$el.addClass("pat_icon");
            this.$el.html(QWeb.render('calendar_scheduler.patient_icon', {
                custom_class: 'source_field_widget',
                icon_url: this.icon_url
            }));
        }
    });

    fieldRegistry.add('patient_icon', PatientIconWidget);

    return PatientIconWidget;
});
