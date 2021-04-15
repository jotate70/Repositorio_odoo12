# coding: utf-8
##################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)          #
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.                     #
# All Rights Reserved.                                                           #
#                                                                                #
# This program is copyright property of the author mentioned above.              #
# You can`t redistribute it and/or modify it.                                    #
#                                                                                #
##################################################################################

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    debit_account_id = fields.Many2one('account.account', string="Travel Expenses Debit Account")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'debit_account_id': int(self.env['ir.config_parameter'].sudo().get_param('debit_account_id')) or False
        })
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('debit_account_id', int(self.debit_account_id.id))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: