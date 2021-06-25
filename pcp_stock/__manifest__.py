# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Stock",
    "summary": "Performance Co-Packing Stock",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base",
        "stock_picking_auto_create_lot",
    ],
    "data": [
        # ============================== DATA =================================
        'data/ir_cron_data.xml',
        'data/stock_sequence_data.xml',

        # ============================== VIEWS ================================
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'views/picking_templates.xml',
        'views/product_template_views.xml',
        'views/uom_uom_views.xml',
        'views/stock_move_line_views.xml',
        'views/license_plate_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_inventory_line_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_production_lot_views.xml',
        'views/stock_barcode_lot_view.xml',
        'views/tree_views_limiting.xml',

        # ============================== SECURITY ============================
        'security/ir.model.access.csv',

        # ============================== TEMPLATES ============================


        # ============================== REPORT ===============================
        'report/license_plate_report.xml',

        # ============================== WIZARDS ==============================
        'wizard/generate_license_plate_view.xml',

    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
