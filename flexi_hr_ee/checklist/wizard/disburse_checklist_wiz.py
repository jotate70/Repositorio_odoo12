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
from datetime import datetime,date


class disburse_checklist_wiz(models.Model):
    _name = 'disburse.checklist.wiz'

    cheque_no = fields.Char(string="Cheque Number", required=True, size=10)

    @api.multi
    def disburse(self):
        emp_product_id = self.env['emp.product.line'].browse(self._context.get('active_id'))
        if emp_product_id.payment_by == 'cheque':
            move_line = []
            journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
            payable_acc_id = self.env['account.account'].search([('user_type_id.type','=', 'payable')], limit=1)
            rec_acc_id = self.env['account.account'].search([('user_type_id.type','=', 'receivable')], limit=1)
            if not journal_id and not self._context.get('journal_id'):
                raise UserError(_('Please create the journal for bank type.'))
            move_line.append((0, 0, {'account_id': rec_acc_id.id,
                                     'name': '/',
                                     'debit': emp_product_id.charged_amt,
                                     'credit': 0}))
            move_line.append((0, 0, {'account_id': payable_acc_id.id,
                                     'name': '/',
                                     'debit': 0,
                                     'credit': emp_product_id.charged_amt}))
            move_id = self.env['account.move'].create({
                                                 'journal_id': self._context.get('journal_id') if self._context.get('journal_id') else journal_id,
                                                 'ref': emp_product_id.product_exit_id.name,
                                                 'line_ids': move_line,
                                                 'cheque_ref': self.cheque_no
                                                })
            move_id.post()
            emp_product_id.write({'state': 'paid', 'move_id': move_id.id, 'disburse_date':  date.today()})
            return True

    _sql_constraints = [('cheque_no_uniq', 'unique(cheque_no)',
                     'Cheque Number should be unique.')]