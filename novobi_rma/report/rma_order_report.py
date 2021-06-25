# Copyright © 2020 Novobi, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo import tools


class RMAOrderReport(models.Model):
    """ RMA Order Report"""

    _name = "rma.order.report"
    _auto = False
    _description = "RMA Order Report"

    user_id = fields.Many2one('res.users', string='User', readonly=True)
    team_id = fields.Many2one('crm.team', string='Team', readonly=True)
    nbr = fields.Integer(string='# of RMAs', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    create_date = fields.Datetime(string='Create Date', readonly=True, index=True)
    rma_order_date = fields.Datetime(string='RMA Date', readonly=True)
    delay_close = fields.Float(string='Delay to close', digits=(16, 2), readonly=True, group_operator="avg",
                               help="Number of Days to close the case")
    state = fields.Selection([
                            ('draft', 'New'),
                            ('open', 'In Progress'),
                            ('return', 'Waiting for Return'),
                            ('delivery', 'Waiting for Delivery'),
                            ('repair', 'Waiting for Repair'),
                            ('payment', 'Waiting for Payment'),
                            ('cancel', 'Rejected'),
                            ('done', 'Settled')
                         ],'Status', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], string='Priority')
    type = fields.Selection([
        ('return', 'Return'),
        ('exchange', 'Exchange')]
        , default='return', string='Type', required=True)
    rma_order_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier')],
        string='Partner Type', required=True, default='customer',
        help="customer = from customer to company ; supplier = from company to supplier")
    date_closed = fields.Datetime('Close Date', readonly=True, index=True)
    date_deadline = fields.Date('Deadline', readonly=True, index=True)
    delay_expected = fields.Float('Overpassed Deadline', digits=(16, 2), readonly=True, group_operator="avg")
    email = fields.Integer('# Emails', size=128, readonly=True)
    subject = fields.Char('Subject', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM  %s 
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
            SELECT
                min(c.id) as id,
                c.date as rma_order_date,
                c.date_closed as date_closed,
                c.date_deadline as date_deadline,
                c.user_id,
                c.state as state,
                c.team_id,
                c.partner_id,
                c.company_id,
                c.name as subject,
                count(*) as nbr,
                c.priority as priority,
                c.create_date as create_date,
                c.type as type,
                c.rma_order_type as rma_order_type,
                avg(extract('epoch' from (c.date_closed-c.create_date)))/(3600*24) as  delay_close,
                (SELECT count(id) FROM mail_message WHERE model='rma.order' AND res_id=c.id) AS email,
                extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24) as  delay_expected
        """
        return select_str

    def _from(self):
        from_str = """rma_order c"""
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                c.date,
                c.user_id,
                c.team_id,
                c.state,
                c.partner_id,
                c.company_id,
                c.create_date,
                c.priority,
                c.date_deadline,
                c.date_closed,
                c.id,
                c.type,
                c.rma_order_type
        """
        return group_by_str
