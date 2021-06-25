# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.picking_id',
                 'order_line.move_ids.move_dest_ids')
    def _compute_picking(self):
        """
        Override function to get pickings from the move_dest_ids that have destination location = STOCK location
        (only apply the 2 steps that receive goods in input and the stock)
        """
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                origin_move_ids = line.move_ids
                moves = origin_move_ids | origin_move_ids.mapped('returned_move_ids')

                # PC-162: Get picking from the move_dest_ids that have destination location = STOCK location
                wfp_stock_location = self.env.ref('pcp_base.stock_location_stock_wfp')
                pcp_stock_location = self.env.ref('stock.stock_location_stock')
                move_dest_ids = origin_move_ids.mapped('move_dest_ids').filtered(lambda m: m.location_dest_id in [pcp_stock_location, wfp_stock_location])
                moves |= move_dest_ids

                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)
