# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    @api.model
    def _search_record_to_update_xmlids(self, data_list):
        res_model = data_list[0]["res_model"]
        res_model_env = self.env[res_model]
        data_lst = []
        for data in data_list[1:]:
            record_id = None
            if res_model == "stock.warehouse":
                record_id = res_model_env.search([('code', '=', data["code"])], limit=1)
            elif res_model == "stock.location":
                company_id = self.env.ref(data["company_id"])
                record_id = res_model_env.search([('name', '=', data["name"]), ('company_id', '=', company_id.id)], limit=1)
            elif res_model == "stock.picking.type":
                warehouse_id = self.env.ref(data["warehouse_id"])
                record_id = res_model_env.search([('code', '=', data["code"]), ('warehouse_id', '=', warehouse_id.id)],
                                                 limit=1)

            if record_id:
                data.update({'record': record_id})
                data_lst.append(data)
                
        self._update_xmlids(data_lst)
