# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from pytz import timezone, utc
from datetime import datetime
from odoo import api, models, fields, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def button_generate_lp_number(self):
        self.ensure_one()
        action = self.env.ref('pcp_stock.generate_license_plate_action').read()[0]
        action['context'] = {
            'default_lot_id': self.id,
            'default_type': 'production',
            'default_qty_done': self.product_qty,
            'default_product_qty': self.product_qty,
        }

        return action

    def button_open_license_plate(self):
        action = self.env.ref('pcp_stock.license_plate_action').read()[0]
        action['domain'] = [('lot_id', 'in', self.ids)]
        return action

    def generate_lot_name(self, code=None):
        ir_sequence_env = self.env['ir.sequence']
        if self._context.get('create_finished_product_lot'):
            lot_name = ir_sequence_env.next_by_code('finished.product.lot')
            code = code or self._context.get('code', '')
            lot_name = self.update_lot_name_for_finished_product(lot_name, code, update_time=False)
        else:
            lot_name = ir_sequence_env.next_by_code('stock.lot.serial')
            lot_name = self.update_lot_name_for_receiving_product(lot_name, code)
        return lot_name

    name = fields.Char(default=generate_lot_name)

    def _update_lot_name(self, code, update_time=True):
        self.ensure_one()
        new_lot_name = self.update_lot_name_for_finished_product(self.name, code, update_time)
        if new_lot_name:
            self.write({'name': new_lot_name})

    def update_lot_name_for_finished_product(self, lot_name, workcenter_code, update_time):
        new_lot_name = lot_name
        lot_name = lot_name[:lot_name.find('#')]
        index = lot_name.find(' ')
        if index >= 0:
            military_time = lot_name[index + 1:]
            if update_time:
                tz = self.env.user.tz and timezone(self.env.user.tz) or utc
                military_time = datetime.now(tz=tz).strftime('%H:%M')

            if workcenter_code:
                new_lot_name = '%s-%s %s' % (lot_name[0: index], workcenter_code, military_time)
            else:
                new_lot_name = '%s %s' % (lot_name[0: index], military_time)
        return new_lot_name

    def update_lot_name_for_receiving_product(self, lot_name, partner_code):
        new_lot_name = lot_name
        if partner_code is None:
            partner_code = self.env.company.partner_id.short_code or ''

        if partner_code:
            new_lot_name = '%s-%s' % (lot_name, partner_code)
        return new_lot_name
