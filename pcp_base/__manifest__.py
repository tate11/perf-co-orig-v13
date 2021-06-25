# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    "name": "Performance Co-Packing: Base",
    "summary": "Performance Co-Packing Base",
    "version": "13.0.1.0.0",
    "website": "https://novobi.com",
    "author": "Novobi, LLC",
    "license": "OPL-1",
    "depends": [
        "contacts", "crm", "purchase", "sale_management",
        "account_accountant",
        "quality_control",
        "sale_margin",
        "inter_company_rules", "mrp_subcontracting",
        "stock_barcode", "mrp_workorder",

        # OCA Modules
        "partner_fax", "partner_phone_extension",
        "base_user_role"
    ],
    "data": [
        # ============================== DATA =================================
        'data/res_company_data.xml',
        'data/ir_model_data.xml',
        'data/uom_uom_data.xml',

        # ============================== MENU =================================

        # ============================== VIEWS ================================
        'views/res_users_views.xml',
        # ============================== SECURITY =============================

        # ============================== TEMPLATES =============================

        # ============================== REPORT =============================

        # ============================== WIZARDS =============================

    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
