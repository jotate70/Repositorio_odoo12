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
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta


class loan_adjustment(models.Model):
    _name = 'loan.adjustment'
    _description = 'Loan Adjustment'

    @api.multi
    @api.depends('rate', 'loan_type_id', 'operation')
    def preview_new_payments(self):
        final_list = []
        new_rate = False
        if self.rate:
            loan_app_ids = self.env['loan.application'].search([('loan_payment_ids.state', '=', 'draft'),
                                                ('loan_type_id', '=', self.loan_type_id.id),
                                                ('state', '=', 'paid'), ('rate_selection', '=', 'floating')])
            for each in loan_app_ids:
                if self.operation == 'increase':
                    new_rate = each.rate + self.rate
                if self.operation == 'decrease':
                    new_rate = each.rate - self.rate
                final_list.append((0, 0, {
                            'loan_app_id': each.id,
                            'employee_id': each.employee_id.id,
                            'amount': each.amount,
                            'term': each.term,
                            'rate': each.rate,
                            'new_rate': new_rate,
                        }))
                self.loan_adjustment_ids = final_list

    @api.multi
    def new_rate_payments(self):
        loan_app_ids = []
        loan_payment = self.env['loan.payment']
        balance_list = []
        remain_balance = 0
        if not self.loan_adjustment_ids:
            raise Warning(_('No loan application found.'))
        for each_line in self.loan_adjustment_ids:
            if each_line.new_rate <= 0.00:
                raise Warning(_('New rate number should be positive.'))
            loan_payment_ids = loan_payment.search([('loan_app_id', '=', each_line.loan_app_id.id),
                                                            ('state', '=', 'draft')])
            loan_payment_paid_ids = loan_payment.search([('loan_app_id', '=', each_line.loan_app_id.id),
                                                                     ('state', '=', 'paid')])
            each_line.loan_app_id.write({'rate': each_line.new_rate})
            for paid_id in loan_payment_paid_ids[-1:]:
                months = len(loan_payment_paid_ids)
#                 months = months + 1
                rate = paid_id.loan_app_id.rate / 100.00
                per = np.arange(months) + 1
                ppmt = (paid_id.balance_amt * (rate / 12) / (1 - (1 + rate / 12) ** -months))
                paid_id.write({'balance_amt': ppmt})
                balance_list.append(paid_id.balance_amt)
#             if loan_payment_paid_ids:
#                 for each in loan_payment_paid_ids:
#                     balance_list.append(each.balance_amt)
            if not balance_list:
                remain_balance = each_line.loan_app_id.amount
            if balance_list:
                remain_balance = balance_list[-1]
            if each_line.loan_app_id.loan_method == 'reducing':
                principal = remain_balance
                months = len(loan_payment_ids)
                rate = each_line.new_rate / 100.00
                per = np.arange(months) + 1
                ipmt = np.ipmt(rate / 12, per, months, principal)
                ppmt = np.ppmt(rate / 12, per, months, principal)
                pmt = np.pmt(rate / 12, months, principal)
                self.loan_type_id.update({'interest_rate': each_line.new_rate})
                index = 0
                if self.loan_type_id.interest_rate:
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
                                    'loan_app_id': each_line.loan_app_id.id,
                                })
                                index += 1
                elif not self.loan_type_id.interest_rate:
                    principal = remain_balance
                    rate = each_line.new_rate / 100 * principal
                    time = float(len(loan_payment_ids)) / 12
                    months = each_line.loan_app_id.term
                    per = np.arange(months) + 1
                    each_month_payment = balance = 0.00
#                     self.loan_type_id.update({'interest_rate': each_line.new_rate})
                    if rate and time:
                        balance = ((principal / time + rate) / 12) * each_line.loan_app_id.term
                        for each in loan_payment_ids:
                            if each_line.loan_app_id.loan_type_id and each_line.loan_app_id.loan_method:
                                interest = principal / time + rate
                                each_month_payment = interest / 12
                                total_pay_amount = each_month_payment * each_line.loan_app_id.term
                                balance -= each_month_payment
                                monthly_interest = rate * time / each_line.loan_app_id.term
                                monthly_principal = principal / each_line.loan_app_id.term
                                each.update({
                                                'principal': monthly_principal,
                                                'interest': monthly_interest,
                                                'total': monthly_interest + monthly_principal,
                                                'balance_amt': balance,
                                                'rate': ((each_line.new_rate)/100 / 12) * 100,
                                                'loan_app_id': each_line.loan_app_id.id,
                                                })
            if each_line.loan_app_id.loan_method == 'flat':
                    principal = remain_balance
                    rate = each_line.new_rate / 100 * principal
                    time = float(len(loan_payment_ids)) / 12
                    months = each_line.loan_app_id.term
                    per = np.arange(months) + 1
                    each_month_payment = balance = 0.00
                    self.loan_type_id.update({'interest_rate': each_line.new_rate})
                    if rate and time:
                        balance = ((principal / time + rate) / 12) * each_line.loan_app_id.term
                        for each in loan_payment_ids:
                            if each_line.loan_app_id.loan_type_id and each_line.loan_app_id.loan_method:
                                interest = principal / time + rate
                                each_month_payment = interest / 12
                                total_pay_amount = each_month_payment * each_line.loan_app_id.term
                                balance -= each_month_payment
                                monthly_interest = rate * time / each_line.loan_app_id.term
                                monthly_principal = principal / each_line.loan_app_id.term
                                each.update({
                                                'principal': monthly_principal,
                                                'interest': monthly_interest,
                                                'total': monthly_interest + monthly_principal,
                                                'balance_amt': balance,
                                                'rate': ((each_line.new_rate)/100 / 12) * 100,
                                                'loan_app_id': each_line.loan_app_id.id,
                                                })
            
            self.env['interest.rate.history'].create({
                                                  'rate': each_line.new_rate,
                                                  'loan_type_id': each_line.loan_app_id.loan_type_id.id,
                                                  'date': datetime.datetime.now()
                                              })
#             template_id = self.env.ref('flexi_hr_ee.email_template_for_new_loan_rate')
#             template_id.send_mail(each_line.loan_app_id.id, force_send=True, raise_exception=True)
            loan_app_ids.append(each_line.loan_app_id.id)
        return {
            'name': _('Loan Application'),
            'view_type': 'form',
            "view_mode": 'tree,form',
            'res_model': 'loan.application',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', loan_app_ids)]
        }

    @api.onchange('loan_type_id')
    def exsiting_rate(self):
        if self.loan_type_id:
            self.existing_rate = self.loan_type_id.interest_rate

    rate = fields.Float('Rate', required=True)
    existing_rate = fields.Float('Existing Rate', readonly=True, store=True)
    loan_type_id = fields.Many2one('loan.type', string="Loan Type")
    operation = fields.Selection([
                              ('increase', 'Increase'),
                              ('decrease', 'Decrease')], string="Operation", default="increase",
                              required=True)
    loan_adjustment_ids = fields.One2many('loan.adjustment.line', 'loan_adjustment_id', string="Payment Lines",
                              compute="preview_new_payments", readonly=False)


class loan_adjustment_line(models.Model):
    _name = 'loan.adjustment.line'
    _description = 'Loan Adjustment Line'

    loan_app_id = fields.Many2one('loan.application', string="Loan Application")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    rate = fields.Float("Rate")
    amount = fields.Float("Amount")
    term = fields.Integer("Term")
    new_rate = fields.Float("New Rate")
    loan_adjustment_id = fields.Many2one('loan.adjustment', string="Loan Adjustment")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
