# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    operation_name = fields.Char(string="Operation Name", compute='_compute_operation_info', store=True)
    costs_hour = fields.Float(string="Costs Hour", compute='_compute_operation_info', store=True, default=0.0)
    workcenter_code = fields.Char(string="Workcenter Code", related='workcenter_id.code', default='')
    is_change_date = fields.Boolean(compute='_compute_is_change_date')

    # Additional Information of the finished good
    unit_upc_code = fields.Char("Unit UPC", related='production_id.unit_upc_code')
    case_upc_code = fields.Char("Case UPC", related='production_id.case_upc_code')
    best_by_date = fields.Date("Best By", related='production_id.best_by_date', readonly=False)
    case_lot = fields.Char("Case Lot", related='production_id.case_lot',readonly=False)
    ti_pallet_size = fields.Integer("TI Pallet", related='production_id.ti_pallet_size')
    hi_pallet_size = fields.Integer("HI Pallet", related='production_id.hi_pallet_size')
    case_count_per_pallet = fields.Integer("Per Pallet Case Count", related='production_id.case_count_per_pallet')
    total_pallets = fields.Float("Total Pallets", related='production_id.total_pallets', digits="Product Unit of Measure")
    unit_count_per_case = fields.Integer("Case Count", related='production_id.unit_count_per_case')
    weight_ounce = fields.Float("Unit Weight", related='production_id.weight_ounce', digits="Stock Weight",)
    weight_gram = fields.Float("Grams", related='production_id.weight_gram', digits="Stock Weight")

    @api.depends('production_id', 'production_id.state',
                 'workcenter_id', 'workcenter_id.costs_hour',
                 'operation_id', 'operation_id.name')
    def _compute_operation_info(self):
        for rec in self:
            if rec.production_id and rec.production_id.state not in ['done', 'cancel']:
                rec.update({
                    'operation_name':  rec.operation_id.name,
                    'costs_hour': rec.workcenter_id.costs_hour
                })

    def _compute_is_change_date(self):
        is_change_date = False
        if self.env.user.has_group('pcp_security.can_change_date_on_mo_wo'):
            is_change_date = True
        for rec in self:
            rec.is_change_date = is_change_date

    def do_finish(self):
        """
        Override to return action
        """
        action = self.record_production()
        return action

    def _update_finished_move(self):
        """
        Override _update_finished_move function for create new move line on transfer when update finished move line.
        """
        production_id = self.production_id
        production_move = production_id.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id and
            move.state not in ('done', 'cancel')
        )

        # PC-142: Search stock_moves on finished transfer of MO
        pcp_warehouse = self.env.ref('stock.warehouse0')
        stock_location = self.env.ref('pcp_base.stock_location_stock_wfp')
        if production_id.picking_type_id.warehouse_id == pcp_warehouse:
            stock_location = self.env.ref('stock.stock_location_stock')
        picking_move = production_id.picking_ids.mapped('move_ids_without_package').filtered(
            lambda move: move.location_dest_id.id == stock_location.id and
                         move.product_id.id == self.product_id.id and
                         move.state not in ('done', 'cancel')
        )

        if production_move and production_move.product_id.tracking != 'none':
            if not self.finished_lot_id:
                raise UserError(_('You need to provide a lot for the finished product.'))
            move_line = production_move.move_line_ids.filtered(
                lambda line: line.lot_id.id == self.finished_lot_id.id
            )
            if move_line:
                if self.product_id.tracking == 'serial':
                    raise UserError(_('You cannot produce the same serial number twice.'))
                move_line.product_uom_qty += self.qty_producing
                move_line.qty_done += self.qty_producing
            else:
                location_dest_id = production_move.location_dest_id._get_putaway_strategy(self.product_id).id or production_move.location_dest_id.id
                move_line = move_line.create({
                    'move_id': production_move.id,
                    'product_id': production_move.product_id.id,
                    'lot_id': self.finished_lot_id.id,
                    'product_uom_qty': self.qty_producing,
                    'product_uom_id': self.product_uom_id.id,
                    'qty_done': self.qty_producing,
                    'location_id': production_move.location_id.id,
                    'location_dest_id': location_dest_id,
                })

            # PC-142: Update quantity for move line on finished transfer when updating quantity for finished_move on MO
            if picking_move:
                picking_move._update_quantity_by_move_line(move_line)
        else:
            rounding = production_move.product_uom.rounding
            production_move._set_quantity_done(
                float_round(self.qty_producing, precision_rounding=rounding)
            )

            # PC-142: Update quantity for move line on finished transfer when updating quantity for finished_move on MO
            if picking_move:
                picking_move._set_quantity_done(float_round(self.qty_producing, precision_rounding=picking_move.product_uom.rounding))

    def record_production(self):
        """
        Override to return action
        """
        # PC-213: Update lot name when validating the finished product on the last WO
        if self.finished_lot_id and self.is_last_step:
            self.finished_lot_id._update_lot_name(self.workcenter_code or '')

        self.env["license.plate"].update_quantity_license_plate(self)
        res = super(MrpWorkOrder, self).record_production()
        if self.next_work_order_id:
            action = {
                'type': 'ir.actions.client',
                'tag': 'history_back_action'
            }
        else:
            action = self.open_manufacturing_order()
        return action

    def open_manufacturing_order(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
            'res_id': self.production_id.id,
            'target': 'main',
        }
        return action
