# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    technical_owner_id = fields.Many2one('res.partner', 'Owner', check_company=True)

    @api.model
    def create(self, values):
        values = self.update_owner_id(values)
        return super(StockInventoryLine, self).create(values)

    def write(self, values):
        values = self.update_owner_id(values)
        return super(StockInventoryLine, self).write(values)

    def update_owner_id(self, values):
        current_company_id = self and self.mapped('company_id').id or False
        if not current_company_id and 'inventory_id' in values:
            inventory_id = self.env['stock.inventory'].browse(values['inventory_id'])
            current_company_id = inventory_id and inventory_id.company_id.id or False

        values = self.env['res.partner']._update_owner_id(
            values, owner_str='partner_id', technical_owner_str='technical_owner_id', company_id=current_company_id)
        return values
