# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: MRP",
    "summary": "Performance Co-Packing MRP",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base",
    ],
    "data": [
        # ============================== DATA =================================
        # ============================== MENU =================================
        # ============================== SECURITY =============================
        "security/ir.model.access.csv",

        # ============================== VIEWS ================================
        'views/assets.xml',
        'views/sage_stock_move_views.xml',
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_routing_views.xml',
        'views/mrp_workorder_views.xml',
        'views/stock_picking_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/product_template_views.xml',

        # ============================== TEMPLATES ============================

        # ============================== REPORT ===============================
        'reports/mrp_production_templates.xml',
        'reports/cost_structure_report.xml',

        # ============================== WIZARDS ==============================
        'wizard/mrp_product_produce_views.xml',

    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
