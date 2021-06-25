# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    material_status = fields.Selection([
        ('out_of_stock', 'Out of Stock'),
        ('ordered', 'Ordered'),
        ('needs_picked', 'Needs Picked'),
        ('available', 'Available'),
    ], string='Material Status', compute='_compute_material_status', store=True, default=False)

    @api.depends(
        "product_uom_qty",
        "reserved_availability",
        "product_id",
        "product_id.incoming_qty",
        "product_id.free_qty",
        "move_orig_ids",
        "move_orig_ids.state",
        "raw_material_production_id",
        "raw_material_production_id.source_sale_id",
        "raw_material_production_id.customer_materials",
    )
    def _compute_material_status(self):
        for move in self:
            product_id = move.product_id
            if not product_id or not move.raw_material_production_id or move.raw_material_production_id.mapped('state') in ['draft', 'done', 'cancel']:
                continue

            rounding = product_id.uom_id.rounding
            customer_materials = move.raw_material_production_id.customer_materials

            owner_id = False if customer_materials else None
            no_owner_res = product_id._compute_quantities_dict(lot_id=None, owner_id=owner_id, package_id=None)
            incoming_qty = no_owner_res[product_id.id]['incoming_qty']
            free_qty = no_owner_res[product_id.id]['free_qty']

            # Additional the quantity of product that has customer's owner_id
            source_sale_id = move.raw_material_production_id.source_sale_id
            if customer_materials and source_sale_id:
                owner_res = product_id._compute_quantities_dict(lot_id=None, owner_id=source_sale_id.partner_id.id, package_id=None)
                incoming_qty += owner_res[product_id.id]['incoming_qty']
                free_qty += owner_res[product_id.id]['free_qty']

            reserved_move = move.move_orig_ids.filtered(lambda m: m.state in ['partially_available', 'assigned'])
            if float_compare(move.reserved_availability, move.product_uom_qty, precision_rounding=move.product_uom.rounding) != -1:
                material_status = 'available'
            elif reserved_move or float_compare(free_qty, 0, precision_rounding=rounding) == 1:
                material_status = 'needs_picked'
            elif float_compare(incoming_qty, 0, precision_rounding=rounding) == 1:
                material_status = 'ordered'
            else:
                material_status = 'out_of_stock'

            move.material_status = material_status

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        ctx_owner_id = self._context.get('owner_id', False)
        if ctx_owner_id:
            owner_id = ctx_owner_id

        return super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id, lot_id, package_id, owner_id, strict)
