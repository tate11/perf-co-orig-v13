# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round

import logging

_logger = logging.getLogger(__name__)


class GenerateQualityControlWizard(models.TransientModel):
    _name = "generate.quality.control"
    _description = "Generate Quality Control Points"
    _inherit = ['quality.point']

    product_categ_id = fields.Many2one('product.category', string='Product Category', required=True)
    measure_frequency_type = fields.Selection([('all', 'All Operations'),
                                               ('random', 'Randomly'),
                                               ('periodical', 'Periodically')], string="Type of Frequency",
                                              default='all', required=True)
    measure_frequency_unit = fields.Selection([
        ('day', 'Days'),
        ('week', 'Weeks'),
        ('month', 'Months')], default="day")
    product_tmpl_id = fields.Many2one('product.template', 'Product', required=False)

    def generate_control_points(self):
        self.ensure_one()
        product_tmpl_ids = self.product_categ_id.product_tmpl_ids.filtered(
            lambda p: p.type in ['consu', 'product'] and (not p.company_id or p.company_id == self.company_id))
        datas = [{
            'active': True,
            'title': self.title,
            'product_tmpl_id': p.id,
            'team_id': self.team_id.id,
            'picking_type_id': self.picking_type_id.id,
            'test_type_id': self.test_type_id.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'measure_frequency_type': self.measure_frequency_type,
            'measure_frequency_value': self.measure_frequency_value,
            'measure_frequency_unit_value': self.measure_frequency_unit_value,
            'measure_frequency_unit': self.measure_frequency_unit,
            'norm': self.norm,
            'tolerance_min': self.tolerance_min,
            'tolerance_max': self.tolerance_max,
            'norm_unit': self.norm_unit,
            'note': self.note,
            'reason': self.reason,
            'failure_message': self.failure_message
        } for p in product_tmpl_ids]

        quality_points = self.env['quality.point'].sudo().create(datas)
        return {
            'name': _('Quality Control Points Created'),
            'view_mode': 'tree,form',
            'res_model': 'quality.point',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', quality_points.ids)],
            'context': {'search_default_groupby_product_template': 1},
            'target': 'current',
        }
