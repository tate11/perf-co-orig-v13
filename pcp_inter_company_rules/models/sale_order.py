# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    inter_company_purchase_order_id = fields.Many2one(
        'purchase.order', string='Created Purchase Order', readonly=True, copy=False,
        help='Origin Purchase Order on Inter Company')
    auto_purchase_order_id = fields.Many2one(
        'purchase.order', string='Created by Purchase Order',
        help='Destination Purchase Order on Inter Company')
    receipt_picking_ids = fields.Many2many('stock.picking', 'sale_order_receipt_materials_rel', 'order_id', 'receipt_id',
                                           string='Receipt Materials', copy=False, )
    receipt_picking_count = fields.Integer(string='Receipt Materials Count', default=0, store=True, copy=False,
                                           compute='_compute_receipt_picking_count')

    @api.depends('receipt_picking_ids')
    def _compute_receipt_picking_count(self):
        for order in self:
            order.receipt_picking_count = len(order.receipt_picking_ids.ids)

    def inter_company_create_purchase_order(self, company):
        """
            Override function to write inter_company_purchase_order_id field on SO.

            Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo, and the creation of the derived
            PO as intercompany_user, minimizing the access right required for the trigger user
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id, company_id=company.id)
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for rec in self:
            if not company or not rec.company_id.partner_id:
                continue

            # find user for creating and validating SO/PO from company
            intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
            if not intercompany_uid:
                raise Warning(_('Provide one user for intercompany relation for % ') % company.name)
            # check intercompany user access rights
            if not PurchaseOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
                raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            # create the PO and generate its lines from the SO
            # read it as sudo, because inter-compagny user can not have the access right on PO
            po_vals = rec.sudo()._prepare_purchase_order_data(company, company_partner)
            inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
            purchase_order = PurchaseOrder.with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(intercompany_uid).create(po_vals)
            for line in rec.order_line.sudo():
                po_line_vals = rec._prepare_purchase_order_line_data(line, rec.date_order,
                    purchase_order.id, company)
                # TODO: create can be done in batch; this may be a performance bottleneck
                PurchaseOrderLine.with_user(intercompany_uid).with_context(allowed_company_ids=inter_user.company_ids.ids).create(po_line_vals)

            # PC-186: Write inter_company_purchase_order_id field on SO
            rec.inter_company_purchase_order_id = purchase_order

            # write customer reference field on SO
            if not rec.client_order_ref:
                rec.client_order_ref = purchase_order.name

            # auto-validate the purchase order if needed
            if company.auto_validation:
                purchase_order.with_user(intercompany_uid).button_confirm()

    def check_fully_shipping_products(self):
        self.ensure_one()
        is_fully_shipping_products = True
        if self.state in ['draft', 'sent'] or self.picking_ids.filtered(lambda m: m.picking_type_code == 'outgoing' and m.state not in ['done', 'cancel']):
            is_fully_shipping_products = False

        return is_fully_shipping_products

    def get_inter_company_purchase_order(self):
        self.ensure_one()
        return self.inter_company_purchase_order_id or self.auto_purchase_order_id or False

    def action_view_receipt_materials(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        pick_ids = self.mapped('receipt_picking_ids')

        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result

    def action_cancel(self):
        """
        When canceling the Sale Order, "Receipt Materials" should be canceled if it is not done
        """
        res = super(SaleOrder, self).action_cancel()
        receipts_material = self.mapped('receipt_picking_ids').filtered(lambda p: p.state != 'done')
        receipts_material.action_cancel()
        return res
