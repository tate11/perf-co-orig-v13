odoo.define('pcp_barcode.picking_client_action', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var PickingClientAction = require('stock_barcode.picking_client_action');

    PickingClientAction.include({

        custom_events: _.extend({}, PickingClientAction.prototype.custom_events, {
            'create_lot_name': '_onCreateLotName',
        }),

        _onCreateLotName: function (ev) {
            ev.stopPropagation();
            var self = this;
            var move_line_id = ev.data.$line.data('id');

            // Create lot name for move_line
            this._rpc({
                model: 'stock.move.line',
                method: "create_lot_name_for_move_line",
                args: [move_line_id],
                context: {},
            }).then(function (lot_name) {
                if (lot_name){
                    // Update Lot Name of move_line on PickingClientAction
                    var currentPage = self.pages[self.currentPageIndex];
                    var currentLine = _.find(currentPage.lines, function(line){
                        return line.id == move_line_id;
                    });
                    currentLine.lot_name = lot_name;

                    // Reload the line on view
                    self.linesWidget._reloadLine(ev.data.$line, currentLine);
                    self.do_notify(_t("Success"), _t("Create Lot Name successfully!"));
                }

            });
        },

        /**
         * Override
         * Write license_plate_ids to stock move line
         * */
        _applyChanges: function (changes) {
            var res = this._super.apply(this, arguments);
            var formattedCommands = [];
            var cmd = [];
            for (var i in changes) {
                var line = changes[i];
                var license_plate_ids = _.map(line.scanned_license_plates, e => e[0]);
                if (line.id) {
                    // Line needs to be updated
                    cmd = [1, line.id, {
                        'license_plate_ids': [[6, 0, license_plate_ids]],
                    }];
                    formattedCommands.push(cmd);
                }
            }
            if (formattedCommands.length > 0) {
                var params = {
                    'mode': 'write',
                    'model_name': this.actionParams.model,
                    'record_id': this.currentState.id,
                    'write_vals': formattedCommands,
                    'write_field': 'move_line_ids',
                };
                this._rpc({
                    'route': '/stock_barcode/get_set_barcode_view_state',
                    'params': params,
                });
            }
            return res;
        },

        /**
         * @Override
         * Search license plate then increase qty done of line
         * */
        _step_lot: function (barcode, linesActions) {
            var self = this;
            var _super = this._super.bind(this);

            this.currentStep = 'lot';
            var errorMessage = '';
            var license_plate = false;
            var move_line = false;
            var searchLicensePlate = function (barcode) {
                // Search from fetched data
                move_line = _.find(self.currentState.move_line_ids, function (line) {
                    license_plate = _.find(line['license_plates'], function (lp_line) {
                        return lp_line['name'] === barcode;
                    });
                    if (license_plate) {
                        var scanned_license_plate = _.find(line.scanned_license_plates, function (scanned_lp_line) {
                            return scanned_lp_line[0] === license_plate['id']
                        });
                        if (scanned_license_plate) {
                            errorMessage = _t('This license plate was scanned.');
                            return false
                        } else {
                            return true
                        }

                    } else {
                        return false;
                    }
                });

                if (move_line) {
                    return Promise.resolve(move_line);
                } else {
                    if (errorMessage) {
                        return Promise.reject(errorMessage)
                    }

                    // Try to search from server
                    var move_line_ids = _.map(self.currentState.move_line_ids, e => e['id']);
                    return self._rpc({
                        model: 'stock.move.line',
                        method: 'search_license_plate',
                        kwargs: {
                            move_line_ids: move_line_ids,
                            lp_barcode: barcode
                        }
                    }).then(function(result) {
                        if (result) {
                            move_line = _.find(self.currentState.move_line_ids, function (line) {
                                return line['id'] === result;
                            });
                            if (move_line) {
                                return Promise.resolve(move_line)
                            } else {
                                return Promise.resolve(false)
                            }
                        }
                    }, function (error) {
                        return Promise.resolve(false)
                    });
                }
            };

            return searchLicensePlate(barcode).then(function (move_line) {
                if (move_line) {
                    move_line['product_id']['qty'] = license_plate['product_qty'] - license_plate['reserved_qty'];
                    move_line['product_id']['uom_id'] = move_line['product_uom_id'];
                    move_line['product_id']['display_name'] = move_line['display_name'];
                    var res = this._incrementLines({
                        'product': move_line['product_id'],
                        'barcode': move_line['product_barcode'],
                        'lot_id': move_line['lot_id'][0],
                        'lot_name': move_line['lot_name'],
                        'owner_id': move_line['owner_id'],
                        'package_id': move_line['package_id']
                    });
                    if (!res.isNewLine) {
                        if (this.scannedLines.indexOf(res.lineDescription.id) === -1) {
                            this.scannedLines.push(res.lineDescription.id || res.lineDescription.virtual_id);
                        }
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, license_plate['product_qty'] - license_plate['reserved_qty'], this.actionParams.model]]);
                        linesActions.push([this.linesWidget.addLicensePlatetoLine, [res.id || res.virtualId, license_plate['name']]]);
                        move_line['scanned_license_plates'].push([license_plate['id'], license_plate['name']])
                        // linesActions.push([self.linesWidget.setLotName, [res.id || res.virtualId, barcode]]);
                    } else {
                        return Promise.reject(_t('Quantity done of line exceeds product quantity. Please use Inventory app to edit.'))
                    }
                    return Promise.resolve({linesActions: linesActions});
                } else {
                    return _super(barcode, linesActions);
                }
            }.bind(this));
        }
    });

    return PickingClientAction;
});