# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class RMAOrderReason(models.Model):
    _name = 'rma.order.reason'

    name = fields.Char('Name', size=64)
    color = fields.Integer('Color Index')
