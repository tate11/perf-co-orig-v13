odoo.define('pcp_barcode.lines_widget', function (require) {
    "use strict";
    var core = require("web.core");
    var QWeb = core.qweb;
    var LinesWidget = require('stock_barcode.LinesWidget');

    LinesWidget.include({
        events: _.extend({}, LinesWidget.prototype.events, {
            'click .o_create_lot_name': '_onClickCreateLotName',
        }),
        /**
         * Add scanned license plate tag to line
         */
        addLicensePlatetoLine: function(id_or_virtual_id, lp_name) {
            var $line = this.$("[data-id='" + id_or_virtual_id + "']");
            $line.find('.lp_tags').append('<span class="badge badge-pill" style="color:#777777;margin-left:2px;font-size:12px;">'+ lp_name + '</span>')
        },

        _onClickCreateLotName: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var $line = $(ev.target).parents('.o_barcode_line');
            this.trigger_up('create_lot_name', {$line: $line});
        },

        _reloadLine:function($line, lineDescription){
            // Update Lot Name of move_line on LineWidget
            var move_line_id = $line.data('id');
            this.page.lines.forEach(function (record) {
                if (record.id == move_line_id){
                    record.lot_name = lineDescription.lot_name;
                }
            });

            // Reload data of line on view
            var $replaceLine = $(QWeb.render('stock_barcode_lines_template', {
                lines: this.getProductLines([lineDescription]),
                packageLines: this.getPackageLines([lineDescription]),
                groups: this.groups,
                model: this.model,
            }));
            $line.replaceWith($replaceLine);
            $replaceLine.on('click', '.o_edit', this._onClickEditLine.bind(this));
            $replaceLine.on('click', '.o_package_content', this._onClickTruckLine.bind(this));
        },
    });

    return LinesWidget;
});