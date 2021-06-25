from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_assigned_so_email_to_sales_person = fields.Boolean(string='Send assigned Sales order email to Salesperson',
                                                            related='company_id.send_assigned_so_email_to_sales_person',
                                                            readonly=False)
