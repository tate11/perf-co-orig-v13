# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class QualityCheck(models.Model):
    _inherit = "quality.check"

    lp_number_id = fields.Many2one('license.plate')
