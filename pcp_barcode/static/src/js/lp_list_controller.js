odoo.define('tote_picking_barcode.PickingListController', function (require) {
"use strict";

const core = require('web.core');
const ListController = require('web.ListController');
const Session = require('web.session');

ListController.include({
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        if (this.modelName === 'license.plate'){
            this._barcodeStartListening();
        }
    },

    destroy: function () {
        this._barcodeStopListening();
        this._super();
    },
    _barcodeStartListening: function(){
        core.bus.on('barcode_scanned', this, this._barcodeScanned);
    },
    _barcodeStopListening: function () {
        core.bus.off('barcode_scanned', this, this._barcodeScanned);
    },
    /**
     * @override
     * Reassign barcode listener if it is detached
     */
    reload: function (params) {
        let res = this._super.apply(this, arguments);
        if (this.modelName === 'license.plate'){
            this._barcodeStartListening();
        }
        return res;
    },
    _barcodeScanned: function (barcode) {
        if (this.modelName === 'license.plate') {
            let self = this;
            Session.rpc('/pcp_picking_barcode/scan_from_list', {
                barcode: barcode,
            }).then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning, barcode);
                }
            });
        }
    },
})

});
