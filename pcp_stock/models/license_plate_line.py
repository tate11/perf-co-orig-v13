# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LicensePlateLine(models.Model):
    _name = "license.plate.line"
    _description = "License Plate Line"

    license_plate_id = fields.Many2one('license.plate', 'License Plate')
    product_id = fields.Many2one('product.product', 'Product', related="license_plate_id.product_id", readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    reserved_qty = fields.Float('Reserved Quantity', digits="Product Unit of Measure", default=0.0)
    workorder_line_id = fields.Many2one('mrp.workorder.line', 'Workorder Line')
    move_line_id = fields.Many2one('stock.move.line', 'Move Line')

    def update_license_plate_line_with_workorder(self, workorder):
        lp_line_id = workorder.workorder_line_id and workorder.workorder_line_id.lp_line_id or False
        if workorder.lp_number_id:
            if lp_line_id:
                lp_line_id.write({'reserved_qty': workorder.qty_done,})
            else:
                lp_line_id = self.env["license.plate.line"].create({
                    'license_plate_id': workorder.lp_number_id.id,
                    'product_id': workorder.component_id.id,
                    'product_uom_id': workorder.component_uom_id.id,
                    'reserved_qty': workorder.qty_done,
                    'workorder_line_id': workorder.workorder_line_id.id
                })
        else:
            lp_line_id and lp_line_id.unlink()

        return lp_line_id or False

    def update_license_plate_line_with_move_line(self, move_line, old_lp_ids, new_lp_ids):
        if not old_lp_ids:
            old_lp_ids = self.env['license.plate'].browse()
        if not new_lp_ids:
            new_lp_ids = self.env['license.plate'].browse()
        removed_lp_ids = old_lp_ids - new_lp_ids
        added_lp_ids = new_lp_ids - old_lp_ids
        if removed_lp_ids:
            lp_line_ids = removed_lp_ids.mapped('lp_line_ids').filtered(lambda l: l.move_line_id.id == move_line.id)
            lp_line_ids.unlink()
        if added_lp_ids:
            values =[]
            for lp in added_lp_ids:
                values.append({
                    'license_plate_id': lp.id,
                    'product_id': move_line.product_id.id,
                    'product_uom_id': move_line.product_uom_id.id,
                    'reserved_qty': lp.product_qty,
                    'move_line_id': move_line.id
                })
            self.create(values)