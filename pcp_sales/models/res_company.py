from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    send_assigned_so_email_to_sales_person = fields.Boolean(string='Send assigned Sales order email to Salesperson', default=True)
