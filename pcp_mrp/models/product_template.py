# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unit_upc_code = fields.Char("Unit UPC", copy=False)
    case_upc_code = fields.Char("Case UPC", copy=False)
    best_by_date = fields.Date("Best By", copy=False)
    case_lot = fields.Char("Case Lot", copy=False)
    ti_pallet_size = fields.Integer("TI Pallet", copy=False)
    hi_pallet_size = fields.Integer("HI Pallet", copy=False)
    case_count_per_pallet = fields.Integer("Per Pallet Case Count", compute='_compute_case_count_per_pallet', store=True)
    unit_count_per_case = fields.Integer("Case Count", copy=False)
    weight_ounce = fields.Float("Unit Weight", copy=False, digits="Stock Weight",)
    weight_gram = fields.Float("Grams", compute='_compute_weight_gram', store=True, digits="Stock Weight")

    @api.depends("ti_pallet_size", "hi_pallet_size")
    def _compute_case_count_per_pallet(self):
        for rec in self:
            rec.case_count_per_pallet = rec.ti_pallet_size * rec.hi_pallet_size

    @api.depends("weight_ounce")
    def _compute_weight_gram(self):
        for rec in self:
            rec.weight_gram = rec.weight_ounce * 28.35
