# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class MrpBoMLine(models.Model):
    _inherit = 'mrp.bom.line'

    comment = fields.Char(string="Notes")
