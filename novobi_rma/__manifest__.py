# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Novobi RMA',
    'summary':'Return Merchandise authorization',
    'version': '1.0',
    'category': 'Custom',
    'author': "Novobi LLC",
    'website': "https://novobi.com",
    'license': 'OPL-1',
    'description': """
Return Merchandise authorization.
=======================
This application allows you to track your customers/vendors claims and grievances.
""",
    'depends': [
        'crm',
        'sale',
        'purchase',
        'stock',
        'repair',
    ],
    'data': [
        # ============================== SECURITY =============================
        'security/novobi_rma_security.xml',
        'security/ir.model.access.csv',

        # ============================== DATA =================================
        'data/ir_sequence_data.xml',

        # ============================== VIEWS ================================
        'views/rma_order_views.xml',
        'views/rma_order_reason_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/stock_picking_views.xml',
        'views/repair_views.xml',

        # ============================== REPORT =============================
        'report/rma_order_report_views.xml',
        # ============================== MENU =============================
        'views/menuitem.xml',

        # ============================== WIZARDS =============================
        'wizard/stock_picking_return_views.xml',
        'wizard/account_move_reversal_views.xml',
        'wizard/wizard_create_picking_views.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
