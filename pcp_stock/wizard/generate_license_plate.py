# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError


class GenerateLicensePlate(models.TransientModel):
    _name = 'generate.license.plate'
    _description = 'Generate License Plate'

    number_of_lp = fields.Integer(
        "No. License Plate",
        required=True,
        default=1
    )
    lot_id = fields.Many2one(
        'stock.production.lot',
        'Lot/Serial Number',
        required=True,
    )
    type = fields.Selection(
        [("incoming", "Incoming"), ("production", "Production")],
        string="Type",
        default="incoming",
        required=True,
    )
    product_id = fields.Many2one('product.product', related='lot_id.product_id')
    product_qty = fields.Float('Quantity per LP', digits="Product Unit of Measure")
    qty_done = fields.Float('Qty Done of Stock Move Line', digits="Product Unit of Measure")
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='lot_id.product_uom_id', readonly=True, store=True)

    @api.onchange('number_of_lp')
    def onchange_number_of_lp(self):
        number_of_lp, qty_done = self.number_of_lp, self.qty_done
        if number_of_lp not in (0, 1) and qty_done:
            self.product_qty = qty_done // number_of_lp

    @api.onchange('product_qty', 'qty_done')
    def onchange_product_qty(self):
        product_qty, qty_done = self.product_qty, self.qty_done
        if product_qty and qty_done:
            total_product_qty = product_qty * self.number_of_lp
            rounding = self.product_uom_id.rounding
            if float_compare(qty_done, total_product_qty, precision_rounding=rounding) != 0:
                return {
                    "warning": {
                        "title": "Warning",
                        "message":
                            """The Total Quantity of License Plates doesn't not equal to the Done Quantity in the picking.
You may need to adjust the quantity per License Plate after generating if needed.
                            """
                    },
                }

    def _get_lot(self):
        self.ensure_one()
        lot_id = self.lot_id
        existing_lp = self.env['license.plate'].search([('lot_id', '=', lot_id.id)], limit=1)
        if existing_lp:
            raise ValidationError("Please remove all LP of (LOT: %s, Company: %s) before generating the new one" % (lot_id.name, lot_id.company_id.name))
        return lot_id

    def _get_lp_sequence(self):
        self.ensure_one()
        if self.type == 'production':
            lp_name = self.env['ir.sequence'].next_by_code('lp.production.serial')
        else:
            lp_name = self.env['ir.sequence'].next_by_code('lp.incoming.serial')
        return lp_name

    def generate(self):
        self.ensure_one()
        lot_id = self._get_lot()
        number_of_lp = self.number_of_lp
        action = self.env.ref('pcp_stock.license_plate_action').read()[0]
        if number_of_lp and lot_id:
            lp_numbers = self.env['license.plate'].create([{
                'name': self._get_lp_sequence(),
                'lot_id': lot_id.id,
                'product_qty': self.product_qty,
                'type': self.type
            } for lp_number in range(0, number_of_lp)
            ])
            action['domain'] = [('id', 'in', lp_numbers.ids)]
        return action
