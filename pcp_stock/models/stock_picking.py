# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', copy=False)
    source_sale_id = fields.Many2one('sale.order', related='mo_id.source_sale_id')
    customer_materials = fields.Boolean(string="Receive Customer's Materials", default=False, copy=False)
    technical_owner_id = fields.Many2one(
        'res.partner', 'Assign Owner',
        check_company=True,
        help="When validating the transfer, the products will be assigned to this owner.")

    @api.model
    def create(self, values):
        if 'origin' in values:
            mo = self.env['mrp.production'].search([('name', '=', values['origin'])])
            if mo:
                values.update({
                    'mo_id': mo.id,
                    # This feature should be removed since PCP has their own materials
                    # 'customer_materials': True if mo.source_sale_id else False
                })
        values = self.update_owner_id(values)
        return super(StockPicking, self).create(values)

    def write(self, values):
        values = self.update_owner_id(values)
        return super(StockPicking, self).write(values)

    def update_owner_id(self, values):
        current_company_id = self and self.mapped('company_id').id or values.get('company_id', False)
        values = self.env['res.partner']._update_owner_id(
            values, owner_str='owner_id', technical_owner_str='technical_owner_id', company_id=current_company_id)
        return values

    def action_assign(self):
        customer_mateirals = self.mapped('customer_materials')
        owner_id = self.mapped('mo_id.source_sale_id.partner_id')
        if customer_mateirals and customer_mateirals[0] and owner_id:
            owner_id = owner_id[0]
        else:
            owner_id = False

        return super(StockPicking, self.with_context(owner_id=owner_id)).action_assign()

    def button_auto_create_lot_name(self):
        self.ensure_one()
        owner_code = None
        if self.owner_id:
            owner_code = self.owner_id.short_code or ''
        for line in self.move_line_ids.filtered(lambda l: l.product_id.tracking != 'none' and not l.lot_name and not l.lot_id):
            line.with_context(owner_code=owner_code).create_lot_name_for_move_line()

    def get_barcode_view_state(self):
        """
        Override to add license plates and use_create_lots to stock move line dict
        """
        pickings = super(StockPicking, self).get_barcode_view_state()
        for picking in pickings:
            for line in picking['move_line_ids']:
                line['scanned_license_plates'] = [[lp.id, lp.name] for lp in self.env['stock.move.line'].browse(line['id']).license_plate_ids]
                if line['lot_id']:
                    line['license_plates'] = self.env['license.plate'].search_read([('lot_id', '=', line['lot_id'][0])], ['id', 'name', 'product_qty', 'reserved_qty'])

                else:
                    line['license_plates'] = []
                    
                line["use_create_lots"] = picking["use_create_lots"]

        return pickings
