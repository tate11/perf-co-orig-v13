# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    sale_id = fields.Many2one('sale.order', 'Sale Order', compute='_compute_sale_id', store=True)
    po_number = fields.Char('Customer PO', related='sale_id.po_number', store=True, help='Customer PO Number')
    ship_via = fields.Char('Ship VIA', related='sale_id.ship_via', store=True)
    free_on_board = fields.Char('F.O.B', related='sale_id.free_on_board', store=True, help='Free On Board')

    @api.depends('invoice_origin')
    def _compute_sale_id(self):
        SaleOrder = self.env["sale.order"]
        for res in self:
            res.sale_id = SaleOrder.search([('name', '=', res.invoice_origin)], limit=1) or False
