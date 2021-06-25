# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _rma_orders_count(self):
        rma_order_env = self.env['rma.order']
        for partner in self:
            partner.rma_orders_count = rma_order_env.search_count(
                ['|', ('partner_id', 'in', partner.commercial_partner_id.child_ids.ids),
                 ('partner_id', '=', partner.id)])

    rma_orders_count = fields.Integer(compute='_rma_orders_count', string='# RMAs')
