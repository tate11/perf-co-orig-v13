# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Inter Company Rules",
    "summary": "Performance Co-Packing Inter Company Rules",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base",
        "pcp_stock"
    ],
    "data": [
        # ============================== VIEWS ================================
        "views/purchase_order_views.xml",
        "views/sale_order_views.xml",

        # ============================== TEMPLATES ============================

        # ============================== REPORT ===============================

        # ============================== WIZARDS ==============================
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
