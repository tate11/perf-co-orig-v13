# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.tools.float_utils import float_round
from datetime import datetime


class Picking(models.Model):
    _inherit = 'stock.picking'

    po_number = fields.Char('Customer PO', related='sale_id.po_number', store=True, help='Customer PO Number')
    ship_via = fields.Char('Ship VIA', related='sale_id.ship_via', store=True)
    free_on_board = fields.Char('F.O.B', related='sale_id.free_on_board', store=True, help='Free On Board')

    trailer_number = fields.Char('Trailer NO', related='sale_id.trailer_number', readonly=False)
    special_instructions = fields.Char('Special Instructions', related='sale_id.special_instructions', readonly=False)
    master_bol = fields.Boolean('Master BoL', related='sale_id.master_bol', default=False, readonly=False)

    carrier = fields.Char('Carrier Name', related='sale_id.carrier', readonly=False)
    vessel_no = fields.Char('Vessel NO', related='sale_id.vessel_no', readonly=False)
    booking_no = fields.Char('Booking NO', related='sale_id.booking_no', readonly=False)
    container_no = fields.Char('Container NO', related='sale_id.container_no', readonly=False)
    seal_no = fields.Char('Seal NO', related='sale_id.seal_no', readonly=False)

    freight_terms = fields.Selection([
        ('prepaid', 'Prepaid'),
        ('collect', 'Collect'),
        ('third_party', 'Third Party'),
    ], string="Freight Terms", related='sale_id.freight_terms', readonly=False)
    trailer_loaded = fields.Selection([
        ('shipper', 'By Shipper'),
        ('driver', 'By Driver'),
    ], string="Trailer loaded", related='sale_id.trailer_loaded', readonly=False)
    freight_counted = fields.Selection([
        ('shipper', 'By Shipper'),
        ('driver_pallet', 'By Driver / pallets said to contain'),
        ('driver_pieces', 'By Driver / Pieces'),
    ], string="Freight Counted", related='sale_id.freight_counted', readonly=False)

    def get_bill_of_lading_data(self):
        data = []
        pcp_partner = self.env.ref('base.main_partner')
        pcp_company = self.env.ref('base.main_company')
        for picking_id in self:
            info = {}
            sale_id = picking_id.sale_id
            company_id = picking_id.company_id or pcp_company
            partner_id = picking_id.company_id and picking_id.company_id.partner_id or pcp_partner
            shipper_info = {
                'number': partner_id.short_code  or '',
                'name': partner_id.name  or '',
                'street': partner_id.street  or '',
                'city': partner_id.city  or '',
                'state_code': partner_id.state_id and partner_id.state_id.code  or '',
                'zip_code': partner_id.zip or '',
                'company_name': company_id.name or '',
            }

            customer_id = picking_id.sale_id.partner_id
            customer_info = {
                'name': customer_id.name or '',
                'street': customer_id.street or '',
                'street2': customer_id.street2 or '',
                'city': customer_id.city or '',
                'state_code': customer_id.state_id and customer_id.state_id.code or '',
                'zip_code': customer_id.zip or '',
            }

            delivery_id = picking_id.partner_id
            delivery_info = {
                'name': delivery_id.name or '',
                'street': delivery_id.street or '',
                'city': delivery_id.city or '',
                'state_code': delivery_id.state_id and delivery_id.state_id.code or '',
                'zip_code': delivery_id.zip or '',
            }

            products_lst = []
            total_weight = 0
            total_qty = 0
            for move_id in picking_id.move_lines:
                quantity = float_round(move_id.quantity_done, precision_rounding=2)
                total_qty += quantity
                weight_lbs = float_round(move_id.product_id.weight * quantity, precision_rounding=2)
                total_weight += weight_lbs
                products_lst.append({
                    'name': move_id.product_id.name,
                    'quantity': quantity,
                    'uom_name': move_id.product_uom.name,
                    'weight_lbs': weight_lbs
                })

            max_lines = 6
            if max_lines - len(products_lst) >= 0:
                blank_lines = max_lines - len(products_lst)
            else:
                blank_lines = 0
            info.update({
                'bol_date': datetime.now().strftime('%m/%d/%Y'),
                'bol_number': picking_id.name,
                'shipper': shipper_info,
                'customer': customer_info,
                'delivery': delivery_info,
                'customer_po_number': sale_id.po_number or '',
                'so_number': sale_id.name or '',
                'products_lst': products_lst,
                'blank_lines': blank_lines,
                'total_weight': total_weight,
                'total_qty': total_qty,

                'trailer_number': picking_id.trailer_number,
                'special_instructions': picking_id.special_instructions,
                'master_bol': picking_id.master_bol,
                'carrier': picking_id.carrier,
                'vessel_no': picking_id.vessel_no,
                'booking_no': picking_id.booking_no,
                'container_no': picking_id.container_no,
                'seal_no': picking_id.seal_no,

                'freight_terms': picking_id.freight_terms,
                'trailer_loaded': picking_id.trailer_loaded,
                'freight_counted': picking_id.freight_counted,
            })
            data.append(info)
        return data
