# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    def action_generate_serial(self):
        """
        Override to add name when generating lot.
        """
        self.ensure_one()
        lot_name = self.env['stock.production.lot'].with_context(create_finished_product_lot=True).generate_lot_name()
        self.finished_lot_id = self.env['stock.production.lot'].create({
            'name': lot_name,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
        })

    def open_tablet_view(self):
        self.ensure_one()
        if not self.is_user_working and self.working_state != 'blocked' and self.state in ('ready', 'progress'):
            self.button_start()
        # Generate LOT# when starting the 1st Work Order
        is_first_work_order = self.check_is_first_work_order()
        if is_first_work_order and self.product_tracking != 'none' and not self.finished_lot_id and self.state in ('ready', 'progress'):
            self.action_generate_serial()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('mrp_workorder.mrp_workorder_view_form_tablet').id, 'form']],
            'res_id': self.id,
            'target': 'fullscreen',
            'flags': {
                'withControlPanel': False,
                'form_view_initial_mode': 'edit',
            },
        }

    def check_is_first_work_order(self):
        self.ensure_one()
        is_first_work_order = False
        workorder_ids = self.production_id.workorder_ids.sorted(lambda w: w.id)
        if self == workorder_ids[0]:
            is_first_work_order = True

        return is_first_work_order
