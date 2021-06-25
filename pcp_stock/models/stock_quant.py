# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    technical_owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help='This is the owner of the quant', check_company=True)

    @api.model
    def create(self, values):
        values = self.update_owner_id(values)
        res = super(StockQuant, self).create(values)
        return res

    def update_owner_id(self, values):
        current_company_id = self and self.mapped('company_id').id or False
        if not current_company_id and values.get('location_id'):
            location_id = self.env['stock.location'].browse(values['location_id'])
            current_company_id = location_id and location_id.company_id.id or False

        values = self.env['res.partner']._update_owner_id(
            values, owner_str='owner_id', technical_owner_str='technical_owner_id', company_id=current_company_id)
        return values

    @api.model
    def _get_inventory_fields_create(self):
        """
            Override function to add technical_owner_id to the list.
            Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        return ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id', 'inventory_quantity', 'technical_owner_id']

    @api.model
    def _get_available_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False):
        ctx_owner_id = self._context.get('owner_id', False)
        if ctx_owner_id:
            owner_id = ctx_owner_id

        return super(StockQuant, self)._get_available_quantity(product_id, location_id, lot_id, package_id, owner_id, strict, allow_negative)
