# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class disburse_amt_wiz(models.TransientModel):
    _name = 'disburse.amt.wiz'

    cheque_no = fields.Char(string="Cheque Number", required=True, size=10)
    journal_id = fields.Many2one('account.journal', string="Journal", required=True)

    @api.multi
    def disburse(self):
        adv_req_id = self.env['hr.advance.salary.request'].sudo().browse(self._context.get('active_id'))
        move_line = []
#         journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        payable_acc_id = self.env['account.account'].search([('user_type_id.type', '=', 'payable')], limit=1)
        rec_acc_id = self.env['account.account'].search([('user_type_id.type', '=', 'receivable')], limit=1)
#         if not selfjournal_id:
#             raise UserError(_('Please create the journal for bank type.'))
        move_line.append((0, 0, {'account_id': rec_acc_id.id,
                                 'name': '/',
                                 'debit': adv_req_id.approved_amt,
                                 'credit': 0
                                 }))
        move_line.append((0, 0, {'account_id': payable_acc_id.id,
                                 'name': '/',
                                 'debit': 0,
                                 'credit': adv_req_id.approved_amt
                                 }))
        move_id = self.env['account.move'].create({
                                                 'journal_id': self.journal_id.id,
                                                 'ref': adv_req_id.name,
                                                 'line_ids': move_line,
                                                 'cheque_ref': self.cheque_no
                                                  })
        move_id.post()
        
        adv_req_id.sudo().write({
                                 'state': 'paid', 
                                 'move_id': move_id.id, 
                                 'disburse_date':  date.today()
                                 })
        return True
        
    _sql_constraints = [('cheque_no_uniq', 'unique(cheque_no)',
                     'Cheque Number should be unique.')]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: