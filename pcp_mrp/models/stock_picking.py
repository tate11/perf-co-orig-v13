# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    has_subcontracted_product = fields.Boolean('Has subcontracted products', compute='_compute_has_subcontracted_product')

    def _compute_has_subcontracted_product(self):
        for picking in self:
            picking.has_subcontracted_product = picking._is_subcontract()

    def button_show_subcontracting_cost_analysis(self):
        self.ensure_one()
        production_ids = self._get_subcontracted_productions()
        if production_ids:
            return self.env.ref('mrp_account_enterprise.action_cost_struct_mrp_production').report_action(production_ids, config=False)
        return True

    def action_view_subcontracting_manufacturing_order(self):
        self.ensure_one()
        production_ids = self._get_subcontracted_productions()
        action = self.env.ref('pcp_mrp.action_view_subcontracting_mrp_production')
        result = action.read()[0]

        if len(production_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (production_ids.ids)
        elif len(production_ids) == 1:
            res = self.env.ref('pcp_mrp.view_subcontracting_mrp_production_form_pcp', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = production_ids.id
        else:
            result['views'] = [(False, 'form')]
            result['target'] = 'current'
        return result

    def create_return_order_on_picking(self):
        """
        [PC-157] Create Return Order to move materials from PreProduction to Stock
        """
        return_picking_env = self.env['stock.return.picking']
        return_orders = self.env['stock.picking'].browse()
        for picking in self:
            return_wizard = return_picking_env.with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model="stock.picking",
            ).create({})
            return_wizard._onchange_picking_id()
            for return_line in return_wizard.product_return_moves:
                return_line.write({'quantity': return_line.move_id.product_qty})
            action = return_wizard.create_returns()
            return_orders |= self.browse(action.get('res_id'))

        validate_wizard = self.env['stock.immediate.transfer'].create({'pick_ids': [(6, 0, return_orders.ids)]})
        validate_wizard.process()
        return return_orders
