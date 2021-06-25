# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class RepairOrder(models.Model):
    _inherit = "repair.order"

    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA Order')