# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    auto_create_lot = fields.Boolean(default=True)
    type = fields.Selection(default='product')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.update_barcode()
        return res

    def update_barcode(self):
        for product_template_id in self:
            product_template_id.barcode = str(product_template_id.id).zfill(6)
