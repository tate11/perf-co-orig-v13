# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.tools import float_is_zero


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    source_sale_id = fields.Many2one('sale.order', string='Source Sales Order', copy=False)
    is_historical_data = fields.Boolean(default=False)
    sage_move_raw_ids = fields.One2many('sage.stock.move', 'raw_material_production_id', string='Sage Components')
    # TODO: Store picking info
    picking_ids = fields.Many2many(store=False, compute_sudo=True)
    delivery_count = fields.Integer(store=False, compute_sudo=True)
    is_change_date = fields.Boolean(compute='_compute_is_change_date')

    # Additional Information of the finished good
    unit_upc_code = fields.Char("Unit UPC", copy=False)
    case_upc_code = fields.Char("Case UPC", copy=False)
    best_by_date = fields.Date("Best By", copy=False)
    case_lot = fields.Char("Case Lot", copy=False)
    ti_pallet_size = fields.Integer("TI Pallet", copy=False)
    hi_pallet_size = fields.Integer("HI Pallet", copy=False)
    case_count_per_pallet = fields.Integer("Per Pallet Case Count", compute='_compute_case_count_per_pallet', store=True)
    total_pallets = fields.Float("Total Pallets", compute='_compute_total_pallets', store=True, digits="Product Unit of Measure")
    unit_count_per_case = fields.Integer("Case Count", copy=False)
    weight_ounce = fields.Float("Unit Weight", copy=False, digits="Stock Weight",)
    weight_gram = fields.Float("Grams", compute='_compute_weight_gram', store=True, digits="Stock Weight")

    def _compute_is_change_date(self):
        is_change_date = False
        if self.env.user.has_group('pcp_security.can_change_date_on_mo_wo'):
            is_change_date = True
        for rec in self:
            rec.is_change_date = is_change_date

    @api.depends("ti_pallet_size", "hi_pallet_size")
    def _compute_case_count_per_pallet(self):
        for rec in self:
            rec.case_count_per_pallet = rec.ti_pallet_size * rec.hi_pallet_size

    @api.depends("weight_ounce")
    def _compute_weight_gram(self):
        for rec in self:
            rec.weight_gram = rec.weight_ounce * 28.35

    @api.depends("case_count_per_pallet", "product_qty")
    def _compute_total_pallets(self):
        for rec in self:
            if float_is_zero(rec.case_count_per_pallet, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')):
                rec.total_pallets = 0
            else:
                rec.total_pallets = rec.product_qty / rec.case_count_per_pallet

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product_id = self.product_id
        if product_id:
            self.unit_upc_code = product_id.unit_upc_code
            self.case_upc_code = product_id.case_upc_code
            self.best_by_date = product_id.best_by_date
            self.case_lot = product_id.case_lot
            self.unit_count_per_case = product_id.unit_count_per_case
            self.ti_pallet_size = product_id.ti_pallet_size
            self.hi_pallet_size = product_id.hi_pallet_size
            self.weight_ounce = product_id.weight_ounce
        else:
            self.unit_upc_code = False
            self.case_upc_code = False
            self.best_by_date = False
            self.case_lot = False
            self.unit_count_per_case = False
            self.ti_pallet_size = False
            self.hi_pallet_size = False
            self.weight_ounce = False

    @api.model
    def create(self, values):
        if 'origin' in values:
            sale_order = self.env['sale.order'].search([('name', '=', values['origin'])])
            values['source_sale_id'] = sale_order.id or False

        return super(MrpProduction, self).create(values)

    def action_view_so(self):
        self.ensure_one()
        return {
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.source_sale_id.id
        }

    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()

        # PC-157: Create Return Order when cancelling Manufacturing Order
        pcp_warehouse = self.env.ref('stock.warehouse0')
        for production in self:
            stock_location = self.env.ref('pcp_base.stock_location_stock_wfp')
            if production.picking_type_id.warehouse_id == pcp_warehouse:
                stock_location = self.env.ref('stock.stock_location_stock')

            picking_ids = production.picking_ids.filtered(lambda x: x.state == 'done' and x.location_id.id == stock_location.id)
            picking_ids.create_return_order_on_picking()

        return res
