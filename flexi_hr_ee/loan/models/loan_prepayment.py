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
from odoo.exceptions import UserError, ValidationError
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta


class loan_prepayment(models.Model):
    _name = 'loan.prepayment'
    _description = "Loan Prepayment"

    @api.multi
    def draft_post(self):
        if self.amount and self.amount <= 0:
            raise ValidationError(_('Please enter the amount greater than zero'))
        if not self.loan_app_id.bank_acc_id.id or not self.loan_app_id.emp_loan_acc_id.id:
            raise ValidationError(_('Please select bank account and customer account.'))
        loan_payment_paid_ids = self.env['loan.payment'].search([('loan_app_id', '=', self.loan_app_id.id),
                                                            ('state', '=', 'paid')])
        balance_list = []
        if loan_payment_paid_ids:
            for each in loan_payment_paid_ids:
                balance_list.append(each.balance_amt)
        if not balance_list:
            remain_balance = self.loan_app_id.amount
        if balance_list:
            remain_balance = balance_list[-1]
        bal = "%.2f" % (remain_balance)
        if self.amount and self.amount > float(bal):
            raise ValidationError(_('Please enter the amount less than %s' % (bal)))
        move_line = [
             (0, 0, {'account_id': self.loan_app_id.bank_acc_id.id,
                     'name': '/',
                     'debit': 0,
                     'credit': self.amount}),
             (0, 0, {'account_id': self.loan_app_id.emp_loan_acc_id.id,
                     'name': '/',
                     'debit': self.amount,
                     'credit': 0})
         ]
        self.env['account.move'].create({'journal_id': self.journal_id.id,
                                         'state': 'posted',
                                         'ref': self.loan_app_id.loan_id,
                                         'line_ids': move_line})
        return self.write({'state': 'post'})

    @api.multi
    def post_done(self):
        data_list = []
        loan_payment_ids = self.env['loan.payment'].search([('loan_app_id', '=', self.loan_app_id.id),
                                                            ('state', '=', 'draft')])
        loan_payment_paid_ids = self.env['loan.payment'].search([('loan_app_id', '=', self.loan_app_id.id),
                                                            ('state', '=', 'paid')])
        if loan_payment_ids:
            loan_payment_ids.unlink()
        amount = 0
        balance_list = []
        if loan_payment_paid_ids:
            for each in loan_payment_paid_ids:
                amount += each.principal
                balance_list.append(each.balance_amt)
        if not balance_list:
            remain_balance = self.loan_app_id.amount
        if balance_list:
            remain_balance = balance_list[-1]
        principal = remain_balance - self.amount
        months = len(loan_payment_ids)
        rate = self.loan_app_id.loan_type_id.interest_rate / 100.00
        per = np.arange(months) + 1
        ipmt = np.ipmt(rate / 12, per, months, principal)
        ppmt = np.ppmt(rate / 12, per, months, principal)
        pmt = np.pmt(rate / 12, months, principal)
        if np.allclose(ipmt + ppmt, pmt):
            for payment in per:
                index = payment - 1
                principal = principal + ppmt[index]
                date = datetime.date.today() + relativedelta(months=payment)
                data_list.append((0, 0, {
                                'original_due_date': date,
                                'due_date': date,
                                'principal': (ppmt[index]*-1),
                                'interest': (ipmt[index]*-1),
                                'total': (ppmt[index]*-1) + (ipmt[index]*-1),
                                'rate': (rate/12 ) * 100,
                                'balance_amt': principal,
                                'state': 'draft'
                }))
        self.loan_app_id.write({
            'loan_payment_ids': data_list,
        })
        template_id = self.env['ir.model.data'].get_object_reference('flexi_hr_ee',
                                                            'email_template_for_new_loan_emi')
        if template_id and template_id[1]:
            template_obj = self.env['mail.template'].browse(template_id[1])
            template_obj.send_mail(self.loan_app_id.id, force_send=True, raise_exception=True)
            message_body = _("Your new emi is calculated")
            self.loan_app_id.employee_id.message_post(type='email', subtype='mt_comment',
                                          subject = _('New Loan EMI'),
                                          body = message_body)
        self.write({'state': 'done'})
        return {
            'res_id': self.loan_app_id.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'loan.application',
            'type': 'ir.actions.act_window',
            'nodestroy' : False,
        }

    @api.multi
    @api.onchange('type')
    def onchange_type_id(self):
        final_list = []
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')])
        cash_journal = self.env['account.journal'].search([('type', '=', 'cash')])
        if self.type == 'bank' or self.type == 'card':
            final_list.append(bank_journal.id)
        if self.type == 'cash':
            final_list.append(cash_journal.id)
        self. journal_id = final_list
        return {'domain': {'journal_id': [('id', 'in', final_list)]} }

    name = fields.Char('Name', default="Loan Prepayment")
    loan_app_id = fields.Many2one('loan.application', string="Loan Application", required=True)
    date = fields.Date('Date', required=True)
    amount = fields.Float('Amount', required=True)
    journal_id = fields.Many2one('account.journal', 'Account Journal', required=True)
    cheque_no = fields.Char("Cheque No.")
    card_no = fields.Char("Card No.")
    type = fields.Selection([('cash', 'Cash'), ('card', 'Card'),
                            ('bank', 'Bank')], string='Type', default='bank', required=True)
    state = fields.Selection([
                              ('draft', 'Draft'),
                              ('post','Posted'),
                              ('done','Done'),], string="State", default='draft')

    _rec_name = 'name'

    _sql_constraints = [('cheque_no_uniq', 'unique(cheque_no)', 'Please enter the unique check number.')]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: