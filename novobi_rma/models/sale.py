# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    rma_order_ids = fields.One2many('rma.order', 'sale_id', readonly=True, string='RMA')
    rma_order_id = fields.Many2one('rma.order', readonly=True, string='RMA')
    rma_count = fields.Integer(string='RMA Orders', compute='_compute_rma_ids')

    def _compute_rma_ids(self):
        for rma_order in self:
            rma_order.rma_count = len(self.rma_order_ids)

    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        res['rma_order_id'] = self.rma_order_id.id
        return res

    def action_create_rma(self):
        action = self.env.ref('novobi_rma.rma_order_action_view')
        result = action.read()[0]
        form = self.env.ref('novobi_rma.rma_order_view_form_quick_create', False)
        form_id = form.id if form else False
        result['context'] = "{'rma_order_type': 'customer', 'default_partner_id': %s, 'default_sale_id': %s}" % (self.partner_id.id, self.id)
        result['views'] = [(form_id, 'form')]
        result['target'] = 'new'
        return result
    def action_view_rma(self):
        action = self.env.ref('novobi_rma.rma_order_action_view')
        result = action.read()[0]
        if not self.rma_order_ids:
            raise ValidationError("There's no rma orders related to this sale order.")
        if len(self.rma_order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (self.rma_order_ids.ids)
        elif len(self.rma_order_ids) == 1:
            res = self.env.ref('novobi_rma.rma_order_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.rma_order_ids.id
        return result