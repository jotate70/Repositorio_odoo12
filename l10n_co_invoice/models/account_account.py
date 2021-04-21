# -*- coding: utf-8 -*-

from odoo import models, fields,api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_debit_id = fields.Many2one('account.account', string=u'Cuenta Débito / Fact.Cliente')

    @api.onchange('type_third_parties')
    def _onchange_type_third_parties(self):
        if self.type_third_parties!='customer':
            self.account_debit_id = False