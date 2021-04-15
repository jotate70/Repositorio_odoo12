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
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class loan_advance_payment(models.Model):
    _name = 'loan.advance.payment'
    _description = 'Loan Advance Payment'

    @api.multi
    @api.depends('loan_app_id', 'amount')
    def preview_payments(self):
        final_list = []
        loan_payment = self.env['loan.payment']
        if self.amount and self.amount <= 0:
            raise ValidationError(_('Please enter the amount greater than zero'))
        if self.loan_app_id and self.amount:
            loan_payment_ids = loan_payment.search([('loan_app_id', '=', self.loan_app_id.id),
                                                        ('state', '=', 'draft')])
            loan_payment_paid_ids = loan_payment.search([('loan_app_id', '=', self.loan_app_id.id),
                                                                ('state', '=', 'paid')])
            balance_list = []
            for each in loan_payment_paid_ids:
                balance_list.append(each.balance_amt)
            if not balance_list:
                remain_balance = self.loan_app_id.amount
            if balance_list:
                remain_balance = balance_list[-1]
            bal = "%.2f" % (remain_balance)
            if self.amount and self.amount > float(bal):
                raise ValidationError(_('Please enter the amount less than %s' % (bal)))
            bal = "%.2f" % (remain_balance)
            if self.amount == float(bal):
                final_list = []
            else:
                if self.loan_app_id.loan_method == 'reducing':
                    principal = remain_balance - self.amount
                    months = len(loan_payment_ids)
                    rate = self.loan_app_id.loan_type_id.interest_rate / 100.00
                    per = np.arange(months) + 1
                    ipmt = np.ipmt(rate / 12, per, months, principal)
                    ppmt = np.ppmt(rate / 12, per, months, principal)
                    pmt = np.pmt(rate / 12, months, principal)
                    if self.loan_app_id.loan_type_id and self.loan_app_id.loan_type_id.interest_rate:
                        if np.allclose(ipmt + ppmt, pmt):
                            for payment in per:
                                index = payment - 1
                                principal = principal + ppmt[index]
                                date = datetime.date.today() + relativedelta(months=payment)
                                date = date.replace(day=1)
    #                             if self.loan_app_id.loan_type_id and self.loan_app_id.loan_type_id.interest_rate:
                                final_list.append((0, 0, {
                                    'due_date': date,
                                    'principal': (ppmt[index] * -1),
                                    'interest': (ipmt[index] * -1),
                                    'total': (ppmt[index] * -1) + (ipmt[index] * -1),
                                    'balance_amt': abs(principal),
                                }))
                    elif self.loan_app_id.loan_type_id and not self.loan_app_id.loan_type_id.interest_rate:
                        principal = remain_balance - self.amount
                        rate = self.loan_app_id.loan_type_id.interest_rate / 100 * principal
                        time = float(len(loan_payment_ids)) / 12
                        months = self.loan_app_id.term
                        per = np.arange(months) + 1
                        each_month_payment = balance = 0.00
                        if time:
                            balance = ((principal / time + rate) / 12) * self.loan_app_id.term
                            for each_term in per:
                                date = datetime.date.today() + relativedelta(months=each_term)
                                date = date.replace(day=1)
                                if self.loan_app_id.loan_type_id and self.loan_app_id.loan_method:
                                    interest = principal / time + rate
                                    each_month_payment = interest / 12
                                    total_pay_amount = each_month_payment * self.loan_app_id.term
                                    balance -= each_month_payment
                                    monthly_interest = rate * time / self.loan_app_id.term
                                    monthly_principal = principal / self.loan_app_id.term
                                    final_list.append((0, 0, {
                                                    'due_date': date,
                                                    'number': each_term,
                                                    'principal': monthly_principal,
                                                    'interest': monthly_interest,
                                                    'interest_rate': str("%.2f" % (self.loan_app_id.loan_type_id.interest_rate / 12)) + " %",
                                                    'total': monthly_interest + monthly_principal,
                                                    'balance_amt': abs(balance)
                                                    }))
                elif self.loan_app_id.loan_method == 'flat':
                    principal = remain_balance - self.amount
                    rate = self.loan_app_id.loan_type_id.interest_rate / 100 * principal
                    time = float(len(loan_payment_ids)) / 12
                    months = self.loan_app_id.term
                    per = np.arange(months) + 1
                    each_month_payment = balance = 0.00
                    if time:
                        balance = ((principal / time + rate) / 12) * self.loan_app_id.term
                        for each_term in per:
                            date = datetime.date.today() + relativedelta(months=each_term)
                            date = date.replace(day=1)
                            if self.loan_app_id.loan_type_id and self.loan_app_id.loan_method:
                                interest = principal / time + rate
                                each_month_payment = interest / 12
                                total_pay_amount = each_month_payment * self.loan_app_id.term
                                balance -= each_month_payment
                                monthly_interest = rate * time / self.loan_app_id.term
                                monthly_principal = principal / self.loan_app_id.term
                                final_list.append((0, 0, {
                                                'due_date': date,
                                                'number': each_term,
                                                'principal': monthly_principal,
                                                'interest': monthly_interest,
                                                'interest_rate': str("%.2f" % (self.loan_app_id.loan_type_id.interest_rate / 12)) + " %",
                                                'total': monthly_interest + monthly_principal,
                                                'balance_amt': abs(balance)
                                                }))
            self.lap_line_ids = final_list
            return final_list

    @api.multi
    def new_payments(self):
        loan_payment = self.env['loan.payment']
        loan_payment_ids = loan_payment.search([('loan_app_id', '=', self.loan_app_id.id),
                                                            ('state', '=', 'draft')])
        loan_payment_paid_ids = loan_payment.search([('loan_app_id', '=', self.loan_app_id.id),
                                                            ('state', '=', 'paid')])
        balance_list = []
        for each in loan_payment_paid_ids:
            balance_list.append(each.balance_amt)
        if not balance_list:
            remain_balance = self.loan_app_id.amount
        if balance_list:
            remain_balance = balance_list[-1]
#         principal = remain_balance - self.amount
#         months = len(loan_payment_ids)
#         rate = self.loan_app_id.loan_type_id.interest_rate / 100.00
#         per = np.arange(months) + 1
#         ipmt = np.ipmt(rate / 12, per, months, principal)
#         ppmt = np.ppmt(rate / 12, per, months, principal)
#         pmt = np.pmt(rate / 12, months, principal)
#         index = 0
        bal = "%.2f" % (remain_balance)
        if self.amount == float(bal) and not self.create_entries:
            for each_paid in loan_payment_ids:
                each_paid.update({
                            'state': 'paid',
                            'extra': 0.00,
                            'principal': 0.00,
                            'interest': 0.00,
                            'rate': (rate / 12) * 100,
                            'total': 0.00,
                            'balance_amt': 0.00,
                            'loan_app_id': each.loan_app_id.id})
            if not self.loan_app_id.bank_acc_id.id or not self.loan_app_id.emp_loan_acc_id.id:
                raise ValidationError(_('Please select bank account and customer account.'))
            move_line = [
                 (0, 0, {'account_id': self.loan_app_id.bank_acc_id.id,
                         'name': '/', 'credit': self.amount}),
                 (0, 0, {'account_id': self.loan_app_id.emp_loan_acc_id.id,
                         'name': '/', 'debit': self.amount, })]
            move_id = self.env['account.move'].create({'journal_id': self.loan_app_id.account_journal_id.id,
                                             'ref': self.loan_app_id.loan_id,
                                             'line_ids': move_line})
            move_id.post()
            loan_payment_ids[0].update({'balance_amt': 0.00,
                        'state': 'paid',
                        'extra': self.amount,
                        'move_id': move_id.id
                        })
            loan_payment_ids[0].loan_app_id.update({'state': 'close'})
        if self.create_entries:
            if self.loan_app_id.loan_method == 'reducing':
                principal = remain_balance - self.amount
                months = len(loan_payment_ids)
                rate = self.loan_app_id.loan_type_id.interest_rate / 100.00
                per = np.arange(months) + 1
                ipmt = np.ipmt(rate / 12, per, months, principal)
                ppmt = np.ppmt(rate / 12, per, months, principal)
                pmt = np.pmt(rate / 12, months, principal)
                index = 0
#                 bal = "%.2f" % (remain_balance)
                if np.allclose(ipmt + ppmt, pmt):
                    for each in loan_payment_ids:
                        length = len(per)
                        if index < length:
                            principal = principal + ppmt[index]
                            each.update({
                                'principal': (ppmt[index] * -1),
                                'interest': (ipmt[index] * -1),
                                'rate': (rate / 12) * 100,
                                'total': (ppmt[index] * -1) + (ipmt[index] * -1),
                                'balance_amt': abs(principal),
                                'loan_app_id': each.loan_app_id.id,
                            })
                            index += 1
            elif self.loan_app_id.loan_method == 'flat':
                principal = remain_balance - self.amount
                rate = self.loan_app_id.loan_type_id.interest_rate / 100 * principal
                time = float(len(loan_payment_ids)) / 12
                months = self.loan_app_id.term
                per = np.arange(months) + 1
                each_month_payment = balance = 0.00
                if rate and months:
                    balance = ((principal / time + rate) / 12) * self.loan_app_id.term
                    for each_term in loan_payment_ids:
                        if self.loan_app_id.loan_type_id and self.loan_app_id.loan_method:
                            interest = principal / time + rate
                            each_month_payment = interest / 12
                            total_pay_amount = each_month_payment * self.loan_app_id.term
                            balance -= each_month_payment
                            monthly_interest = rate * time / self.loan_app_id.term
                            monthly_principal = principal / self.loan_app_id.term
                        each_term.update( {
                                        'principal': monthly_principal,
                                        'interest': monthly_interest,
                                        'total': monthly_interest + monthly_principal,
                                        'balance_amt': abs(balance),
                                        'loan_app_id': each_term.loan_app_id.id,
                                        })
                
                
            if not self.loan_app_id.bank_acc_id.id or not self.loan_app_id.emp_loan_acc_id.id:
                raise ValidationError(_('Please select bank account and customer account.'))
            move_line = [
                 (0, 0, {'account_id': self.loan_app_id.bank_acc_id.id,
                         'name': '/', 'credit': self.amount}),
                 (0, 0, {'account_id': self.loan_app_id.emp_loan_acc_id.id,
                         'name': '/', 'debit': self.amount})]
            move_id = self.env['account.move'].create({'journal_id': self.loan_app_id.account_journal_id.id,
                                             'ref': self.loan_app_id.loan_id,
                                             'line_ids': move_line})
            move_id.post()
            loan_payment_ids[0].update({'move_id': move_id.id, 'extra': self.amount})
        elif not self.create_entries and self.amount != float(bal):
            loan_payment_ids[0].update({'extra': self.amount})
            if np.allclose(ipmt + ppmt, pmt):
                for each in loan_payment_ids:
                    length = len(per)
                    if index < length:
                        principal = principal + ppmt[index]
                        each.update({
                            'principal': (ppmt[index] * -1),
                            'interest': (ipmt[index] * -1),
                            'rate': (rate / 12) * 100,
                            'total': (ppmt[index] * -1) + (ipmt[index] * -1) + each.extra,
                            'balance_amt': principal,
                            'loan_app_id': each.loan_app_id.id,
                        })
                        index += 1
        self.env['loan.prepayment'].create({
                                        'loan_app_id': self.loan_app_id.id,
                                        'date': datetime.date.today(),
                                        'amount': self.amount,
                                        'journal_id': self.loan_app_id.account_journal_id.id,
                                        'state': 'done',
                                        'name': 'Loan Prepayment'
                                    })
        template_id = self.env.ref('flexi_hr_ee.email_template_for_new_loan_emi')
        self.loan_app_id.update({'advance_amt': self.amount})
        template_id.send_mail(self.loan_app_id.id)
        self.loan_app_id.employee_id.message_post(subject=_('New Loan EMI'),
                                                  body=_("Your new emi is calculated"))
        return {
            'res_id': self.loan_app_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.application',
            'type': 'ir.actions.act_window',
            'nodestroy' : False,
        }

    loan_app_id = fields.Many2one('loan.application', string="Loan Application", required=True)
    amount = fields.Float('Amount', required=True)
    lap_line_ids = fields.One2many('loan.advance.payment.line', 'loan_advance_payment_id',
                                   string="Payment Lines",
                                   compute="preview_payments")
    create_entries = fields.Boolean('Create Entries', default=False)
    journal_id = fields.Many2one('account.journal', string="Journal")


class loan_advance_payment_line(models.Model):
    _name = 'loan.advance.payment.line'
    _description = 'Loan Advance Payment'

    due_date = fields.Date(string="Due Date")
    principal = fields.Float("Principal")
    balance_amt = fields.Float("Balance")
    interest = fields.Float("Interest")
    total = fields.Float("Total")
    loan_advance_payment_id = fields.Many2one('loan.advance.payment', string="Advance Payment")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: