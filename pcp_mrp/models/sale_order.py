# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mo_ids = fields.One2many('mrp.production', 'source_sale_id', string='Manufacturing Orders')
    mo_count = fields.Integer('Number of linked Manufacturing Orders', compute='_compute_mo_count')

    def action_view_mo(self):
        self.ensure_one()
        return {
            'name': _('Manufacturing Orders'),
            'domain': [('id', 'in', self.mo_ids.ids)],
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form'
        }

    @api.depends('mo_ids')
    def _compute_mo_count(self):
        for record in self:
            record.mo_count = len(record.mo_ids.ids)
