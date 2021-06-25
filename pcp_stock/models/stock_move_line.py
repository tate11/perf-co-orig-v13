# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    number_of_lp = fields.Integer(
        'No. of LP',
        compute='_compute_lp'
    )
    total_qty_of_lp = fields.Float(
        'Total quantity of LP',
        digits='Product Unit of Measure',
        compute='_compute_lp'
    )

    license_plate_ids = fields.Many2many('license.plate', string='License Plate Numbers')
    picking_type_code = fields.Selection(related='picking_id.picking_type_code')
    picking_code = fields.Selection(store=True)
    # PC-121: Don't create lot name when creating new move line on Transfer
    # @api.onchange('product_id')
    # def onchange_product_id_to_generate_lot_name(self):
    #     if self.product_id and self.should_generate_lot_name():
    #         self.lot_name = self.env['stock.production.lot'].generate_lot_name()

    show_lp_buttons_generating = fields.Boolean(related='picking_id.picking_type_id.show_lp_buttons_generating')
    show_lp_buttons_scanning = fields.Boolean(related='picking_id.picking_type_id.show_lp_buttons_scanning')

    def _compute_lp(self):
        lp_env = self.env['license.plate']
        for line in self:
            number_of_lp = 0
            total_qty_of_lp = 0.0
            if line.lot_id:
                license_plates = lp_env.search([('lot_id', '=', line.lot_id.id)])
                number_of_lp = len(license_plates)
                total_qty_of_lp = sum(license_plates.mapped('product_qty'))
            line.number_of_lp = number_of_lp
            line.total_qty_of_lp = total_qty_of_lp

    @api.onchange('license_plate_ids')
    def _onchange_license_plate_ids(self):
        self.qty_done = sum(self.mapped('license_plate_ids.product_qty')) - sum(self.mapped('license_plate_ids.reserved_qty'))

    @api.model
    def create(self, vals):
        # PC-121: Don't create lot name when creating new move line on Transfer
        # self.update_lot_name(vals)
        res = super(StockMoveLine, self).create(vals)
        if res.picking_type_code == 'outgoing':
            self.env['license.plate.line'].update_license_plate_line_with_move_line(res, [], res.license_plate_ids)
        return res

    def write(self, vals):
        outgoing_lines = self.filtered(lambda l: l.picking_type_code == 'outgoing')
        old_lp_ids_dict = dict((line.id, line.license_plate_ids.ids) for line in outgoing_lines)
        res = super(StockMoveLine, self).write(vals)
        for line in outgoing_lines:
            old_lp_ids = self.env['license.plate'].browse(old_lp_ids_dict[line.id])
            self.env['license.plate.line'].update_license_plate_line_with_move_line(line, old_lp_ids, line.license_plate_ids)
        return res

    def unlink(self):
        for picking in self.filtered(lambda l: l.picking_type_code == 'outgoing'):
            self.env['license.plate.line'].update_license_plate_line_with_move_line(picking, picking.license_plate_ids, [])
        return super(StockMoveLine, self).unlink()

    # def update_lot_name(self, vals):
    #     """
    #     Generate lot name base on created lot date
    #     """
    #     if not vals.get('lot_name') and 'lot_id' not in vals and self.should_generate_lot_name(vals):
    #         vals['lot_name'] = self.env['stock.production.lot'].generate_lot_name()
    #
    #     return True

    def should_generate_lot_name(self, vals=None):
        """
        Check that should generate lot name for the move line.
        :param vals: is dictionary that includes product_id and picking_id.
                    If 'vals' is None, get the product_id and the picking_id from self.
        """
        if vals:
            picking_id = vals.get('picking_id') and self.env['stock.picking'].browse(vals.get('picking_id'))
            product_id = vals.get('product_id') and self.env['product.product'].browse(vals.get('product_id'))
            picking_type = picking_id and picking_id.picking_type_id
        else:
            self.ensure_one()
            product_id = self.product_id
            picking_type = self.picking_id and self.picking_id.picking_type_id
        is_generate_lot = product_id.tracking != 'none' and picking_type and picking_type.use_create_lots \
            and picking_type.show_reserved and picking_type.auto_create_lot \
            and product_id.auto_create_lot and picking_type.code == 'incoming'

        return is_generate_lot

    def create_lot_name_for_move_line(self):
        self.ensure_one()
        owner_code = self._context.get('owner_code')
        if self.owner_id:
            owner_code = self.owner_id.short_code or ''
        lot_name = self.env['stock.production.lot'].generate_lot_name(code=owner_code)
        self.sudo().write({
            'lot_name': lot_name
        })
        return lot_name

    def generate_lp_number(self):
        self.ensure_one()
        action = self.env.ref('pcp_stock.generate_license_plate_action').read()[0]
        action['context'] = {
            'default_lot_id': self.lot_id.id,
            'default_type': 'incoming' if self.picking_code == 'incoming' else 'production',
            'default_qty_done': self.qty_done,
            'default_product_qty': self.qty_done
        }

        return action

    def view_lp_number(self):
        self.ensure_one()
        action = self.env.ref('pcp_stock.license_plate_action').read()[0]
        lot_id = self.lot_id
        if lot_id:
            existing_lp = self.env['license.plate'].search([('lot_id', '=', lot_id.id)])
            action['domain'] = [('id', 'in', existing_lp.ids)]
        return action

    @api.model
    def search_license_plate(self, move_line_ids, lp_barcode):
        move_lines = self.browse(move_line_ids)
        lp = self.env['license.plate'].search([('name', '=', lp_barcode)], limit=1)
        if move_lines and lp:
            line = move_lines.filtered(lambda e: e.lot_id.id == lp.lot_id.id)
            if line and lp.id not in line.license_plate_ids.ids:
                return line.id
            else:
                return False
        else:
            return False
