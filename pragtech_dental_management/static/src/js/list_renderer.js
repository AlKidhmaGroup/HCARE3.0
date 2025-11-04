odoo.define('pragtech_dental_management.ListRenderer', function(require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");

    ListRenderer.include({
        _renderHeaderCell: function (node) {
            var $th = this._super(node);
            let attrs = node.attrs;
            let name = attrs.name;
            let field = this.state.fields[name];

            if (field && !field.sortable) {
                if (attrs.sort_by ||
                        (attrs.modifiers && attrs.modifiers.sort_by))
                    $th.addClass('o_column_sortable');
            }

            return $th;
        },
        _onSortColumn: function (event) {
            var name = $(event.currentTarget).data('name');
            let column = _.filter(this.columns, function (col) {
                return col.attrs && col.attrs.name == name;
            });
            column = column && column.length > 0 ? column[0] : null;
            var sort_by = null;
            if (column && column.attrs) {
                if (column.attrs.sort_by)
                    sort_by = column.attrs.sort_by;
                else if (column.attrs.modifiers)
                    sort_by = column.attrs.modifiers.sort_by;
            }

            if (sort_by) {
                this.trigger_up('toggle_column_order', {id: this.state.id, name: sort_by});
            }
            else
                this._super(event);
        },
    });
});
