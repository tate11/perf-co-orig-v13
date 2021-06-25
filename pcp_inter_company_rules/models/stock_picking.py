# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_order_for_delivery = fields.Many2one('purchase.order')

    def action_done(self):
        res = super(StockPicking, self.sudo()).action_done()
        self.reserved_for_inter_company_transfer()
        self.create_receipt_materials()
        self.env['license.plate'].update_quantity_license_plate(pickings=self)
        return res

    def action_assign(self):
        # TODO: check this function
        # self.check_inter_company_rules()
        return super(StockPicking, self).action_assign()

    def check_inter_company_rules(self):
        self = self.sudo()
        for picking in self:
            purchase_id = picking.purchase_id
            inter_comp_sale_id = purchase_id and purchase_id.get_inter_company_sale_order()
            if inter_comp_sale_id and not inter_comp_sale_id.check_fully_shipping_products():
                raise UserError(_(
                    'Please validate the Delivery Orders on the %s before reserving the products on the %s.' %
                    (inter_comp_sale_id.name, purchase_id.name)))

    def reserved_for_inter_company_transfer(self):
        self = self.sudo()
        for picking in self:
            inter_comp_purchase_order = picking.sale_id and picking.sale_id.get_inter_company_purchase_order()
            if inter_comp_purchase_order and picking.picking_type_code == 'outgoing':
                inter_company_receipt_order = inter_comp_purchase_order.picking_ids.filtered(
                    lambda p: p.picking_type_code == 'incoming' and p.state in ['confirmed', 'waiting'])
                inter_company_receipt_order and inter_company_receipt_order._reserved_for_inter_company_receipt_order(picking)

    def _reserved_for_inter_company_receipt_order(self, delivery_order):
        """
        After validating the Inter company Delivery Order, auto-reserve the products on the Inter company Purchase Order
        :param self: The transfer is Receipt Order on Inter company Purchase Order
        :param delivery_order: The transfer is Delivery Order on Inter company Sale Order
        """
        self.ensure_one()
        self = self.sudo()
        stock_production_lot_env = self.env['stock.production.lot'].sudo()
        license_plate_env = self.env['license.plate'].sudo()
        values = []
        orig_moves = delivery_order.move_lines
        for move in self.move_lines:
            origin_move = orig_moves.filtered(lambda m: m.product_id.id == move.product_id.id)
            production_id = move.mapped('move_orig_ids.production_id')
            if production_id:
                if production_id.state not in ['to_close', 'done']:
                    production_id.force_validate_subcontracting_production(move, origin_move)
                    for line in origin_move.move_line_ids:
                        lot_id = stock_production_lot_env.search([
                            ('name', '=', line.lot_id.name),
                            ('product_id', '=', line.product_id.id),
                            ('company_id', '=', self.company_id.id)
                        ], limit=1)
                        if lot_id and line.license_plate_ids:
                            new_lp_ids = []
                            for lp in line.license_plate_ids:
                                lp_line_ids = lp.lp_line_ids.filtered(lambda l: l.move_line_id.id == line.id)
                                reserved_qty = sum(lp_line_ids.mapped('reserved_qty'))
                                new_lp = license_plate_env.search([
                                    ('name', '=', lp.name),
                                    ('lot_id', '=', lot_id.id),
                                    ('company_id', '=', self.company_id.id)
                                ], limit=1)
                                if not new_lp:
                                    new_lp = license_plate_env.create({
                                        'name': lp.name,
                                        'lot_id': lot_id.id,
                                        'type': 'incoming',
                                        'product_qty': reserved_qty,
                                    })
                                else:
                                    new_lp.write({'product_qty': new_lp.product_qty + reserved_qty})
                                new_lp_ids.append(new_lp.id)
                            move_line = self.move_line_ids.filtered(lambda l: l.product_id == line.product_id and l.lot_id.id == lot_id.id)
                            if move_line:
                                move_line.write({'license_plate_ids': [(6, 0, new_lp_ids)]})

            else:
                values.extend(self._prepare_stock_move_line(origin_move, move))

        move_line_ids = self.env['stock.move.line'].sudo().create(values)
        move_line_ids.mapped('move_id').write({'state': 'assigned'})
        self.button_validate()
        self.message_post(body="The Receipt Order has been auto-reserved the products from the Delivery Order: "
                               "<strong>%s</strong>" % delivery_order.name)

    def _prepare_stock_move_line(self, origin_move, destination_move, assign_owner=False):
        """
        Create the stock move lines on the destination move base on the origin move
        :param origin_move: It is the stock move on the validated transfer
        :param destination_move: It is the stock move on the transfer that will be auto-reserve the products
        :param assign_owner: If true, assign the owner for move lint. Otherwise, don't assign the owner.
        """
        values = []
        self = self.sudo()
        stock_production_lot_env = self.env['stock.production.lot'].sudo()
        license_plate_env = self.env['license.plate'].sudo()
        license_plate_line_env = self.env['license.plate.line'].sudo()
        for line in origin_move.move_line_ids:
            val = {
                'move_id': destination_move.id,
                'picking_id': destination_move.picking_id.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom_id.id,
                'product_uom_qty': line.qty_done,
                'location_id': destination_move.location_id.id,
                'location_dest_id': destination_move.location_dest_id.id,
                'owner_id': assign_owner and destination_move.picking_id.partner_id.id,
            }

            if line.lot_id:
                new_lot = stock_production_lot_env.search([
                    ('name', '=', line.lot_id.name),
                    ('product_id', '=', line.product_id.id),
                    ('company_id', '=', destination_move.company_id.id)
                ], limit=1)
                if not new_lot:
                    new_lot = stock_production_lot_env.create({
                        'name': line.lot_id.name,
                        'product_id': line.product_id.id,
                        'company_id': destination_move.company_id.id
                    })
                val.update({
                    'lot_name': new_lot.name,
                    'lot_id': new_lot.id
                })

            if new_lot and line.license_plate_ids:
                new_lp_ids = []
                for lp in line.license_plate_ids:
                    lp_line_ids = lp.lp_line_ids.filtered(lambda l: l.move_line_id.id == line.id)
                    reserved_qty = sum(lp_line_ids.mapped('reserved_qty'))
                    new_lp = license_plate_env.search([
                        ('name', '=', lp.name),
                        ('lot_id', '=', line.lot_id.id),
                        ('company_id', '=', destination_move.company_id.id)
                    ], limit=1)
                    if not new_lp:
                        new_lp = license_plate_env.create({
                            'name': lp.name,
                            'lot_id': new_lot.id,
                            'type': lp.type,
                            'product_qty': reserved_qty,
                        })
                    else:
                        new_lp.write({'product_qty': new_lp.product_qty + reserved_qty})
                    new_lp_ids.append(new_lp.id)
                val['license_plate_ids'] = [(6, 0, new_lp_ids)]

            values.append(val)
        return values

    def create_receipt_materials(self):
        """
        At PCP company, create a new Receipt Materials to receive materials from Delivery Order on WFP company
        """
        StockPicking = self.env['stock.picking'].sudo()
        self = self.sudo()
        subcontracting_location = self.env.ref('pcp_base.stock_location_subcontracting_wfp')
        for picking in self.filtered(lambda p: p.location_dest_id.id == subcontracting_location.id and p.state == 'done'):
            sale_order = picking.purchase_order_for_delivery and picking.purchase_order_for_delivery.get_inter_company_sale_order()
            if sale_order:
                values = picking._prepare_receipt_materials()
                new_receipt = StockPicking.create(values)
                sale_order.write({'receipt_picking_ids': [(4, new_receipt.id, 0)]})

                moves = picking._create_stock_moves_for_receipt_materials(new_receipt)
                moves._action_confirm()
                picking._reserved_for_receipt_materials(new_receipt)
                moves.write({'state': 'assigned'})
                new_receipt.message_post(body="The Receipt Material has been created from the Delivery Material: "
                                              "<strong>%s</strong>" % picking.name)
        return True

    @api.model
    def _prepare_receipt_materials(self):
        partner_id = self.env.ref('pcp_base.wfp_company_partner')
        if not partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'partner_id': partner_id.id,
            'owner_id': partner_id.id,
            'technical_owner_id': partner_id.id,
            'origin': self.purchase_order_for_delivery.partner_ref,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'location_id': partner_id.property_stock_supplier.id,
            'company_id': self.env.ref('base.main_company').id,
            'user_id': False,
        }

    def _create_stock_moves_for_receipt_materials(self, new_receipt):
        values = []
        self = self.sudo()
        for move in self.move_lines.filtered(lambda l: l.product_id and l.product_id.type in ['product', 'consu']):
            values.append({
                # truncate to 2000 to avoid triggering index limit error
                'name': (self.name or '')[:2000],
                'subcontracting_origin_move': move.id,
                'product_id': move.product_id.id,
                'product_uom_qty': move.quantity_done,
                'product_uom': move.product_uom.id,
                'location_id': new_receipt.location_id.id,
                'location_dest_id': new_receipt.location_dest_id.id,
                'picking_id': new_receipt.id,
                'partner_id': new_receipt.partner_id.id,
                'state': 'draft',
                'company_id': new_receipt.company_id.id,
                'picking_type_id': new_receipt.picking_type_id.id,
                'group_id': new_receipt.group_id.id,
                'origin': new_receipt.origin,
                'warehouse_id': new_receipt.picking_type_id.warehouse_id.id,
                'price_unit': move.product_id.standard_price,
            })

        return self.env['stock.move'].sudo().create(values)

    def _reserved_for_receipt_materials(self, new_receipt):
        """
        After validating the Delivery Order on WFP company, auto-reserve the Receipt Materials on PCP company
        """
        values = []
        self = self.sudo()
        for receipt_move in new_receipt.move_lines:
            origin_move = receipt_move.subcontracting_origin_move
            values.extend(self._prepare_stock_move_line(origin_move, receipt_move, assign_owner=True))

        self.env['stock.move.line'].sudo().create(values)

    def action_record_components(self):
        self.ensure_one()
        if self.state != 'assigned':
            self.check_inter_company_rules()
        return super(StockPicking, self).action_record_components()


from odoo.addons.mrp_subcontracting.models.stock_picking import StockPicking as OriginalStockPicking

def action_done(self):
    """
    Override function to avoid the error that when validating the MO before validating the Receipt Order in the Subcontracting process.
    """
    res = super(OriginalStockPicking, self).action_done()
    productions = self.env['mrp.production']
    for picking in self:
        for move in picking.move_lines:
            if not move.is_subcontract:
                continue
            production = move.move_orig_ids.production_id
            if move._has_tracked_subcontract_components():
                move.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel')).move_line_ids.unlink()
                move_finished_ids = move.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
                # PCP: If not move_finished_ids, don't create move lines.
                if move_finished_ids:
                    for ml in move.move_line_ids:
                        ml.copy({
                            'picking_id': False,
                            'production_id': move_finished_ids.production_id.id,
                            'move_id': move_finished_ids.id,
                            'qty_done': ml.qty_done,
                            'result_package_id': False,
                            'location_id': move_finished_ids.location_id.id,
                            'location_dest_id': move_finished_ids.location_dest_id.id,
                        })
            else:
                # PCP: Check that if the state of MO in ['done', 'to_close'], don't produce the MO
                if production not in ['to_close', 'done']:
                    wizards_vals = []
                    for move_line in move.move_line_ids:
                        wizards_vals.append({
                            'production_id': production.id,
                            'qty_producing': move_line.qty_done,
                            'product_uom_id': move_line.product_uom_id.id,
                            'finished_lot_id': move_line.lot_id.id,
                            'consumption': 'strict',
                        })
                    wizards = self.env['mrp.product.produce'].with_context(default_production_id=production.id).create(
                        wizards_vals)
                    wizards._generate_produce_lines()
                    wizards._record_production()
            productions |= production

        # PCP:  Check that if the state of MO is done, don't validate the MO
        for subcontracted_production in productions.filtered(lambda p: p.state != 'done'):
            if subcontracted_production.state == 'progress':
                subcontracted_production.post_inventory()
            else:
                subcontracted_production.button_mark_done()
            # For concistency, set the date on production move before the date
            # on picking. (Tracability report + Product Moves menu item)
            minimum_date = min(picking.move_line_ids.mapped('date'))
            production_moves = subcontracted_production.move_raw_ids | subcontracted_production.move_finished_ids
            production_moves.write({'date': minimum_date - timedelta(seconds=1)})
            production_moves.move_line_ids.write({'date': minimum_date - timedelta(seconds=1)})
    return res

OriginalStockPicking.action_done = action_done
