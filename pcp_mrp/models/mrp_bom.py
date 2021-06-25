# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class MrpBoM(models.Model):
    _inherit = 'mrp.bom'

    consumption = fields.Selection([
        ('strict', 'Strict'),
        ('flexible', 'Flexible')],
        help="Defines if you can consume more or less components than the quantity defined on the BoM.",
        default='flexible',
        string='Consumption'
    )

    @api.onchange("type")
    def onchange_bom_type(self):
        if self.type == "subcontract":
            self.routing_id = False

    @api.model
    def create(self, vals):
        res = super(MrpBoM, self).create(vals)
        res.update_route_for_components()
        return res

    def write(self, vals):
        res = super(MrpBoM, self).write(vals)
        self.update_route_for_components()
        return res

    def update_route_for_components(self):
        """
        When creating/editing the subcontracting BoM, set 'Resupply Subcontractor on Order' = True for the components
        """
        component_ids = self.filtered(lambda m: m.type == 'subcontract').mapped('bom_line_ids.product_id')
        resupply_subcontract = self.env.ref('mrp_subcontracting.route_resupply_subcontractor_mto')
        if component_ids and resupply_subcontract:
            component_ids.write({
                'route_ids': [(4, resupply_subcontract.id, None)]
            })
