# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class QualityCheck(models.Model):
    _inherit = "quality.check"

    note_checks = fields.Html("Note")

    @api.model
    def create(self, vals):
        res = super(QualityCheck, self).create(vals)
        res.note_checks = res.note
        return res


class QualityAlertTeam(models.Model):
    _inherit = "quality.alert.team"

    def _compute_check_count(self):
        """
        Override function to don't show the quality checks of Work Orders
        """
        # PC-199: Add the condition ('workorder_id', '=', False) to domain when searching quality checks
        check_data = self.env['quality.check'].read_group(
            [('team_id', 'in', self.ids), ('quality_state', '=', 'none'), ('workorder_id', '=', False)],
            ['team_id'], ['team_id'])
        check_result = dict((data['team_id'][0], data['team_id_count']) for data in check_data)
        for team in self:
            team.check_count = check_result.get(team.id, 0)
