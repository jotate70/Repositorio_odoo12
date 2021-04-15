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


class loan_payment(models.Model):
    _name = 'loan.payment'
    _description = 'Loan Payment'

    @api.multi
    def paid_button(self):
        if self.loan_app_id.state != 'paid':
            raise ValidationError(_('Loan application is not approved.'))
        if self.state == 'draft':
            if not self.due_date:
                raise ValidationError(_('Please select the due date.'))
            payment_rec = self.search([('loan_app_id', '=', self.loan_app_id.id), ('state', '=', 'paid')])
            if len(payment_rec) + 1 == self.loan_app_id.no_of_installment:
                self.loan_app_id.write({'state': 'close'})
            self.write({'state': 'paid'})

    rate= fields.Float("Rate")
    due_date = fields.Date(string="Due Date")
    original_due_date = fields.Date(string="Original Due Date")
    principal = fields.Float("Principal")
    balance_amt = fields.Float("Balance")
    interest = fields.Float("Interest")
    total = fields.Float("Total")
    extra = fields.Float("Pre-Payment")
    loan_app_id = fields.Many2one('loan.application', string="Loan Application")
    move_id = fields.Many2one('account.move', string="Account Move")
    employee_id = fields.Many2one('hr.employee', related='loan_app_id.employee_id', readonly=True, store=True)
    state = fields.Selection([
                              ('draft', 'Draft'),
                              ('paid','Paid')], string="State", default='draft')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: