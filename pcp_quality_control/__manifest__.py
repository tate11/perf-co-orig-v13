# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Quality Control",
    "summary": "Performance Co-Packing Quality Control",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base", "quality_control",
    ],
    "data": [
        # ============================== VIEWS ================================
        "views/quality_views.xml",

        # ============================== TEMPLATES ============================

        # ============================== REPORT ===============================

        # ============================== WIZARDS ==============================
        'wizard/generate_quality_control_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
