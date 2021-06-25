# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare

class RMAOrder(models.Model):
    """RMA Order"""
    _name = "rma.order"
    _description = "RMA Order"
    _order = "priority,date desc"
    _inherit = ['mail.thread']

    def _get_default_warehouse(self):
        company_id = self.env.company.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise Warning(
                _('There is no warehouse for the current user\'s company.'))
        return wh

    name = fields.Char(string='Subject', required=True)
    active = fields.Boolean(default=True)
    action_next = fields.Char('Next Action')
    date_action_next = fields.Datetime('Next Action Date', default=lambda self: fields.datetime.now() + relativedelta(days=14))
    description = fields.Text('Description')
    create_date = fields.Datetime('Creation Date', readonly=True)
    write_date = fields.Datetime('Update Date', readonly=True)
    date_deadline = fields.Date('Deadline', default=lambda self: fields.date.today() + relativedelta(days=14))
    date_closed = fields.Datetime('Closed Date', readonly=True)
    date = fields.Datetime('Date Created', index=True, default=lambda self: fields.datetime.now())
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always', default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', 'Sales Team',
                              index=True, help="Responsible sales team.",
                              default=lambda self: self.env['crm.team']._get_default_team_id(self.env.uid))
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    partner_id = fields.Many2one('res.partner', 'Partner')
    email_from = fields.Char('Email', size=128, help="Partner Email")
    partner_phone = fields.Char('Phone')
    number = fields.Char(string='Number', default=lambda self: _('New'))
    reason_code = fields.Many2many('rma.order.reason', 'rma_order_reason_rel', 'rma_id', 'reason_id', string='Reason Code')
    sale_id = fields.Many2one('sale.order', string='Sale Order', help='Related Sales')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', help='Related Purchase')
    type = fields.Selection([
        ('return', 'Return'),
        ('exchange', 'Exchange')]
        , default='return', string='Type', required=True)
    rma_order_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier')],
        string='Partner Type', required=True, default='customer',
        help="customer = from customer to company ; supplier = from company to supplier")
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')], default='1')
    state = fields.Selection(type="selection", store=True, string="Status",
                             selection=[
                                 ('draft', 'New'),
                                 ('open', 'In Progress'),
                                 ('return', 'Waiting for Return'),
                                 ('delivery', 'Waiting for Delivery'),
                                 ('repair', 'Waiting for Repair'),
                                 ('payment', 'Waiting for Payment'),
                                 ('cancel', 'Rejected'),
                                 ('done', 'Settled')
                             ], default='draft',required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', help='Related original Customer invoice')
    rma_order_line_ids = fields.One2many('rma.order.line', 'rma_order_id', string='Return lines')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=_get_default_warehouse, required=True)

    sale_count = fields.Integer(string='Sale Orders', compute='_compute_sale_ids')
    purchase_count = fields.Integer(string='Purchase Orders', compute='_compute_purchase_ids')

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_ids')
    refund_count = fields.Integer(string='Invoices', compute='_compute_refund_ids')
    vendor_refund_count = fields.Integer(string='Vendor Refund Count', compute='_compute_vendor_refund_ids')
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_compute_vendor_bill_ids')
    return_count = fields.Integer(string="Returns(s)", compute='_compute_return_ids')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_delivery_order_ids')
    repair_count = fields.Integer(string='Repair Orders', compute='_compute_repair_ids')
    verify_return_product = fields.Boolean(string="Verify return product", compute='_compute_verify_return')
    auto_refund = fields.Boolean(string="Auto Refund Invoicing")

    def _compute_verify_return(self):
        for rec in self:
            line_dict = {}
            verify_return_product = True
            if rec.sale_id:
                current_order = rec.sale_id
            else:
                current_order = rec.purchase_id
            for line in current_order.order_line:
                line_dict.update({line.product_id.id: line.product_uom_qty})
            picking_ids = self.env['stock.picking'].search([
                ('rma_order_id', '=', rec.id),
                ('location_id', '=', rec.partner_id.property_stock_customer.id) if rec.sale_id else('location_dest_id','=', rec.partner_id.property_stock_supplier.id)])
            for line in picking_ids.mapped('move_ids_without_package'):
                product_id = line.product_id.id
                if product_id in line_dict:
                    if float_compare(line.product_uom_qty, line_dict.get(product_id, 0), precision_rounding=line.product_id.uom_id.rounding)>0:
                        verify_return_product = False
                        break
                else:
                    verify_return_product = False
                    break
            rec.verify_return_product = verify_return_product

    def _compute_return_ids(self):
        picking_obj = self.env['stock.picking']
        for rma_order in self:
            if rma_order.rma_order_type == 'customer':
                location_id = rma_order.partner_id.property_stock_customer.id
            else:
                location_id = rma_order.partner_id.property_stock_supplier.id
            rma_order.return_count = picking_obj.search_count([('rma_order_id', '=', rma_order.id), ('location_id', '=', location_id)])

    def _compute_repair_ids(self):
        repair_obj = self.env['repair.order']
        for rma_order in self:
            rma_order.repair_count = repair_obj.search_count([('rma_order_id', '=', rma_order.id)])

    def _compute_delivery_order_ids(self):
        picking_obj = self.env['stock.picking']
        for rma_order in self:
            if rma_order.rma_order_type == 'customer':
                location_dest_id = rma_order.partner_id.property_stock_customer.id
            else:
                location_dest_id = rma_order.partner_id.property_stock_supplier.id
            rma_order.delivery_count = picking_obj.search_count([('rma_order_id', '=', rma_order.id), ('location_dest_id', '=', location_dest_id)])
        
    def _compute_refund_ids(self):
        inv_obj = self.env['account.move']
        for rma_order in self:
            rma_order.refund_count = inv_obj.search_count([('rma_order_id', 'in', rma_order.sale_id.rma_order_ids.ids), ('type', '=', 'out_refund')])
            
    def _compute_vendor_refund_ids(self):
        inv_obj = self.env['account.move']
        for rma_order in self:
            rma_order.vendor_refund_count = inv_obj.search_count([('rma_order_id', 'in', rma_order.purchase_id.rma_order_ids.ids), ('type', '=', 'in_refund')])
            
    def _compute_invoice_ids(self):
        for rma_order in self:
             rma_order.invoice_count = self.env['account.move'].search_count(
                [('rma_order_id', 'in', self.sale_id.rma_order_ids.ids), ('type', '=', 'out_invoice')])

    def _compute_vendor_bill_ids(self):
        for rma_order in self:
            rma_order.vendor_bill_count = self.env['account.move'].search_count(
                [('rma_order_id', 'in', self.purchase_id.rma_order_ids.ids), ('type', '=', 'in_invoice')])

    @api.onchange('rma_order_type')
    def onchange_rma_order_type(self):
        if not self._context.get('default_sale_id'):
            self.sale_id = False
        if not self._context.get('default_purchase_id'):
            self.purchase_id = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner = self.partner_id
        self.email_from = partner.email
        self.partner_phone = partner.phone
        if not self._context.get('default_sale_id'):
            self.sale_id = False
        if not self._context.get('default_purchase_id'):
            self.purchase_id = False
        if partner.team_id:
            self.team_id = partner.team_id.id
        else:
            self.team_id = self.env['crm.team']._get_default_team_id(self.env.uid)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.number + ' - ' + record.name + ' ' + dict(record.fields_get(allfields=['state'])['state']['selection'])[record.state]))
        return result

    @api.onchange('type')
    def _onchange_type(self):
        auto_refund = False
        name = 'Exchange'
        if self.type == 'return':
            auto_refund = True
            name = 'Return'
        self.auto_refund = auto_refund
        if self.sale_id:
            self.name = _("""%s %s""") % (self.sale_id.name, name)
        elif self.purchase_id:
            self.name = _("""%s %s""") % (self.purchase_id.name, name)

    @api.model
    def create(self, vals):
        if vals.get('team_id') and not self._context.get('default_team_id'):
            self = self.with_context(default_team_id=vals.get('team_id'))
        if vals.get('number', _('New')) == _('New'):
            vals['number'] = self.env['ir.sequence'].next_by_code('rma.order') or _('New')
        res = super(RMAOrder, self).create(vals)
        if vals.get('sale_id'):
            sale = self.env['sale.order'].browse(vals.get('sale_id'))
            sale.write({'rma_order_id': res.id})
            sale.invoice_ids.write({'rma_order_id': res.id})
        if vals.get('purchase_id'):
            purchase = self.env['purchase.order'].browse(vals.get('purchase_id'))
            purchase.write({'rma_order_id': res.id})
            purchase.invoice_ids.write({'rma_order_id': res.id})
        return res

    def write(self, vals):
        if 'state' in vals:
            if self.state == 'done':
                vals.update({'date_closed':fields.datetime.now()})
        if 'sale_id' in vals:
            if vals.get('sale_id'):
                sale = self.env['sale.order'].browse(vals.get('sale_id'))
                sale.write({'rma_order_id': self.id})
                sale.invoice_ids.write({'rma_order_id': self.id})
            else:
                sale = self.env['sale.order'].search([('rma_order_id', '=', self.id)])
                sale.write({'rma_order_id': False})
                sale.invoice_ids.write({'rma_order_id': False})
        if 'purchase_id' in vals:
            if vals.get('purchase_id'):
                purchase = self.env['purchase.order'].browse(vals.get('purchase_id'))
                purchase.write({'rma_order_id': self.id})
                purchase.invoice_ids.write({'rma_order_id': self.id})
            else:
                purchase = self.env['purchase.order'].search([('rma_order_id', '=', self.id)])
                purchase.write({'rma_order_id': False})
                purchase.invoice_ids.write({'rma_order_id': False})
        return super(RMAOrder, self).write(vals)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_('%s (copy)') % self.name)
        default['number'] = self.env['ir.sequence'].next_by_code('rma.order') or _('New')
        return super(RMAOrder, self).copy(default)

    def pass_create_rma(self):
        action = self.env.ref('novobi_rma.rma_order_action_view')
        result = action.read()[0]
        result['views'] = [(False, 'form')]
        result['res_id'] = self.id
        return result

    def action_view_sale(self):
        action = self.env.ref('sale.action_orders')
        result = action.read()[0]
        form = self.env.ref('sale.view_order_form', False)
        form_id = form.id if form else False
        result['views'] = [(form_id, 'form')]
        result['res_id'] = self.sale_id.id
        return result

    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq')
        result = action.read()[0]
        form = self.env.ref('purchase.purchase_order_form', False)
        form_id = form.id if form else False
        result['views'] = [(form_id, 'form')]
        result['res_id'] = self.purchase_id.id
        return result

    def action_view_invoice(self):
        if self.rma_order_type == 'customer':
            invoice_type = 'out_invoice'
            action = self.env.ref('account.action_move_out_invoice_type')
        else:
            invoice_type = 'in_invoice'
            action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        if invoice_type == 'out_invoice':
            invoice_ids = self.env['account.move'].search(
                [('rma_order_id', 'in', self.sale_id.rma_order_ids.ids), ('type', '=', invoice_type)])
        else:
            invoice_ids = self.env['account.move'].search(
                [('rma_order_id', 'in', self.purchase_id.rma_order_ids.ids), ('type', '=', invoice_type)])
        if len(invoice_ids) == 1:
            result['views'] = [(False, 'form')]
            result['res_id'] = invoice_ids[0].id
        else:
            result['domain'] = "[('rma_order_id','in',[" + ','.join(map(str, self.sale_id.rma_order_ids.ids if invoice_type == 'out_invoice' else self.purchase_id.rma_order_ids.ids)) + "]),('type','=','" + str(invoice_type) + "')]"
        return result

    def action_view_refund(self):
        if self.rma_order_type == 'customer':
            invoice_type = 'out_refund'
            action = self.env.ref('account.action_move_out_refund_type')
        else:
            invoice_type = 'in_refund'            
            action = self.env.ref('account.action_move_in_refund_type')
        result = action.read()[0]
        invoice_ids = self.env['account.move'].search([('rma_order_id', 'in', self.purchase_id.rma_order_ids.ids if invoice_type == 'in_refund' else self.sale_id.rma_order_ids.ids), ('type', '=', invoice_type)])
        if len(invoice_ids) == 1:
            result['views'] = [(False, 'form')]
            result['res_id'] = invoice_ids[0].id
        else:
            result['domain'] = "[('rma_order_id','in',[" + ','.join(map(str, self.purchase_id.rma_order_ids.ids if invoice_type == 'in_refund' else self.sale_id.rma_order_ids.ids)) + "]),('type','=','" + str(invoice_type) + "')]"
        return result

    def action_view_repair(self):
        action = self.env.ref('repair.action_repair_order_tree')
        result = action.read()[0]
        rma_order_ids = self.ids
        repair_ids = self.env['repair.order'].search([('rma_order_id', 'in', rma_order_ids)])
        if len(repair_ids) == 1:
            form = self.env.ref('repair.view_repair_order_form', False)
            form_id = form.id if form else False
            result['views'] = [(form_id, 'form')]
            result['res_id'] = repair_ids[0].id
        else:
            result['domain'] = "[('rma_order_id','in',[" + ','.join(map(str, rma_order_ids)) + "])]"
        return result  

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        context = result['context']
        picking_type_id = None
        rma_order_ids = self.ids
        domain = [('rma_order_id', 'in', rma_order_ids)]
        if self.rma_order_type == 'customer':
            location_id = self.partner_id.property_stock_customer.id
        else:
            location_id = self.partner_id.property_stock_supplier.id
        context = context.replace('}',
            ", 'default_warehouse_id' : %s, 'default_team_id': %s, 'default_origin': '%s'}" % 
            (self.warehouse_id.id, self.team_id.id, self.number))
        picking_type_code = self._context.get('picking_type_code')
        if 'picking_type_code' in self._context:
            if picking_type_code == 'outgoing':
                picking_type_id = self.warehouse_id.out_type_id.id
                domain += [('location_dest_id', '=', location_id)]
            elif picking_type_code == 'incoming':
                picking_type_id = self.warehouse_id.out_type_id.return_picking_type_id.id or self.warehouse_id.in_type_id.id
                domain += [('location_id', '=', location_id)]
            context = context.replace('}', ", 'default_picking_type_id' : %s}" % picking_type_id)
        result['context'] = context
        picking_ids = self.env['stock.picking'].search(domain)
        if len(picking_ids) == 1:
            form = self.env.ref('stock.view_picking_form', False)
            form_id = form.id if form else False
            result['views'] = [(form_id, 'form')]
            result['res_id'] = picking_ids[0].id
        elif not picking_ids:
            if picking_type_code == 'incoming':
                products = self.sale_id.order_line.mapped('product_id')
                if not self.sale_id:
                    products = self.purchase_id.order_line.mapped('product_id')
                return {
                    'name': 'Create Return',
                    'view_mode': 'form',
                    'res_model': 'wizard.create.picking',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_picking_type_id_number': picking_type_id,
                        'default_rma_order_id': self.id,
                        'default_product_ids': products.filtered(lambda x:
                            x.type != 'service' and x.active == True).ids
                    }
                }
            elif picking_type_code == 'outgoing':
                products = self.purchase_id.order_line.mapped('product_id')
                if not self.purchase_id:
                    products = self.sale_id.order_line.mapped('product_id')
                return {
                    'name': 'Create Delivery',
                    'view_mode': 'form',
                    'res_model': 'wizard.create.picking',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_picking_type_id_number': picking_type_id,
                        'default_rma_order_id': self.id,
                        'default_product_ids': products.filtered(lambda x:
                            x.type != 'service' and x.active == True).ids
                    }
                }
            else:
                result['views'] = [(False, 'form')]
                result['target'] = 'current'
        else:
            result['domain'] = "[('rma_order_id','in',[" + ','.join(map(str, rma_order_ids)) + "]),('id','in',[" + ','.join(map(str, picking_ids.ids)) + "])]"
        return result

    def action_view_receipt(self):
        action = self.env.ref('stock.action_picking_tree_all')
        rma_order_ids = self.ids
        delivery_orders = self.env['stock.picking'].search([('rma_order_id', 'in', rma_order_ids), ('picking_type_code', '=', 'incoming')])
        result = action.read()[0]

        if len(delivery_orders) > 1:
            result['domain'] = "[('id','in',%s)]" % (delivery_orders.ids)
        elif len(delivery_orders) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = delivery_orders.id
        else:
            result['views'] = [(False, 'form')]
            result['target'] = 'current'
        return result
