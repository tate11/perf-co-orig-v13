# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    subcontracting_origin_move = fields.Many2one('stock.move')
