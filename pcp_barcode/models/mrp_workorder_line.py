# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpWorkorderLine(models.Model):
    _inherit = 'mrp.workorder.line'

    lp_line_id = fields.Many2one('license.plate.line')