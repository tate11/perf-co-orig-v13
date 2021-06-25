# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Sales",
    "summary": "Performance Co-Packing Sales",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base", "sale_order_type"
    ],
    "data": [
        # ============================== VIEWS ================================
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "views/account_move_views.xml",
        'views/res_config_settings_views.xml',

        # ============================== TEMPLATES ============================

        # ============================== REPORT ===============================
        'report/sale_order_report_templates.xml',
        'report/stock_picking_report_templates.xml',
        'report/account_move_report_templates.xml',
        'report/bill_of_lading_report.xml',

        # ============================== WIZARDS ==============================
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
