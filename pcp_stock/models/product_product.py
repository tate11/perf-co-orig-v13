# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.update_barcode()
        return res

    def update_barcode(self):
        for product_id in self:
            if product_id.product_tmpl_id:
                product_id.barcode = str(product_id.product_tmpl_id.id).zfill(6)
