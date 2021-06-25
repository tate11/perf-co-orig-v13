# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = "product.category"

    description = fields.Char('Description')
    company_id = fields.Many2one('res.company', 'Company')
