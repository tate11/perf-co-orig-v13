# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Barcode",
    "summary": "Performance Co-Packing Barcode",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base",
        "pcp_stock",
        "pcp_mrp",
    ],
    "data": [
        # ============================== DATA =================================

        # ============================== MENU =================================

        # ============================== VIEWS ================================
        "views/assets.xml",
        "views/mrp_workorder_views.xml",
        # ============================== SECURITY =============================

        # ============================== TEMPLATES =============================

        # ============================== REPORT =============================

        # ============================== WIZARDS =============================

    ],
    'qweb': [
        "static/src/xml/qweb_templates.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
