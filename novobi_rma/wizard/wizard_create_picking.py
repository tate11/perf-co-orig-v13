# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCreatePicking(models.TransientModel):
    _name = "wizard.create.picking"

    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA')
    product_ids = fields.Many2many('product.product', 'wizard_product_rel',
        'wizard_id', 'product_id', string='Products')
    picking_type_id_number = fields.Integer("Picking type id number")
    line_ids = fields.One2many('wizard.create.picking.line', 'wizard_id', string="Lines")

    def create_picking(self):
        pickings = self.rma_order_id.sale_id.picking_ids.filtered(
            lambda x: x.picking_type_code == 'outgoing' and x.state == 'done')
        if self.rma_order_id.sale_id:
            if not pickings:
                raise UserError("This order's product(s) have not been delivered yet!")
        elif self.rma_order_id.purchase_id:
            pickings = self.rma_order_id.purchase_id.picking_ids.filtered(
                lambda x: x.picking_type_code == 'incoming' and x.state == 'done')
            if not pickings:
                raise UserError("This order's product(s) have not been received yet!")

        picking = pickings[0]
        if self.picking_type_id_number == 1 and self.rma_order_id.sale_id or self.picking_type_id_number == 2 and self.rma_order_id.purchase_id:
            location_id = picking.location_dest_id.id
            location_dest_id = picking.location_id.id
        else:
            location_id = picking.location_id.id
            location_dest_id = picking.location_dest_id.id
        new_picking = picking.copy({
            'move_lines': [],
            'picking_type_id': self.picking_type_id_number,
            'state': 'draft',
            'origin': _("%s of %s") % ('Return' if self.rma_order_id.type == 'return' else 'Exchange', self.rma_order_id.number),
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'rma_order_id':self.rma_order_id.id,
        })
        move_lines = []
        for line in self.line_ids:
            move_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': new_picking.id,
                'state': 'draft',
                'name': line.product_id.name,
                'date_expected': fields.Datetime.now(),
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                'procure_method': 'make_to_stock',
            }))
        new_picking.write({'move_lines': move_lines})
        return self.rma_order_id.action_view_picking()


class WizardCreatePickingLine(models.TransientModel):
    _name = "wizard.create.picking.line"

    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
    wizard_id = fields.Many2one('wizard.create.picking', string='Wizard')
