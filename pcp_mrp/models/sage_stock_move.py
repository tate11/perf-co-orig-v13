# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class SageStockMove(models.Model):
    _name = 'sage.stock.move'

    product_id = fields.Many2one( 'product.product', 'Product')
    product_uom_qty = fields.Float(  'To Consume', digits=0)
    quantity_done = fields.Float('Consumed', digits=0)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    needs_lots = fields.Boolean('Tracking', compute='_compute_needs_lots')
    raw_material_production_id = fields.Many2one('mrp.production', 'Production Order for components')

    def _compute_needs_lots(self):
        for move in self:
            move.needs_lots = move.product_id.tracking != 'none'
