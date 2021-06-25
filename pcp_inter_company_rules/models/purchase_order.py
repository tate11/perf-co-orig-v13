# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    inter_company_sale_order_id = fields.Many2one(
        'sale.order', string='Created Sale Order', readonly=True, copy=False,
        help='Origin Sale Order on Inter Company')
    auto_sale_order_id = fields.Many2one(
        'sale.order', string='Created by Sale Order',
        help='Destination Sale Order on Inter Company')
    delivery_picking_ids = fields.One2many('stock.picking', 'purchase_order_for_delivery',
                                           string='Delivery Materials', store=True, copy=False,
                                           compute='_compute_delivery_picking_ids')
    delivery_picking_count = fields.Integer(string='Delivery Materials Count', default=0, store=True, copy=False,
                                            compute='_compute_delivery_picking_ids')

    @api.depends('picking_ids')
    def _compute_delivery_picking_ids(self):
        stock_picking_env = self.env["stock.picking"]
        input_location = self.env.ref("pcp_base.stock_location_input_wfp")
        delivery_picking_type_wfp = self.env.ref("pcp_base.stock_picking_type_delivery_wfp")
        for order in self:
            receipt_orders = order.picking_ids.filtered(lambda p: p.location_dest_id.id == input_location.id)
            delivery_orders = stock_picking_env.search([
                ('origin', 'in', receipt_orders.mapped('name')),
                ('picking_type_id', '=', delivery_picking_type_wfp.id)
            ])
            order.write({
                'delivery_picking_ids': [(6, 0, delivery_orders.ids)],
                'delivery_picking_count': len(delivery_orders.ids)
            })

    def inter_company_create_sale_order(self, company):
        """
            Override function to write inter_company_sale_order_id field on SO.

            Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide at least one user for inter company relation for % ') % company.name)
        # check intercompany user access rights
        if not SaleOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        for rec in self:
            # check pricelist currency should be same with SO/PO document
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            if rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                raise Warning(
                    _('You cannot create SO from PO because sale price list currency is different than purchase price list currency.')
                    + '\n'
                    + _('The currency of the SO is obtained from the pricelist of the company partner.')
                    + '\n\n ({} {}, {} {}, {} {} (ID: {}))'.format(
                        _('SO currency:'), company_partner.property_product_pricelist.currency_id.name,
                        _('Pricelist:'), company_partner.property_product_pricelist.display_name,
                        _('Partner:'), company_partner.display_name, company_partner.id,
                    )
                )

            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            sale_order_data = rec.sudo()._prepare_sale_order_data(
                rec.name, company_partner, company,
                rec.dest_address_id and rec.dest_address_id.id or False)
            inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
            sale_order = SaleOrder.with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(intercompany_uid).create(sale_order_data)
            # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
            for line in rec.order_line.sudo():
                so_line_vals = rec._prepare_sale_order_line_data(line, company, sale_order.id)
                # TODO: create can be done in batch; this may be a performance bottleneck
                SaleOrderLine.with_user(intercompany_uid).with_context(allowed_company_ids=inter_user.company_ids.ids).create(so_line_vals)

            # PC-186: Write inter_company_sale_order_id field on SO
            rec.inter_company_sale_order_id = sale_order

            # write vendor reference field on PO
            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            # Validation of sales order
            if company.auto_validation:
                sale_order.with_user(intercompany_uid).action_confirm()

    def check_create_inter_company_sale_order(self):
        self.ensure_one()
        # get the company from partner then trigger action of intercompany relation
        company_rec = self.env['res.company']._find_company_from_partner(self.partner_id.id)
        is_create_sale_order = False
        if company_rec and company_rec.applicable_on in ('purchase', 'sale_purchase') and (not self.auto_generated):
            is_create_sale_order = True

        return is_create_sale_order

    def _create_picking(self):
        """
        Unreserve the picking when the picking created from PO that will create a new Inter company Sale Order
        """
        res = super(PurchaseOrder, self)._create_picking()
        for order in self.sudo().filtered(lambda o: o.check_create_inter_company_sale_order() or o.get_inter_company_sale_order()):
            reserved_transfer = order.picking_ids.filtered(lambda p: p.state == 'assigned' and p.picking_type_code == 'incoming')
            if reserved_transfer:
                reserved_transfer.mapped('move_lines.move_line_ids').unlink()
        return res

    def get_inter_company_sale_order(self):
        self.ensure_one()
        return self.inter_company_sale_order_id or self.auto_sale_order_id or False

    def action_view_delivery_materials(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        pick_ids = self.mapped('delivery_picking_ids')

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
