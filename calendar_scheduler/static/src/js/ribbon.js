odoo.define('calendar_scheduler.ribbon', function (require) {
    'use strict';

    /**
     * This widget adds a ribbon on the top right side of the form
     *
     *      - You can specify the text with the title attribute.
     *      - You can specify a background color for the ribbon with the bg_color attribute
     *        using bootstrap classes :
     *        (bg-primary, bg-secondary, bg-success, bg-danger, bg-warning, bg-info,
     *        bg-light, bg-dark, bg-white)
     *
     *        If you don't specify the bg_color attribute the bg-success class will be used
     *        by default.
     */

    var widgetRegistry = require('web.widget_registry');
    var Widget = require('web.Widget');

    var RibbonWidget = Widget.extend({
        template: 'calendar_scheduler.ribbon',
        xmlDependencies: ['/calendar_scheduler/static/src/xml/ribbon.xml'],

        init: function (parent, data, options) {
            this._super.apply(this, arguments);
            this.text = options.attrs.title || options.attrs.text;
            this.bgColor = options.attrs.bg_color;
            this.custom_class = options.attrs.custom_class || "";
            this.show_stars = options.attrs.show_stars;
            this.visibility = options.attrs.visibility;
            this.data = data.data;
        },
        start: function () {
            this._super();
            if (this.visibility) {
                let f_domain = this.visibility.split("=");
                var show_el = true;
                try {
                    /*todo: update in future to handle complex domains*/
                    let f_val = f_domain[1] == 'true' ? true : (f_domain[1] == 'false' ? false : f_domain[1]);
                    switch ('=') {
                        case "=": {
                            show_el = this.data[f_domain[0]] == f_val ? true : false;
                            break;
                        }
                        default: show_el = true;
                    }
                }
                catch (err) {}
                if (!show_el)
                    this.$el.hide();
            }
            this.$el.parent().find(".oe_button_box").after(this.$el.outerHTML);
        }

    });

    widgetRegistry.add('web_ribbon', RibbonWidget);

    return RibbonWidget;
});
