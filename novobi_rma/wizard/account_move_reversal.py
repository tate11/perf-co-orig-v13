# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA')

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        record_id = self._context.get('active_id', False)
        move = self.env['account.move'].browse(record_id)
        if move.rma_order_id:
            res['rma_order_id'] = move.rma_order_id.id
        return res

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        if move.rma_order_id:
            res['rma_order_id'] = move.rma_order_id.id
        return res
