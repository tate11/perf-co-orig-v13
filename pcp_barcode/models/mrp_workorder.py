# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import float_compare, float_round


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    lp_number_id = fields.Many2one('license.plate', related='current_quality_check_id.lp_number_id', readonly=False)

    @api.onchange('lp_number_id')
    def on_change_lp(self):
        """
        This function allows the user change the LP# to adjust the quantity done on workorder
        """
        qty_done = self.qty_done
        if self.lp_number_id:
            qty_done = min(self.lp_number_id.product_qty - self.lp_number_id.reserved_qty, self.component_remaining_qty)
        self.qty_done = qty_done

    def _next(self, continue_production=False):
        self.ensure_one()
        old_workorder_line_id = self.workorder_line_id
        lp_line_id =  self.env["license.plate.line"].update_license_plate_line_with_workorder(workorder=self)
        result = super(MrpWorkorder, self)._next(continue_production=continue_production)
        if old_workorder_line_id:
            old_workorder_line_id.write({'lp_line_id': lp_line_id and lp_line_id.id or False})
        return result

    def on_barcode_scanned(self, barcode):
        # qty_done field for serial numbers is fixed
        if self.component_tracking != 'serial':
            lot = self.lot_id
            if not lot:
                # not scanned yet
                self.qty_done = 0
            else:
                license_plate = self.env['license.plate'].search([
                    ('name', '=', barcode),
                    ('lot_id', '=', lot.id),
                ], limit=1)
                if license_plate:
                    self.lp_number_id = license_plate
                else:
                    return {
                        'warning': {
                            'title': _("Warning"),
                            'message': _("You are using components from another lot. \nPlease validate the components from the first lot before using another lot.")
                        }
                    }

        # lot = self.env['stock.production.lot'].search([('name', '=', barcode)])

        # Don't allow user create new LOT/SN
        # if self.component_tracking:
        #     if not lot:
        #         # create a new lot
        #         # create in an onchange is necessary here ("new" cannot work here)
        #         lot = self.env['stock.production.lot'].with_context(active_mo_id=self.production_id.id).create({
        #             'name': barcode,
        #             'product_id': self.component_id.id,
        #             'company_id': self.company_id.id,
        #         })
        #     self.lot_id = lot
        # elif self.production_id.product_id.tracking and self.production_id.product_id.tracking != 'none':
        #     if not lot:
        #         lot = self.env['stock.production.lot'].create({
        #             'name': barcode,
        #             'product_id': self.product_id.id,
        #             'company_id': self.company_id.id,
        #         })
        #     self.finished_lot_id = lot
