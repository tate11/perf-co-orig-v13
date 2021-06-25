odoo.define('_picking_barcode.FormController', function (require) {
    "use strict";

    const FormController = require('web.FormController');
    require('barcodes.FormView');  // Wait for parent to complete

    FormController.include({
        init: function() {
            let controllers = arguments[0].controllers;
            // Store list of controllers for list views currently assigned for detach barcode listeners
            this.listControllers = _.chain(controllers)
                .filter(c => c.viewType === 'list' && c.widget)
                .map(c => c.widget).value();
            this._super.apply(this, arguments);
        },
        _barcodeStartListening: function () {
            this._super.apply(this, arguments);
            // Deactivate all other list view barcode scanning listeners
            _.each(this.listControllers, w => w._barcodeStopListening());
        },
        /**
         * @override
         * Reassign barcode listener if it is detached
         */
        reload: function (params) {
            let res = this._super.apply(this, arguments);
            // Deactivate all other list view barcode scanning listeners
            _.each(this.listControllers, w => w._barcodeStopListening());
            return res;
        },
    });

    return FormController;
});
