# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_order_id = fields.Many2one('rma.order', string='RMA')

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.picking_type_id and self.rma_order_id.rma_order_type == 'customer' and self.picking_type_code == 'incoming':
            if self.partner_id:
                location_id = self.partner_id.property_stock_customer.id
            else:
                location_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            self.location_id = location_id
        if self.picking_type_id and self.rma_order_id.rma_order_type == 'supplier' and self.picking_type_code == 'outgoing':
            if self.partner_id:
                location_dest_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_dest_id, = self.env['stock.warehouse']._get_partner_locations()
            self.location_dest_id = location_dest_id
        return res

    def action_done(self):
        move_obj = self.env['account.move']
        res = super(StockPicking, self).action_done()
        for rec in self:
            rma_order_id = rec.rma_order_id
            if rma_order_id and rma_order_id.rma_order_type == 'customer' and rec.picking_type_id.code == 'incoming' and rma_order_id.auto_refund:
                moves = move_obj.search([('rma_order_id', 'in', rma_order_id.sale_id.rma_order_ids.ids), ('type', '=', 'out_invoice')])
                if moves:
                    return_list = {}
                    for line in rec.move_ids_without_package:
                        product_id = line.product_id.id
                        if not return_list.get(product_id, False):
                            return_list.update({product_id: line.quantity_done})
                        else:
                            return_list[product_id] += line.quantity_done
                    rec._auto_refund_invoice_rma(moves[0], return_list)
                else:
                    raise UserError(
                        "The Sale order has no invoice to automatically create refund. Please create an invoice and try again!")
            elif rma_order_id and rma_order_id.rma_order_type == 'supplier' and rec.picking_type_id.code == 'outgoing' and rma_order_id.auto_refund:
                moves = move_obj.search([('rma_order_id', 'in', rma_order_id.purchase_id.rma_order_ids.ids), ('type', '=', 'in_invoice')])
                if moves:
                    return_list = {}
                    for line in rec.move_ids_without_package:
                        product_id = line.product_id.id
                        if not return_list.get(product_id, False):
                            return_list.update({product_id: line.quantity_done})
                        else:
                            return_list[product_id] += line.quantity_done
                    rec._auto_refund_invoice_rma(moves[0], return_list)
                else:
                    raise UserError(
                        "The Purchase order has no bill to automatically create refund. Please create a bill and try again!")
        return res

    def _auto_refund_invoice_rma(self, moves, return_list):
        reversal_obj = self.env['account.move.reversal']
        default_values_list = []
        for move in moves:
            reversal = reversal_obj.with_context(active_ids=move.ids, active_id=move.id).create({
                'refund_method': 'refund',
                'date': fields.Date.today(),
                'reason': 'RMA Refund'
            })
            values = reversal._prepare_default_reversal(move)
            values.update({
                'auto_post': False
            })
            default_values_list.append(values)
        new_moves = moves._reverse_moves(default_values_list)
        for new_move in new_moves:
            invoice_line_ids = []
            for inv_line in new_move.invoice_line_ids:
                product = inv_line.product_id
                return_qty = return_list.get(product.id, 0)
                if return_qty:
                    if return_qty > inv_line.quantity:
                        raise UserError("Return Quantity can not bigger than Invoiced quantity!")
                    else:
                        invoice_line_ids.append((0, 0, {
                            'name': product.name,
                            'product_id': product.id,
                            'quantity': return_qty,
                            'product_uom_id': product.uom_id.id,
                            'price_unit': inv_line.price_unit,
                            'tax_ids': [(6, 0, inv_line.tax_ids.ids)]
                            }))
                        return_list.update({product.id: 0})
            new_move.write({'invoice_line_ids': [(5, 0)]})
            new_move.write({'invoice_line_ids': invoice_line_ids})
        new_moves.action_post()
