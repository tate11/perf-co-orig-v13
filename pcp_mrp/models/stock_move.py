# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _calculate_extra_account_move_line(self, data_dict, partner_id, qty, debit_value, credit_value,
                                           debit_account_id, credit_account_id, description):
        """
        Can be overridden in different projects.
        """
        CostStructure = self.env['report.mrp_account_enterprise.mrp_cost_structure']
        production_id = self.production_id

        # MO is finished
        if production_id and not self.scrap_ids and not self.scrapped:
            operation_account_id = self.product_id.categ_id.property_expense_account_operation_cost_categ_id
            if not operation_account_id:
                raise UserError(_(
                    'You don\'t have Expense Account - Cost of Operations defined on your product category. You must define one before processing this operation.'))

            data = CostStructure.get_lines(production_id)

            total_workcenter_cost = 0
            for line in data:
                if line['product'] == self.product_id:
                    total_workcenter_cost = line.get('total_workcenter_cost', 0.0)
                    break

            if not float_is_zero(total_workcenter_cost, precision_digits=2):
                data_dict = self._append_account_move_line(data_dict, partner_id, qty, total_workcenter_cost,
                                                           credit_account_id, operation_account_id.id, description)

            # MO's move for Final Product should have at most 1 dest_move, if generated from PO
            dest_moves = self.move_dest_ids
            if dest_moves and dest_moves[0].purchase_line_id:
                purchase_line = dest_moves[0].purchase_line_id
                product_cost = purchase_line.price_unit * qty
                interim_received_acc_id = self.product_id.categ_id.property_stock_account_input_categ_id

                """ MO Journal Entry
                OOTB
                Account                                     | Debit | Credit
                -----------------------------------------------------------------------------------
                WIP                                         |       | Component Cost + PO Cost
                -----------------------------------------------------------------------------------
                Stock Valuation                             | Component Cost + PO Cost  |
                -----------------------------------------------------------------------------------

                We add these lines:
                -----------------------------------------------------------------------------------
                WIP                                         | PO Cost |
                -----------------------------------------------------------------------------------
                101130 Stock Interim Account (Received)     |         | PO Cost
                -----------------------------------------------------------------------------------
                """
                if not float_is_zero(product_cost, precision_digits=2):
                    data_dict = self._append_account_move_line(data_dict, partner_id, qty, product_cost,
                                                               credit_account_id, interim_received_acc_id.id, description)

        return data_dict

    def _prepare_common_svl_vals(self):
        vals = super()._prepare_common_svl_vals()
        if self.production_id and self.move_dest_ids and self.move_dest_ids[0].purchase_line_id:
            vals['stock_move_id'] = self.id
        else:
            if self.move_dest_ids and self.move_dest_ids[0].is_subcontract:
                vals['stock_move_id'] = self.move_dest_ids[0].id
        return vals

    def _update_quantity_by_move_line(self, move_line):
        self.ensure_one()
        if not move_line:
            return True
        to_update_line = self.move_line_ids.filtered(
            lambda line: line.lot_id.id == move_line.lot_id.id
        )
        if to_update_line:
            move_line.product_uom_qty = 0
            move_line.qty_done = move_line.qty_done
        else:
            # TODO: Search location_dest_id by putaway strategy rule
            # self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
            to_update_line.create({
                'move_id': self.id,
                'picking_id': self.picking_id.id,
                'product_id': self.product_id.id,
                'lot_id': move_line.lot_id.id,
                'product_uom_qty': 0,
                'product_uom_id': move_line.product_uom_id.id,
                'qty_done': move_line.qty_done,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        return True


from odoo.addons.stock_account.models.stock_move import StockMove as OriginalStockMove


def _get_out_move_lines(self):
    """ Returns the `stock.move.line` records of `self` considered as outgoing. It is done thanks
    to the `_should_be_valued` method of their source and destionation location as well as their
    owner.

    :returns: a subset of `self` containing the outgoing records
    :rtype: recordset
    """
    res = self.env['stock.move.line']
    for move_line in self.move_line_ids:
        # PCP-266: Ignore the condition to show all move on the cost analysis report
        # if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
        #     continue
        if move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
            res |= move_line
    return res

OriginalStockMove._get_out_move_lines = _get_out_move_lines
