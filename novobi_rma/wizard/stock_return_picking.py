# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA Order')

    @api.model
    def default_get(self, fields):
        res = super(StockReturnPicking, self).default_get(fields)
        record_id = self._context.get('active_id', False)
        stock_picking = self.env['stock.picking'].browse(record_id)
        if stock_picking.rma_order_id:
            res['rma_order_id'] = stock_picking.rma_order_id.id
        return res

    def _create_returns(self):
        new_picking_id, pick_type_id = super(StockReturnPicking, self)._create_returns()
        if self.rma_order_id:
            new_picking = self.env['stock.picking'].browse([new_picking_id])
            new_picking.write({'rma_order_id': self.rma_order_id.id})
        return new_picking_id, pick_type_id    
