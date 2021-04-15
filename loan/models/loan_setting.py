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


class loan_setting(models.Model):
    _name = 'loan.setting'

    @api.multi
    def execute(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def default_get(self, fields):
        obj = self.search([], order='id desc', limit=1)
        res = super(loan_setting, self).default_get(fields)
        if obj:
            res.update({'emp_loan_acc_id':obj.emp_loan_acc_id.id,
                        'bank_acc_id':obj.bank_acc_id.id,
                        'interest_acc_id':obj.interest_acc_id.id,
                        'loan_principal_acc_id':obj.loan_principal_acc_id.id,
                        'account_journal_id':obj.account_journal_id.id,
                        'service_charges_acc_id':obj.service_charges_acc_id.id,
                        'other_fee_acc_id':obj.other_fee_acc_id.id,
                        'installment_start_day':obj.installment_start_day,
                        'apply_multiple_loan':obj.apply_multiple_loan
                        })
        return res

    emp_loan_acc_id = fields.Many2one('account.account', string="Employee Loan Account")
    bank_acc_id = fields.Many2one('account.account', string="Bank Account")
    interest_acc_id = fields.Many2one('account.account', string="Interest Account")
    loan_principal_acc_id = fields.Many2one('account.account', string="Loan Principal Account")
    account_journal_id = fields.Many2one('account.journal', string="Bank Journal")
    service_charges_acc_id = fields.Many2one('account.account', 'Service Charges Account')
    other_fee_acc_id = fields.Many2one('account.account', 'Other Fee Account')
    installment_start_day = fields.Integer('Installment Start Day', default=1)
    apply_multiple_loan = fields.Boolean(string="Apply Multiple Loan")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
