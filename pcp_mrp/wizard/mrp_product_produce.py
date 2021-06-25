# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def action_generate_serial(self):
        """
        Override to add name when generating lot.
        """
        self.ensure_one()
        product_produce_wiz = self.env.ref('mrp.view_mrp_product_produce_wizard', False)
        lot_name = self.env['stock.production.lot'].with_context(create_finished_product_lot=True).generate_lot_name()
        self.finished_lot_id = self.env['stock.production.lot'].create({
            'name': lot_name,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
        })
        return {
            'name': _('Produce'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mrp.product.produce',
            'res_id': self.id,
            'view_id': product_produce_wiz.id,
            'target': 'new',
        }