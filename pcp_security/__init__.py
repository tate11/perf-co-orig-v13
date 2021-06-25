from . import models
from odoo.api import Environment, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    menus = env['ir.ui.menu'].search([('parent_id', '=', False), ('name', 'not in', ['Settings', 'Apps'])])
    for menu in menus:
        group = env['res.groups'].create({
            'name': 'Can see {}'.format(menu.name),
            'category_id': env.ref('pcp_security.module_category_pcp').id
        })
        if group:
            menu.write({'groups_id': [(6, 0, group.ids)]})
            erp_group = env.ref('base.group_erp_manager')
            if erp_group:
                erp_group.write({'implied_ids': [(4, group.id)]})


def uninstall_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})

    groups = env['res.groups'].search([('category_id', '=', env.ref('pcp_security.module_category_pcp').id)])
    groups.unlink()
