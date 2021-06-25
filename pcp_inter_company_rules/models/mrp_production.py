# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def force_validate_subcontracting_production(self, subcontract_move_id, origin_move_id):
        # Due to multi-companies workflow, we force validate some documents in the other company
        self = self.sudo()
        #######################################################################
        self.ensure_one()
        context = dict(
            default_production_id=self.id,
            default_subcontract_move_id=subcontract_move_id.id
        )
        stock_production_lot_env = self.env['stock.production.lot'].sudo()

        for move_line in origin_move_id.move_line_ids:
            wizard = self.with_context(context).env['mrp.product.produce'].new({})
            wizard.qty_producing = move_line.qty_done
            if move_line.lot_id:
                new_lot = stock_production_lot_env.search([
                    ('name', '=', move_line.lot_id.name),
                    ('product_id', '=', move_line.product_id.id),
                    ('company_id', '=', subcontract_move_id.company_id.id)
                ], limit=1)
                if not new_lot:
                    new_lot = stock_production_lot_env.create({
                        'name': move_line.lot_id.name,
                        'product_id': move_line.product_id.id,
                        'company_id': subcontract_move_id.company_id.id
                    })
                wizard.finished_lot_id = new_lot
            wizard._onchange_qty_producing()
            wizard.do_produce()
        self.button_mark_done()
