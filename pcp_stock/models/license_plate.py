# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LicensePlate(models.Model):
    _name = "license.plate"
    _description = "License Plate"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _sql_constraints = [
        (
            "lot_lp_uniq",
            "unique(lot_id, name)",
            "The Lot/Serial Number and License Plate Number combination must be unique.",
        )
    ]

    name = fields.Char('License Plate Number', index=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', readonly=True, index=True)
    type = fields.Selection(
        [("incoming", "Incoming"), ("production", "Production")],
        string="Type",
        default="incoming",
        required=True,
    )

    lp_line_ids = fields.One2many('license.plate.line', 'license_plate_id', string='License Plate Lines')
    product_id = fields.Many2one('product.product', related="lot_id.product_id", readonly=True)
    product_qty = fields.Float('Quantity', digits="Product Unit of Measure",)
    reserved_qty = fields.Float('Reserved Quantity', digits="Product Unit of Measure", compute='_compute_reserved_qty', store=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='lot_id.product_uom_id', readonly=True, store=True)
    company_id = fields.Many2one('res.company', related="lot_id.company_id", readonly=True, store=True, index=True)
    use_date = fields.Datetime(related="lot_id.use_date", readonly=True)
    removal_date = fields.Datetime(related="lot_id.removal_date", readonly=True)
    life_date = fields.Datetime(related="lot_id.life_date", readonly=True)
    alert_date = fields.Datetime(related="lot_id.alert_date", readonly=True)
    note = fields.Text('Description')

    def get_lp_sequence(self, lp_type):
        if lp_type == 'production':
            lp_name = self.env['ir.sequence'].next_by_code('lp.production.serial')
        else:
            lp_name = self.env['ir.sequence'].next_by_code('lp.incoming.serial')
        return lp_name

    @api.model
    def create(self, values):
        if 'name' not in values:
            values['name'] = self.get_lp_sequence(values.get('type', 'incoming'))
        return super(LicensePlate, self).create(values)

    @api.depends('lp_line_ids', 'lp_line_ids.reserved_qty')
    def _compute_reserved_qty(self):
        for rec in self:
            rec.reserved_qty = sum(rec.mapped('lp_line_ids.reserved_qty'))

    def update_quantity_license_plate(self, workorder=False, pickings=False):
        if workorder:
            lp_line_ids = workorder.mapped('raw_workorder_line_ids.lp_line_id')
            lp_ids = lp_line_ids.mapped('license_plate_id')
            for lp in lp_ids:
                delete_lp_lines = lp.lp_line_ids.filtered(lambda l: l.id in lp_line_ids.ids)
                lp.write({'product_qty': lp.product_qty - sum(delete_lp_lines.mapped('reserved_qty'))})
            lp_line_ids.unlink()
        elif pickings:
            move_line_ids = pickings.move_line_ids
            lp_ids = move_line_ids.license_plate_ids
            delete_lp_lines = self.env['license.plate.line'].browse()
            for lp in lp_ids:
                lp_lines = lp.lp_line_ids.filtered(lambda l: l.move_line_id.id in move_line_ids.ids)
                lp.write({'product_qty': lp.product_qty - sum(lp_lines.mapped('reserved_qty'))})
                delete_lp_lines |= lp_lines
            delete_lp_lines.unlink()
