# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError
import logging
_logger = logging.getLogger(__name__)
try:
    import numpy as np
except ImportError:
    _logger.error('Cannot `import numpy`.use `sudo pip install numpy` command.')


class loan_application(models.Model):
    _name = 'loan.application'
    _rec_name = 'loan_id'
    _inherit = ['mail.thread']
    _description = 'Loan Application'

    @api.onchange('app_categ_id', 'loan_type_id')
    def onchange_field(self):
        final_list = []
        if self.app_categ_id:
            for line in self.app_categ_id.loan_doc_ids:
                final_list.append((0, 0, {'loan_type_doc_id': line.id, 'state': 'draft'}))
        elif self.loan_type_id and not self.app_categ_id:
            for line in self.loan_type_id.loan_doc_ids:
                final_list.append((0, 0, {'loan_type_doc_id': line.id, 'state': 'draft'}))
        self.loan_type_doc_ids = final_list

    def check_approved_document(self):
        for each_document in self.loan_type_doc_ids:
            if not each_document.document:
                raise ValidationError(_('You must upload the document for %s.'
                                        % (each_document.loan_type_doc_id.name)))

    @api.one
    def approved_document(self):
        account_move_obj = self.env['account.move']
        if self.requested_loan_amt < self.loan_type_id.minimum_amount:
                raise ValidationError(_('Request amount you entered is lower than the minimum amount %d.'
                                        % (self.loan_type_id.minimum_amount)))
        elif self.requested_loan_amt > self.loan_type_id.maximum_amount:
                raise ValidationError(_('Request amount exceed the limit %d.' % (self.loan_type_id.maximum_amount)))
        if self.app_categ_id:
            self.check_approved_document()
        elif self.loan_type_id and not self.app_categ_id:
            self.check_approved_document()
        if self.loan_type_doc_ids.filtered(lambda line:line.state != 'approved'):
            raise ValidationError(_('All the uploaded document must be in approved state.'))
        move_line = []
        if self.other_fee:
            move_line.append((0, 0, {'account_id': self.other_fee_acc_id.id,
                                    'name': '/', 'credit': self.other_fee}))
            move_line.append((0, 0, {'account_id': self.emp_loan_acc_id.id,
                                     'name': '/', 'debit': self.other_fee}))
        if self.service_charges:
            move_line.append((0, 0, {'account_id': self.service_charges_acc_id.id,
                                      'name': '/', 'credit': self.service_charges}))
            move_line.append((0, 0, {'account_id': self.emp_loan_acc_id.id,
                                 'name': '/', 'debit': self.service_charges}))
        if move_line:
            account_move_obj = account_move_obj.create({'journal_id': self.account_journal_id.id,
                                                        'ref': self.loan_id, 'line_ids': move_line})
            account_move_obj.post()
        self.write({"state": "verified"})

    @api.multi
    def rejected_mail_template(self):
        template_id = self.env.ref('flexi_hr_ee.email_template_for_reject_loan')
        template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.employee_id.message_post(subject=_('Loan Rejected'),
                                      body='Hello, Your %s is rejected.' % (self.loan_id))

    @api.multi
    def cancelled_mail_template(self):
        template_id = self.env.ref('flexi_hr_ee.email_template_for_cancel_loan')
        template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.employee_id.message_post(subject=_('Loan Cancelled'),
                                      body='Hello, Your %s is cancelled.' % (self.loan_id))

    @api.multi
    def rejected(self):
        return {
            'name': _('Loan Reject'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('flexi_hr_ee.wizard_loan_form_view').id,
            'res_model': 'wizard.loan',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'from_reject':True}
          }

    @api.multi
    def verified_approve(self):
        loan_settings_id = self.env['loan.setting'].search([], limit=1, order="id desc")
        loan_id = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id), ('state', '!=', 'close')])
#         if loan_settings_id and not loan_settings_id.apply_multiple_loan and loan_id:
#             raise ValidationError(_('You can not have multiple loans.'))
        template_id = self.env.ref('flexi_hr_ee.email_template_for_loan_manager')
        if self.approved_loan_amt <= 0.00:
            raise ValidationError(_('Please enter the approved loan amount.'))
        if self.loan_type_id.minimum_amount > self.approved_loan_amt:
            raise ValidationError(_('Approved amount you entered is lower than the minimum amount %d.'
                           % (self.loan_type_id.minimum_amount)))
        if self.loan_type_id.maximum_amount < self.approved_loan_amt:
            raise ValidationError(_('Approved amount exceed the limit %d.' % (self.loan_type_id.maximum_amount)))
        try:
            if template_id:
                template_id.send_mail(self.id, force_send=True, raise_exception=True)
#                 message_body = _("New loan application for customer %s is coming to approved for amount %d") \
#                                 % (self.employee_id.name, self.amount)
#                 for each_user in self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)]):
#                     each_user.message_post(subject=_('New Loan Application For Approve'),
#                                            body=message_body)
        except Exception as e:
                raise ValidationError(_("Please Configure Outgoing Mail Server.- %s")%e)
        self.write({"state": "approve"})

    @api.multi
    def get_loan_manager_mail(self):
        email_list = ''
        loan_manager_id = self.env['ir.model.data'].get_object_reference('hr',
                                                                         'group_hr_manager')[1]
        for each_user in self.env['res.groups'].sudo().browse(loan_manager_id).users:
            email_list += str(each_user.email) + ','
        return email_list
#         return email_list

    @api.multi
    def button_approved(self):
        template_id = self.env.ref('flexi_hr_ee.email_template_for_apporve_loan')
        template_id.send_mail(self.id, force_send=True, raise_exception=True)
        self.write({'state': 'approved', 'approve_date': datetime.datetime.now()})

    @api.multi
    def button_paid(self):
        move_line = [
             (0, 0, {'account_id': self.bank_acc_id.id,
                     'name': '/', 'debit': self.total_principal_amt}),
             (0, 0, {'account_id': self.emp_loan_acc_id.id,
                     'name': '/', 'credit': self.total_principal_amt})
         ]
        move_id = self.env['account.move'].create({'journal_id': self.account_journal_id.id, 'ref': self.loan_id, 'line_ids': move_line})
        move_id.post()
        per = np.arange(self.term) + 1
        lst_date = []
        loan_setting_id = self.env['loan.setting'].sudo().search([], limit=1, order='id desc')
        if self.approve_date:
            for each_term in per:
#                 approve_dt = datetime.datetime.strptime(self.approve_date, "%Y-%m-%d %H:%M:%S")
                date = self.approve_date + relativedelta(months=each_term)
                date = date.replace(day=loan_setting_id.installment_start_day)
                lst_date.append(date)
        len_date = len(lst_date)
        count = 0
        for each in self.loan_payment_ids:
            if count <= len_date:
                each.write({'original_due_date': lst_date[count], 'due_date': lst_date[count]})
                count += 1
        template_id = self.env.ref('flexi_hr_ee.email_template_for_paid_loan')
        template_id.send_mail(self.id, force_send=True, raise_exception=True)
        message_body = _("Your loan is paid for amount %d") % (self.amount)
        self.employee_id.message_post(subject=_('Loan Paid'), body=message_body)
        self.write({'state': 'paid'})

    @api.multi
    @api.depends('loan_payment_ids.principal', 'loan_payment_ids.interest', 'loan_payment_ids.total', 'loan_payment_ids.state', 'loan_payment_ids.extra')
    def _amount_all(self):
        for payment in self:
            pre_payment_amount = principal = interest = paid_amt = remain_amt = 0.0
            for line in payment.loan_payment_ids:
                principal += line.principal
                interest += line.interest
                pre_payment_amount += line.extra
                if line.state == 'paid':
                    paid_amt += line.total
                if line.state == 'draft':
                    remain_amt += line.total
            payment.update({'total_paid_amt': payment.currency_id.round(paid_amt + pre_payment_amount),
                            'total_remaining_amt': payment.currency_id.round(self.amount) - payment.currency_id.round(paid_amt + pre_payment_amount),
                            'total_principal_amt': payment.currency_id.round(principal),
                            'total_interest_amt': payment.currency_id.round(interest),
                            'total_pre_payment': payment.currency_id.round(pre_payment_amount),
                            'amount_total': principal + interest
                            })

#     @api.multi
#     @api.depends('loan_payment_ids.principal', 'loan_payment_ids.interest', 'loan_payment_ids.total', 'loan_payment_ids.state')
#     def _amount_unpaid(self):
#         for payment in self:
#             amt = 0.0
#             for line in payment.loan_payment_ids:
#                 if line.state == 'draft':
#                     amt += line.total
#             payment.update({
#                 'total_remaining_amt': payment.currency_id.round(amt),
#             })

    @api.multi
    def unlink(self):
        for each_loan in self:
#             if each_loan.state in ['paid', 'close']:
                raise ValidationError(_("You can't delete Loan."))
        return super(loan_application, self).unlink()

    @api.multi
    def button_dummy(self):
        return True

    @api.multi
    def compute_payments_again(self):
        if self.loan_type_id and self.loan_type_id.maximum_amount < self.amount:
            raise Warning(_('Disbursed Loan amount exceed the limit %d.'
                              % (self.loan_type_id.maximum_amount)))
        if self.loan_type_id and self.loan_type_id.minimum_amount >= self.amount and self.amount:
            raise Warning(_('Disbursed amount you entered is lower than the minimum amount %d.'
                               % (self.loan_type_id.minimum_amount)))
        date_list = []
        if self.amount != 0.00:
            if self.loan_type_id.method == 'reducing':
                principal = self.amount
                months = self.term
                rate = self.loan_type_id.interest_rate / 100.00
                per = np.arange(months) + 1
                ipmt = np.ipmt(rate / 12, per, months, principal)
                ppmt = np.ppmt(rate / 12, per, months, principal)
                pmt = np.pmt(rate / 12, months, principal)
                p = i = 0.00
                if np.allclose(ipmt + ppmt, pmt):
                    for payment in per:
                        index = payment - 1
                        principal = principal + ppmt[index]
                        interestpd = np.sum(ipmt)
                        date = datetime.date.today() + relativedelta(months=payment)
                        date = date.replace(day=1)
                        if self.loan_type_id and self.loan_type_id.method and self.amount:
                            date_list.append((0, 0, {
                                            'due_date': date,
                                            'principal': (ppmt[index] * -1),
                                            'interest': (ipmt[index] * -1),
                                            'interest_rate': str ("%.2f" % ((rate / 12) * 100)) + " %",
                                            'total': (ppmt[index] * -1) + (ipmt[index] * -1),
                                            'balance_amt': principal
                            }))
            else:
                principal = self.amount
                rate = self.loan_type_id.interest_rate / 100 * principal
                time = float(self.term) / 12
                months = self.term
                per = np.arange(months) + 1
                each_month_payment = balance = 0.00
                if rate and time:
                    balance = ((self.amount / time + rate) / 12) * self.term
                for each_term in per:
                    date = datetime.date.today() + relativedelta(months=each_term)
                    if principal and time and self.loan_type_id and self.loan_type_id.method and self.term and self.amount:
                        interest = self.amount / time + rate
                        each_month_payment = interest / 12
                        total_pay_amount = each_month_payment * self.term
                        balance -= each_month_payment
                    if self.loan_type_id and self.method and self.term and self.amount:
                        monthly_interest = ((self.loan_type_id.interest_rate / 100 * self.amount) * time) / self.term
                        monthly_principal = self.amount / self.term
                        date_list.append((0, 0, {
                                        'number': each_term,
                                        'due_date': False,
                                        'principal': monthly_principal,
                                        'interest': monthly_interest,
                                        'interest_rate': str("%.2f" % (self.loan_type_id.interest_rate / 12)) + " %",
                                        'total': monthly_interest + monthly_principal,
                                        'balance_amt': abs(balance)
                        }))
            payment_ids = self.env['loan.payment'].search([('loan_app_id' , '=', self.id)])
            payment_ids.unlink()
            self.write({'loan_payment_ids': date_list})

    def get_signup_url(self):
        loan_manager_id = self.env['ir.model.data'].get_object_reference('hr',
                                                                         'group_hr_manager')[1]
        contex_signup = dict(self._context, signup_valid=True)
        for each_user in self.env['res.groups'].browse(loan_manager_id).users:
            return each_user.partner_id.with_context(signup_valid=True)._get_signup_url_for_action(
            action='/mail/view',
            model=self._name,
            res_id=self.id)[each_user.partner_id.id]

    def _return_history_count(self):
        for each in self:
            count = self.env['return.cheque.history'].search([('loan_app_id', '=', self.id)])
            count_no = len(count)
            each.return_count = count_no
        return True

    @api.multi
    def reset(self):
        self.write({'state': 'draft'})

    @api.multi
    def approved_reset(self):
        return self.write({'state': 'verified'})

    @api.one
    def loan_close(self):
        self.write({'state':'close'})
        template_obj = self.env.ref('flexi_hr_ee.email_template_loan_close')
        template_obj.send_mail(self.id, force_send=True, raise_exception=True)

    @api.one
    @api.depends('loan_payment_ids.state')
    def _check_loan_fully_paid(self):
        if self.loan_payment_ids:
            all_record = all ([x.state == 'paid' for x in self.loan_payment_ids if self.loan_payment_ids])
            if all_record:
                self.fully_paid = True

    @api.model
    def default_get(self, fields):
        res = super(loan_application, self).default_get(fields)
        loan_setting_id = self.env['loan.setting'].sudo().search([], limit=1, order='id desc')
        if not loan_setting_id.emp_loan_acc_id.id or not loan_setting_id.bank_acc_id.id or not \
        loan_setting_id.interest_acc_id.id or not loan_setting_id.loan_principal_acc_id.id or not \
        loan_setting_id.account_journal_id.id or not loan_setting_id.service_charges_acc_id.id \
        or not loan_setting_id.other_fee_acc_id.id:
            raise ValidationError(_('Please Configure the loan Setting for account details.'))
        else:
            res.update({
               'emp_loan_acc_id': loan_setting_id.emp_loan_acc_id.id,
               'bank_acc_id': loan_setting_id.bank_acc_id.id,
               'interest_acc_id': loan_setting_id.interest_acc_id.id,
               'loan_principal_acc_id': loan_setting_id.loan_principal_acc_id.id,
               'account_journal_id': loan_setting_id.account_journal_id.id,
               'service_charges_acc_id': loan_setting_id.service_charges_acc_id.id,
               'other_fee_acc_id': loan_setting_id.other_fee_acc_id.id,
            })
        return res

    @api.onchange('loan_type_id')
    def loan_type_method(self):
        self.loan_method = self.loan_type_id.method

    return_count = fields.Integer('Return Count', compute='_return_history_count')
    loan_method = fields.Selection([('flat', 'Flat'), ('reducing', 'Reducing')],
                                string="Method")
    loan_type_id = fields.Many2one('loan.type', string="Loan Type", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id,
                                 store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                  readonly=True, store=True)
    loan_type_doc_ids = fields.One2many('loan.application.document', 'loan_app_id',
                                        string="Loan Type Document")
    amount = fields.Float("Disbursed Loan Amount")
    term = fields.Integer("Term", readonly=True)
    loan_payment_ids = fields.One2many('loan.payment', 'loan_app_id', string="Loan Payment")
    state = fields.Selection([
                              ('draft', 'Draft'),
                              ('emi_calculated', 'EMI Calculated'),
                              ('verified', 'Verified Document'),
                              ('approve', 'Waiting For Approval'),
                              ('approved', 'Approved'),
                              ('paid', 'Amount Disbursed'),
                              ('close', 'Closed'),
                              ('cancel', 'Cancelled'),
                              ('rejected', 'Rejected'), ('reset', 'Reset')],
                              string="State", default='draft')
    rate = fields.Float("Annual Rate", readonly=True)
    no_of_installment = fields.Integer("No. Of Installment", readonly=True)
    application_date = fields.Datetime("Apply Date", default=datetime.datetime.now())
    approve_date = fields.Datetime("Approve Date")
    loan_id = fields.Char("Loan")
    emp_loan_acc_id = fields.Many2one('account.account', string="Employee Loan Account", required=True)
    bank_acc_id = fields.Many2one('account.account', string="Bank Account", required=True)
    interest_acc_id = fields.Many2one('account.account', string="Interest Account", required=True)
    loan_principal_acc_id = fields.Many2one('account.account', string="Loan Principal Account",
                                             required=True)
    account_journal_id = fields.Many2one('account.journal', string="Bank Journal", required=True)
    service_charges_acc_id = fields.Many2one('account.account', 'Service Charges Account',
                                             required=True)
    other_fee_acc_id = fields.Many2one('account.account', 'Other Fee Account', required=True)
    total_principal_amt = fields.Monetary(string='Total Principal', store=True,
                                       compute='_amount_all', track_visibility='always')
    total_interest_amt = fields.Monetary(string='Total Interest', store=True,
                                      compute='_amount_all', track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, compute='_amount_all',
                                track_visibility='always')
    total_pre_payment = fields.Monetary(string='Total Pre-Payment', compute='_amount_all', store=True)
    reject_reason = fields.Text('Rejection Reason')
    loan_purpose = fields.Text(string="Loan Purpose", required=True)
    template_id = fields.Many2one('mail.template', string="Template", required=True)
    app_categ_id = fields.Many2one('applicant.category', string="Applicant Category")
    requested_loan_amt = fields.Float(string="Requested Loan Amount", required=True)
    approved_loan_amt = fields.Float(string="Approved Loan Amount", required=True, default=0.00)
    service_charges = fields.Float(string="Service Charges")
    other_fee = fields.Float(string="Miscellaneous Fee")
    loan_cancel_reason = fields.Text('Cancellation Reason')
    total_paid_amt = fields.Float(string="Paid Amount", compute="_amount_all", store=True)
    total_remaining_amt = fields.Text('Remaining Amount', compute="_amount_all", store=True)
    advance_amt = fields.Text('Advance Amount')
    fully_paid = fields.Boolean(string="Fully Paid", compute='_check_loan_fully_paid', store=True)
    rate_selection = fields.Selection([('fixed', 'Fixed'), ('floating', 'Floating')], string="Rate Selection")

    _sql_constraints = [('loan_id_uniq', 'unique(loan_id)', 'Loan should be unique.')]

    @api.multi
    def cancel(self):
        return {
            'name': _('Loan Cancel'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.loan',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('flexi_hr_ee.wizard_loan_form_view').id,
            'target': 'new',
            'context':{'from_cancel':True}
          }

    @api.model
    def create(self, vals):
        vals['loan_id'] = self.env['ir.sequence'].next_by_code('loan.application.number') or _('New')
        if vals.get('requested_loan_amt') <= 0.00:
            raise ValidationError(_('Please enter the requested loan amount.'))
        loan_type_id = self.env['loan.type'].browse(vals.get('loan_type_id'))
        if loan_type_id:
            if vals.get('requested_loan_amt') < loan_type_id.minimum_amount:
                raise ValidationError(_('Request amount you entered is lower than the minimum amount %d.'
                                        % (loan_type_id.minimum_amount)))
            elif vals.get('requested_loan_amt') > loan_type_id.maximum_amount:
                raise ValidationError(_('Request amount exceed the limit %d.' % (loan_type_id.maximum_amount)))
        return super(loan_application, self).create(vals)

    @api.multi
    def create_loan_calc(self):
        if self.state == 'draft':
            if self.requested_loan_amt <= 0.00:
                raise ValidationError(_('Please enter requested loan amount.'))
            amount = self.requested_loan_amt
        if self.state in ['verified', 'approve']:
            if self.approved_loan_amt <= 0.00:
                raise ValidationError(_('Please enter approved loan amount.'))
            if self.loan_type_id.minimum_amount > self.approved_loan_amt:
                raise ValidationError(_('Approved amount you entered is lower than the minimum amount %d.'
                                     % (self.loan_type_id.minimum_amount)))
            if self.loan_type_id.maximum_amount < self.approved_loan_amt:
                raise ValidationError(_('Approved amount exceed the limit %d.' % (self.loan_type_id.maximum_amount)))
            amount = self.approved_loan_amt
        if self.state == 'approved':
            if self.amount <= 0.00:
                raise ValidationError(_('Please enter proper disburse loan amount.'))
            if self.amount != self.approved_loan_amt:
                raise ValidationError(_('Disbursed amount and Approved Loan amount should be same.'))
#             if self.loan_type_id.minimum_amount > self.amount:
#                 raise ValidationError(_('Disbursed amount you entered is lower than the minimum amount %d.'
#                                       % (self.loan_type_id.minimum_amount)))
#             if self.loan_type_id.maximum_amount < self.amount:
#                 raise ValidationError(_('Disbursed amount exceed the limit %d.' % (self.loan_type_id.maximum_amount)))
            amount = self.amount
        return {
            'name': _('Loan Calculator'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.calc',
            'type': 'ir.actions.act_window',
            'context': {'default_loan_type_id': self.loan_type_id.id,
                        'default_method': self.loan_type_id.method,
                        'default_loan_amount': amount,
                        'from_loan_app':True if self.state == 'approved' else False,
                        },
            'view_id': self.env.ref('flexi_hr_ee.loan_calc_form').id,
            'target': 'new'
        }

    @api.multi
    def view_loan_prepayment(self):
        return {
            'name': _('Loan Prepayment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'loan.prepayment',
            'domain': [('loan_app_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_loan_app_id': self.id},
        }


class loan_application_document(models.Model):
    _name = 'loan.application.document'
    _description = 'Loan Application Document'

    @api.one
    def draft_to_verified(self):
        if not self.document:
            raise ValidationError(_('You must upload the document for %s.' % (self.loan_type_doc_id.name)))
        self.write({'state': 'verified', 'verified_date': datetime.datetime.now(), 'verified_user_id': self._uid})

    @api.one
    def verified_to_approved(self):
        self.write({'state': 'approved', 'approved_date': datetime.datetime.now(), 'approved_user_id': self._uid})

    @api.one
    def cancel(self):
        self.write({'state': 'cancel'})

    @api.one
    def reset(self):
        self.write({'state': 'draft'})

    @api.one
    def approved_reset(self):
        self.write({'state': 'verified'})

    loan_type_doc_id = fields.Many2one("loan.document", "Name", required=True)
    loan_app_id = fields.Many2one('loan.application', string="Loan Application")
    employee_id = fields.Many2one('hr.employee', related="loan_app_id.employee_id", string="Employee")
    document = fields.Binary('Document')
    file_name = fields.Char('File Name')
    verified_user_id = fields.Many2one('res.users', string="Verified User", readonly=True)
    approved_user_id = fields.Many2one('res.users', string="Approved User", readonly=True)
    verified_date = fields.Datetime("Verified Date", readonly=True)
    approved_date = fields.Datetime("Approved Date", readonly=True)
    state = fields.Selection([
                              ('draft', 'Draft'),
                              ('verified', 'Verified'),
                              ('approved', 'Approved'),
                              ('reset', 'Reset'),
                              ('cancel', 'Cancel')], string="State", default='draft')


class applicant_category(models.Model):
    _name = 'applicant.category'
    _description = 'Applicant Category'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if self._context.get('loan_type_id'):
            loan_type_rec = self.env['loan.type'].browse(self._context.get('loan_type_id'))
            lst_app_categ = [x.id for x in loan_type_rec.app_categ_ids]
            args += [('id', 'in', lst_app_categ)]
        return super(applicant_category, self).name_search(name, args)

    name = fields.Char("Name", required=True)
    loan_doc_ids = fields.Many2many('loan.document', 'loan_app_categ_id',
                                    'loan_app_doc_id', string='Documents')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
