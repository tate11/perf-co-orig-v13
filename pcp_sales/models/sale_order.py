# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_required_type = fields.Boolean("Is Required Type", compute="_compute_is_required_type", store=True)
    qty_returned = fields.Float('Quantity Returned', digits='Product Unit of Measure')
    po_number = fields.Char("Customer PO Number", help="Customer PO Number")
    ship_via = fields.Char("Ship VIA")
    free_on_board = fields.Char("F.O.B", help="Free On Board")

    trailer_number = fields.Char('Trailer NO')
    special_instructions = fields.Char('Special Instructions')
    master_bol = fields.Boolean('Master BoL', default=False)

    carrier = fields.Char('Carrier Name')
    vessel_no = fields.Char('Vessel NO')
    booking_no = fields.Char('Booking NO')
    container_no = fields.Char('Container NO')
    seal_no = fields.Char('Seal NO')

    freight_terms = fields.Selection([
        ('prepaid', 'Prepaid'),
        ('collect', 'Collect'),
        ('third_party', 'Third Party'),
    ])
    trailer_loaded = fields.Selection([
        ('shipper', 'By Shipper'),
        ('driver', 'By Driver'),
    ])
    freight_counted = fields.Selection([
        ('shipper', 'By Shipper'),
        ('driver_pallet', 'By Driver / pallets said to contain'),
        ('driver_pieces', 'By Driver / Pieces'),
    ])

    @api.depends('company_id')
    def _compute_is_required_type(self):
        pcp_company = self.env.ref('base.main_company')
        for rec in self:
            rec.is_required_type = True if rec.company_id and rec.company_id == pcp_company else False

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        """
        Override method of mail.thread model to prevent sending email to salesperson
        """
        if self._name == 'sale.order':
            if 'user_id' in updated_values and not self.env.company.send_assigned_so_email_to_sales_person:
                del updated_values['user_id']
        return super(SaleOrder, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)
