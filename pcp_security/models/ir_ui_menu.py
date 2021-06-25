# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def create(self, values):
        """
        Override to assign group to new root menu
        """
        if not values.get('parent_id', False):
            group = self.env['res.groups'].create({
                'name': 'Can see {}'.format(values['name']),
                'category_id': self.env.ref('pcp_security.module_category_pcp').id
            })
            if group:
                values['groups_id'] = [(6, 0, group.ids)]
                erp_group = self.env.ref('base.group_erp_manager')
                if erp_group:
                    erp_group.write({'implied_ids': [(4, group.id)]})

        return super(IrUiMenu, self).create(values)
