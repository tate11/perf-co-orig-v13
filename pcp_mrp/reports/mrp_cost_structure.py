# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import float_is_zero


class MrpCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'
    _description = 'MRP Cost Structure Report'

    def get_lines(self, productions):
        """
        Overwrite function to the operation name and cost/hour will be static after the MO done (PC-156)
        """
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        cost_digits = self.env['decimal.precision'].precision_get('Product Price')
        res = []
        for product in productions.mapped('product_id'):
            mos = productions.filtered(lambda m: m.product_id == product)
            total_cost = 0.0

            # Get the cost of operations
            operations = []
            total_workcenter_cost = 0.0
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            if Workorders:
                # PC-156: Get Operation name and cost/hour from Work Order instead of MRP Routing Workcenter and Workcenter
                query_str = """SELECT w.operation_id, w.operation_name, partner.name, sum(t.duration), w.costs_hour
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                LEFT JOIN res_users u ON (t.user_id = u.id)
                                LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
                                LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                                GROUP BY w.operation_id, w.operation_name, partner.name, t.user_id, w.costs_hour
                                ORDER BY w.operation_name, partner.name
                            """
                self.env.cr.execute(query_str, (tuple(Workorders.ids), ))
                for op_id, op_name, user, duration, cost_hour in self.env.cr.fetchall():
                    duration = duration or 0.0
                    cost_hour = cost_hour or 0.0
                    operations.append([user, op_id, op_name, duration / 60.0, cost_hour])
                    total_workcenter_cost += duration / 60.0 * cost_hour

            # Get the cost of raw material effectively used
            raw_material_moves = []
            query_str = """SELECT sm.product_id, sm.bom_line_id, abs(SUM(svl.quantity)), abs(SUM(svl.value))
                             FROM stock_move AS sm
                       INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                            WHERE sm.raw_material_production_id in %s AND sm.state != 'cancel' AND sm.product_qty != 0 AND scrapped != 't'
                         GROUP BY sm.bom_line_id, sm.product_id
                         ORDER BY sm.bom_line_id"""
            self.env.cr.execute(query_str, (tuple(mos.ids), ))
            product_dict = {}
            index = 1
            for product_id, bom_line_id, qty, cost in self.env.cr.fetchall():
                product_index = product_dict.get(product_id)
                if product_index and float_is_zero(cost, precision_digits=cost_digits):
                    material_data = raw_material_moves[product_index - 1]
                    material_data['qty'] += qty
                else:
                    product_dict[product_id] = index
                    raw_material_moves.append({
                        'qty': qty,
                        'cost': cost,
                        'product_id': ProductProduct.browse(product_id),
                        'bom_line_id': bom_line_id
                    })
                    index += 1
                total_cost += cost

            # Get the cost of scrapped materials
            scraps = StockMove.search([('production_id', 'in', mos.ids), ('scrapped', '=', True), ('state', '=', 'done')])
            uom = mos and mos[0].product_uom_id
            mo_qty = 0
            if not all(m.product_uom_id.id == uom.id for m in mos):
                uom = product.uom_id
                for m in mos:
                    qty = sum(m.move_finished_ids.filtered(lambda mo: mo.state == 'done' and mo.product_id == product).mapped('product_qty'))
                    if m.product_uom_id.id == uom.id:
                        mo_qty += qty
                    else:
                        mo_qty += m.product_uom_id._compute_quantity(qty, uom)
            else:
                for m in mos:
                    mo_qty += sum(m.move_finished_ids.filtered(lambda mo: mo.state == 'done' and mo.product_id == product).mapped('product_qty'))
            for m in mos:
                byproduct_moves = m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id != product)

            # Get cost of subcontracting
            # TODO: should get subcontractor name and handle multi MOs
            packaging_fee = []
            po_cost = 0.0
            for m in mos:
                move_finished_ids = m.move_finished_ids.filtered(lambda mo: mo.state == 'done' and mo.product_id == product)
                quantity_done = sum(move_finished_ids.mapped('product_qty'))
                dest_moves = move_finished_ids.mapped('move_dest_ids')
                if dest_moves and dest_moves[0].purchase_line_id:
                    purchase_line = dest_moves[0].purchase_line_id
                    operator = purchase_line.order_id.partner_id.name
                    subcontracting_cost = m.extra_cost * quantity_done
                    packaging_fee = [operator, subcontracting_cost]
                    po_cost += subcontracting_cost

            res.append({
                'product': product,
                'mo_qty': mo_qty,
                'mo_uom': uom,
                'operations': operations,
                'currency': self.env.company.currency_id,
                'raw_material_moves': raw_material_moves,
                'total_cost': total_cost,
                'po_cost': po_cost,
                'total_workcenter_cost': total_workcenter_cost,
                'scraps': scraps,
                'packaging_fee': packaging_fee,
                'mocount': len(mos),
                'byproduct_moves': byproduct_moves,
            })
        return res

#     # Get the labor cost
#     query_str = """SELECT w.operation_id, op.name, partner.name, sum(t.duration), p.employee_rate
#                    FROM mrp_workcenter_productivity t
#                                     LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
#                                     LEFT JOIN mrp_production p ON (p.id = w.production_id)
#                                     LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
#                                     LEFT JOIN res_users u ON (t.user_id = u.id)
#                                     LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
#                                     LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
#                    WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s AND p.id IS NOT NULL
#                    GROUP BY w.operation_id, op.name, partner.name, t.user_id, p.employee_rate
#                    ORDER BY op.name, partner.name
#                 """
#     self.env.cr.execute(query_str, (tuple(workorders.ids),))
#     for op_id, op_name, user, duration, employee_rate in self.env.cr.fetchall():
#         labors.append([user, op_id, op_name, duration / 60.0, employee_rate])
#         total_labor_cost += duration / 60.0 * employee_rate
#
#
# for line in res:
#     if line['product'].id == product.id:
#         line['labors'] = labors
#         line['operations'] = operations
#         line['total_labor_cost'] = total_labor_cost
#         line['total_workcenter_cost'] = total_workcenter_cost