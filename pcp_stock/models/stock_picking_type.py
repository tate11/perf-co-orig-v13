# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    show_lp_buttons_generating = fields.Boolean(string='Show LP Buttons (for generating)')
    show_lp_buttons_scanning = fields.Boolean(string='Show LP Buttons (for scanning')
