# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    short_code = fields.Char('Short Code')

    def get_owner_id(self, company_id):
        """
        Get the 'owner_id' field from the 'technical_owner_id' field
        :param self: technical_owner_id
        :param company_id: the company of record. If not, get current company of the user.
        :return: owner_id
        """
        self.ensure_one()
        if not company_id:
            company = self.env.company
        else:
            company = self.env['res.company'].browse(company_id)
        partner = company.partner_id

        real_owner_id = False
        if self != partner:
            real_owner_id = self
        return real_owner_id

    def get_technical_owner_id(self, company_id):
        """
        Get the 'technical_owner_id' field from the 'owner_id' field of ODOO
        :param self: owner_id field of ODOO
        :param company_id: the company of record. If not, get current company of the user.
        :return: technical_owner_id
        """
        if not company_id:
            company = self.env.company
        else:
            company = self.env['res.company'].browse(company_id)
        partner = company.partner_id

        technical_owner_id = self
        if not technical_owner_id:
            technical_owner_id = partner
        return technical_owner_id

    def _update_owner_id(self, values, owner_str, technical_owner_str, company_id):
        if values.get(technical_owner_str):
            technical_owner = self.browse(values[technical_owner_str])
            owner_id = technical_owner.get_owner_id(company_id)
            values.update({owner_str: owner_id and owner_id.id or False})
        elif owner_str in values:
            old_owner = self.browse(values[owner_str])
            technical_owner = old_owner.get_technical_owner_id(company_id)
            new_owner = technical_owner.get_owner_id(company_id)
            values.update({
                owner_str: new_owner and new_owner.id or False,
                technical_owner_str: technical_owner and technical_owner.id or False,
            })
        return values