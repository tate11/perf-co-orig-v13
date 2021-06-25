from . import models
from . import wizard
from odoo.api import Environment, SUPERUSER_ID


def modify_lot_sequence(env):
    lot_sequence = env.ref('stock.sequence_production_lots')
    if lot_sequence:
        lot_sequence.write({
            'name': 'Lot number for receiving product',
            'prefix': '%(y)s%(doy)s-',
            'padding': 3
        })


def set_default_for_picking_type(env):
    receipt_picking_types = env['stock.picking.type'].search([('code', '=', 'incoming')])
    for picking_type in receipt_picking_types:
        picking_type.write({
            'use_create_lots': True,
            'show_reserved': True,
            'auto_create_lot': True,
        })


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    modify_lot_sequence(env)
    set_default_for_picking_type(env)
