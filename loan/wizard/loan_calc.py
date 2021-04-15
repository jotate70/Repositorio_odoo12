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

from odoo import fields, models, api, _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError
import numpy as np


class loan_calc(models.Model):
    _name = 'loan.calc'
    _description = 'Loan Calc'

    global flag
    flag = 0

    @api.multi
    def get_payment_data(self):
        global flag
        if not self.term:
            raise Warning(_('You must enter the term for loan.'))
        payment_list = []
        if self._context.get('active_id'):
            loan_app_rec = self.env['loan.application'].browse([self._context.get('active_id')])
            if loan_app_rec.state != 'approved':
                raise Warning(_("You can't create the payments because loan still not approved."))
            if loan_app_rec.state == 'approved' and flag == 0:
                flag = 1
                raise Warning(_('Are you sure you want to calculate the emi based on this amount %d.'
                               % (self.loan_amount)))
            for line in self.loan_calc_line_ids:
                if line.due_date:
                    loan_due_date = line.due_date.strftime('%m-%Y')
                rate = line.interest_rate.strip('%')
                value = {
                    'original_due_date': line.due_date,
                    'due_date': line.due_date,
                    'rate': rate,
                    'principal': line.principal,
                    'interest': line.interest,
                    'total': line.total,
                    'balance_amt': line.balance_amt,
                    'loan_app_id': loan_app_rec.id,
                }
                payment_list.append((0, 0, value))
            if flag == 1:
                loan_app_rec.write({
                    'loan_payment_ids': payment_list,
                    'no_of_installment': len(payment_list),
                    'term': self.term,
                    'rate': self.loan_type_id.interest_rate,
                    'state': 'emi_calculated'
                })

    @api.depends('loan_calc_line_ids.principal', 'loan_calc_line_ids.interest')
    def _amount_all(self):
        for each in self:
            total_principal = principal = interest = 0.0
            if each.method == 'flat' and self.loan_amount and self.method and self.loan_type_id:
                for each_line in self.loan_calc_line_ids:
                    total_principal += each_line.principal
                principal = each.loan_amount
                interest = each.loan_type_id.interest_rate / 100 * each.loan_amount
                amt_disp = (float(self.term) / 12) * interest
                interest = amt_disp
            else:
                for line in each.loan_calc_line_ids:
                    principal += line.principal
                    interest += line.interest
            each.update({
                'principal_amount': principal,
                'interest_amount': interest,
                'total_amount': principal + interest,
            })

    @api.constrains('loan_type_id', 'loan_amount')
    def check_validation_exception_date_ids(self):
         if self.loan_type_id:
            if self.loan_type_id.maximum_amount < self.loan_amount:
                raise ValidationError(_('Loan amount exceed the limit %d.' % (self.loan_type_id.maximum_amount)))
            if self.loan_type_id.maximum_term < self.term:
                raise ValidationError(_('Loan term exceed the limit %d.' % (self.loan_type_id.maximum_term)))
            if self.loan_type_id.minimum_term > self.term:
                raise ValidationError(_('Loan term limit should be greater then or equal to then %d.' % (self.loan_type_id.minimum_term)))
            if self.loan_type_id.minimum_amount > self.loan_amount and self.loan_amount:
                raise ValidationError(_('The amount you entered is lower than the minimum amount %d.'
                                   % (self.loan_type_id.minimum_amount)))

    @api.multi
    @api.depends('term', 'loan_type_id', 'loan_amount', 'method')
    def compute_due_date(self):
        date_list = []
        if self.method == 'reducing':
            principal = self.loan_amount
            months = self.term
            rate = self.loan_type_id.interest_rate / 100.00
            per = np.arange(months) + 1
            ipmt = np.ipmt(rate / 12, per, months, principal)
            ppmt = np.ppmt(rate / 12, per, months, principal)
            pmt = np.pmt(rate / 12, months, principal)
            p = i = 0.00
            if self.loan_type_id and self.loan_type_id.interest_rate and self.method and self.loan_amount:
                if np.allclose(ipmt + ppmt, pmt):
                    for payment in per:
                        index = payment - 1
                        principal = principal + ppmt[index]
                        interestpd = np.sum(ipmt)
                        date = datetime.date.today() + relativedelta(months=payment)
                        date = date.replace(day=1)
#                     if self.loan_type_id and self.loan_type_id.interest_rate and self.method and self.loan_amount:
                        date_list.append((0, 0, {
                                        'due_date': date,
                                        'principal': (ppmt[index] * -1),
                                        'interest': (ipmt[index] * -1),
                                        'interest_rate': str ("%.2f" % ((rate / 12) * 100)) + " %",
                                        'total': (ppmt[index] * -1) + (ipmt[index] * -1),
                                        'balance_amt': abs(principal)
                        }))
            elif self.loan_type_id and not self.loan_type_id.interest_rate and self.method and self.loan_amount:
                principal = self.loan_amount
                rate = self.loan_type_id.interest_rate / 100 * principal
                time = float(self.term) / 12
                months = self.term
                per = np.arange(months) + 1
                each_month_payment = balance = 0.00
                if time:
                    balance = ((self.loan_amount / time + rate) / 12) * self.term
                    for each_term in per:
                        date = datetime.date.today() + relativedelta(months=each_term)
                        interest = principal / time + rate
                        each_month_payment = interest / 12
                        total_pay_amount = each_month_payment * self.term
                        balance -= each_month_payment
                        monthly_interest = rate * time / self.term
                        monthly_principal = principal / self.term
                        date_list.append((0, 0, {
                                        'due_date': date,
                                        'number': each_term,
                                        'principal': monthly_principal,
                                        'interest': monthly_interest,
                                        'interest_rate': str("%.2f" % (self.loan_type_id.interest_rate / 12)) + " %",
                                        'total': monthly_interest + monthly_principal,
                                        'balance_amt': abs(balance)
                                        }))
        elif self.method == 'flat':
            principal = self.loan_amount
            rate = self.loan_type_id.interest_rate / 100 * principal
            time = float(self.term) / 12
            months = self.term
            per = np.arange(months) + 1
            each_month_payment = balance = 0.00
            if time:
                balance = ((self.loan_amount / time + rate) / 12) * self.term
                for each_term in per:
                    date = datetime.date.today() + relativedelta(months=each_term)
                    if self.loan_type_id and self.method and self.term and self.loan_amount:
                        interest = self.loan_amount / time + rate
                        each_month_payment = interest / 12
                        total_pay_amount = each_month_payment * self.term
                        balance -= each_month_payment
                        monthly_interest = rate * time / self.term
                        monthly_principal = self.loan_amount / self.term
                        date_list.append((0, 0, {
                                        'number': each_term,
                                        'principal': monthly_principal,
                                        'interest': monthly_interest,
                                        'interest_rate': str("%.2f" % (self.loan_type_id.interest_rate / 12)) + " %",
                                        'total': monthly_interest + monthly_principal,
                                        'balance_amt': abs(balance)
                                        }))
        self.loan_calc_line_ids = date_list

    loan_amount = fields.Float(string="Loan Amount")
    principal_amount = fields.Monetary(string="Principal", store=True, readonly=True, compute='_amount_all')
    interest_amount = fields.Monetary(string="Interest", store=True, readonly=True, compute='_amount_all')
    total_amount = fields.Monetary(string="Total", store=True, readonly=True, compute='_amount_all')
    term = fields.Integer("Term")
    loan_type_id = fields.Many2one('loan.type', string="Loan Type")
    loan_calc_line_ids = fields.One2many('loan.calc.line', 'loan_calc_id', string="Loan Type", readonly=False,
                                         compute="compute_due_date", store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True, store=True)
    method = fields.Selection([
                              ('flat', 'Flat'),
                              ('reducing', 'Reducing')], string="Method", default='reducing')


class loan_calc_line(models.Model):
    _name = 'loan.calc.line'
    _description = 'Loan Calc Line'

    loan_calc_id = fields.Many2one('loan.calc', string="Loan Calculator")
    currency_id = fields.Many2one('res.currency', related='loan_calc_id.currency_id', readonly=True, store=True)
    due_date = fields.Date(string="Due Date", readonly=True)
    principal = fields.Monetary("Principal", readonly=True)
    interest = fields.Monetary("Interest", readonly=True)
    balance_amt = fields.Float("Balance", readonly=True)
    interest_rate = fields.Char("Interest Rate", readonly=True)
    total = fields.Monetary("Total", readonly=True)
    method = fields.Selection([('flat', 'Flat'), ('reducing', 'Reducing')],
                                related="loan_calc_id.method", string="Method", readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: