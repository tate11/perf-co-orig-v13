# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA')
