# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_fully_reserved = fields.Boolean('Is fully reserved material', compute='_compute_is_fully_reserved')
    customer_materials = fields.Boolean(string='Receive Customer Materials', compute='_compute_customer_materials')

    @api.depends('picking_ids', 'picking_ids.customer_materials')
    def _compute_customer_materials(self):
        for order in self:
            pickings = order.picking_ids.filtered(lambda p: not p.customer_materials)
            customer_materials = True
            if not order.picking_ids or pickings:
                customer_materials = False
            order.customer_materials = customer_materials

    @api.depends('move_raw_ids', 'move_raw_ids.material_status')
    def _compute_is_fully_reserved(self):
        for rec in self:
            not_fully_reserved_moves = rec.move_raw_ids.filtered(lambda m: m.material_status != 'available')
            is_fully_reserved = True
            if not_fully_reserved_moves:
                is_fully_reserved = False
            rec.is_fully_reserved = is_fully_reserved
