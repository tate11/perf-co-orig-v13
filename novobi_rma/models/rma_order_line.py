# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class RMAOrderLine(models.Model):
    _name = "rma.order.line"
    _description = "List of product to return"

    name = fields.Char(string='Description', required=True, default=None)
    rma_order_id = fields.Many2one('rma.order', readonly=True, string='Related RMA', help="To link to the RMA object")
    rma_order_origin = fields.Selection([('none', 'Not specified'),
                                         ('legal', 'Legal retractation'),
                                         ('cancellation', 'Order cancellation'),
                                         ('damaged', 'Damaged delivered product'),
                                         ('error', 'Shipping error'),
                                         ('exchange', 'Exchange request'),
                                         ('lost', 'Lost during transport'),
                                         ('other', 'Other'),
                                         ('warranty', 'Warranty')], string='RMA Subject', required=True, default='none',
                                        help="To describe the line product problem")
    refund_line_id = fields.Many2one('account.move.line', string='Refund Line',
                                     help='The refund line related to the returned product')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line',
                                      help='The invoice line related to the returned product')
    product_id = fields.Many2one('product.product', string='Product', help="Returned product")
    product_returned_quantity = fields.Float(string='Quantity', digits=(12, 2), help="Quantity of product returned")
    unit_sale_price = fields.Float(string='Unit sale price', digits=(12, 2),
                                   help="Unit sale price of the product. Auto filed if retrun done by invoice selection. BE CAREFUL AND CHECK the automatic value as don't take into account previous refounds, invoice discount, can be for 0 if product for free,...")
    product_uom_id = fields.Many2one('uom.uom', string='UoM', required=True)
    state = fields.Selection([('draft', 'No Refund'),
                              ('refund', 'Refund'),
                              ('refund_restock', 'Refund with restocking fee')], string='State', default='draft')
    prodlot_id = fields.Many2one('stock.production.lot', string='Serial/Lot n', help="The serial/lot of the returned product")
    warning = fields.Char(string='Warranty', readonly=True, help="If warranty has expired")
    on_invoice = fields.Boolean(string="On Invoice", readonly=True, help="Product form Invoice")
