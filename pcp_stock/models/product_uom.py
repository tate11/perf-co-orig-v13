# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ProductUoM(models.Model):
    _inherit = 'uom.uom'

    print_multiple_barcodes = fields.Boolean(string='Print Multiple Barcodes')
