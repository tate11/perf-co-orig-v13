from odoo import http, _
from odoo.http import request
from odoo.addons.stock_barcode.controllers.main import StockBarcodeController


class CustomStockBarcodeController(StockBarcodeController):

    @http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        """ Receive a barcode scanned from the main menu and return the appropriate
            action (open an existing / new picking) or warning.
        """
        ret_open_lp = self.try_open_license_plate(barcode)
        if ret_open_lp:
            return ret_open_lp
        else:
            return super(CustomStockBarcodeController, self).main_menu(barcode, **kw)

    def try_open_license_plate(self, barcode):
        """ If barcode represent a license plate, open a current license plate"""

        lp = request.env['license.plate'].search([('name', '=', barcode)], limit=1)
        if lp:
            view_id = request.env.ref('pcp_stock.license_plate_form').id
            return {
                'action': {
                    'name': _('Open picking form'),
                    'res_model': 'license.plate',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'res_id': lp.id,
                }
            }
        return False

    @http.route('/pcp_picking_barcode/scan_from_list', type='json', auth='user')
    def scan_from_list(self, barcode):
        lp = request.env['license.plate'].search([('name', '=', barcode)], limit=1)
        if lp:
            return {
                'action': {
                    'name': _('Open picking form'),
                    'res_model': 'license.plate',
                    'view_mode': 'form',
                    'view_id': False,
                    'views': [(False, 'form')],
                    'type': 'ir.actions.act_window',
                    'res_id': lp.id,
                }
            }
        else:
            return False
