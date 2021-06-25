# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Security",
    "summary": "Performance Co-Packing Security",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "pcp_base"
    ],
    "data": [
        # ============================== DATA =================================
        # ============================== MENU =================================
        # ============================== SECURITY =============================
        'security/ir.model.access.csv',
        'security/pcp_security.xml',
        'security/uom_uom_views.xml',
        # ============================== VIEWS ================================

        # ============================== TEMPLATES ============================

        # ============================== REPORT ===============================

        # ============================== WIZARDS ==============================

    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook'
}
