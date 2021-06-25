# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockBarcodeLot(models.TransientModel):
    _inherit = 'stock_barcode.lot'

    def on_barcode_scanned(self, barcode):
        """
        Override to increase qty done when scanning license plate
        """
        license_plate = self.env['license.plate'].search([('name', '=', barcode)], limit=1)

        suitable_lines = self.stock_barcode_lot_line_ids.filtered(lambda x: x.lot_name == license_plate.lot_id.name)
        if suitable_lines:
            for line in suitable_lines:
                if self.product_id.tracking == 'serial':
                    raise UserError(_('You cannot scan two times the same serial number'))
                if license_plate.id in line.license_plate_ids.ids:
                    raise UserError(_('You cannot scan a license plate for one lot twice'))
                line.write({
                    'qty_done': line.qty_done + (license_plate.product_qty - license_plate.reserved_qty),
                    'license_plate_ids': [(4, license_plate.id, False)]
                })

        else:
            super(StockBarcodeLot, self).on_barcode_scanned(barcode)

    def get_lot_or_create(self, barcode):
        """
        Override
        Fix: Return lot of current company
        """
        res = super(StockBarcodeLot, self).get_lot_or_create(barcode)

        if len(res) > 1:
            return res.filtered(lambda e: e.company_id == self.env.company)
        else:
            return res

class StockBarcodeLotLine(models.TransientModel):
    _inherit = "stock_barcode.lot.line"

    license_plate_ids = fields.Many2many(related='move_line_id.license_plate_ids', readonly=False)
