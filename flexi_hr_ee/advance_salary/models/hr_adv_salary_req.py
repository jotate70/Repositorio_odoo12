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

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import time 
from odoo.exceptions import ValidationError
from lxml import etree
from odoo.osv.orm import setup_modifiers

YEARS = []

for year in range(int(date.today().strftime('%Y')) , int(date.today().strftime('%Y')) + 10):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'Jan'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Apr'), ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'),
          ('08', 'Aug'), ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')]


class hr_advance_salary_request(models.Model):
    _name = "hr.advance.salary.request"
    _inherit = 'mail.thread'
    _description = 'HR Advance Salary Request'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if not vals.get('request_amt') or vals.get('request_amt') <= 0.00:
            raise ValidationError(_('Please enter the requested  amount.'))
        advance_num = self.env['ir.sequence'].next_by_code('advance.salary.request.num')
        if advance_num:
            vals.update({'name': advance_num})
        return super(hr_advance_salary_request, self).create(vals)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    request_date = fields.Date(string="Request Date", default=datetime.today().strftime('%Y-%m-%d'), readonly=True)
    req_year = fields.Integer(string="Req. Year", compute="compute_year_of_req", store=True)
    approved_date = fields.Date(string="Approved Date", readonly=True)
    disburse_date = fields.Date(string="Disburse Date", readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('sent_hr', 'Waiting for Manager Approval'),
                              ('sent_admin','Waiting for Approval'),
                              ('approved', 'Approved'),
                              ('reject', 'Rejected'),
                              ('paid', 'Paid'),
                              ('closed', 'Closed'),
                              ('cancelled','Cancelled')], default='draft', string="State")
    name = fields.Char('Name')
    request_amt = fields.Float(string="Requested Amount", required=True)
    required_month = fields.Selection(PERIOD, string="Required Month", default=date.today().strftime('%m'))
    required_year = fields.Selection(YEARS, string="Required Year",default=date.today().strftime('%Y'))
    approved_amt = fields.Float(string="Approved Amount")
    req_reason = fields.Text(string="Reason for Request", required=True)
    reason = fields.Text(string="Reason")
    payment_by = fields.Selection([('next_salary', 'Next Salary'),
                                   ('cheque', 'Cheque')],
                                  default='cheque', string="Payment By")
    no_of_installment = fields.Integer(string="No. of Installment", default=1 , store=True)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    move_id = fields.Many2one('account.move', string="Journal", readonly=True)
    req_count = fields.Integer(stirng="Request Count", compute='get_req_count')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', readonly=True)
    salary_payment_ids = fields.One2many('salary.payment', 'adv_sal_req_id',
                                      string='Salary Payment')
    next_sal_date = fields.Date(string="Next Salary Date", store=True)
    

    @api.model
    def default_get(self, field_name):
        res = super(hr_advance_salary_request, self).default_get(field_name)
        if not self._context.get('emp_form'):
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
            res.update({'employee_id': employee.id})
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(hr_advance_salary_request, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        erp_magr_gid = self.env.ref('base.group_erp_manager').id
        user_group_ids = self.env['res.users'].browse(self._uid).groups_id.ids
        doc = etree.XML(res['arch'])
        if erp_magr_gid not in user_group_ids:
            nodes = doc.xpath("//field[@name='no_of_installment']")
            for node in nodes:
                node.set('readonly', '1')
                setup_modifiers(node, res['fields']['no_of_installment'])
            nodes =  doc.xpath("//field[@name='salary_payment_ids']")
            for node in nodes:
                node.set('readonly', '1')
                setup_modifiers(node, res['fields']['salary_payment_ids'])
        hr_magr_gid = self.env.ref('hr.group_hr_manager').id
        if hr_magr_gid not in user_group_ids:
            nodes = doc.xpath("//field[@name='approved_amt']")
            for node in nodes:
                node.set('readonly', '1')
                setup_modifiers(node, res['fields']['approved_amt'])
        res['arch'] = etree.tostring(doc)
        return res

    @api.one
    @api.depends('request_date')
    def compute_year_of_req(self):
        self.req_year = self.request_date.year
        return self.req_year

    @api.constrains('request_amt')
    def check_request_amt_limit(self):
        if self.employee_id.advance_salary_limit and self.employee_id.job_id.advance_salary_limit:
            if self.request_amt > self.employee_id.advance_salary_limit:
                raise ValidationError(_("You are exceeding your advance salary limit of %d. Enter valid request amount."\
                                  %self.employee_id.advance_salary_limit))
        if self.employee_id.advance_salary_limit and not self.employee_id.job_id.advance_salary_limit:
            if self.request_amt > self.employee_id.advance_salary_limit:
                raise ValidationError(_("You are exceeding your advance salary limit of %d. Enter valid request amount."\
                                  %self.employee_id.advance_salary_limit)) 
        if not self.employee_id.advance_salary_limit and self.employee_id.job_id.advance_salary_limit:
            if self.request_amt > self.employee_id.job_id.advance_salary_limit:
                raise ValidationError(_("You are exceeding your advance salary limit of %d. Enter valid request amount."\
                                  %self.employee_id.job_id.advance_salary_limit))
        if self.employee_id.contract_id and self.request_amt > self.employee_id.contract_id.wage * 36:
            raise ValidationError(_("As per your Wage, you can't request amount more than %d." %(self.employee_id.contract_id.wage * 36))) 

    @api.multi
    def get_req_count(self):
        for each in self:
            if each.employee_id:
                each.req_count = each.search_count([('employee_id', '=', each.employee_id.id)])
    
    @api.multi
    def request_related_employee(self):
        return {
                'type': 'ir.actions.act_window',
                'name': _('Advance Salary Request'),
                'res_model': 'hr.advance.salary.request',
                'view_type': 'form',
                'view_mode': 'tree',
                'target': 'current',
                'domain': [('employee_id', '=', self.employee_id.id)]
                }

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda reg: reg.state not in ('draft','reject'))):
            raise ValidationError(_("You cannot delete any salary request before rejecting it."))
        return super(hr_advance_salary_request, self).unlink()

    @api.constrains('approved_amt')
    def check_approved_amt(self):
        if self.approved_amt > self.request_amt:
            raise ValidationError(_('You should approve less amount than requested amount(%d).'%self.request_amt))

    @api.constrains('no_of_installment')
    def check_no_of_installment(self):
        if self.no_of_installment == 0:
            raise ValidationError(_('"Number Of Installments" should not be zero.'))
        config_id = self.env['res.config.settings'].search(([]), order='id desc', limit=1)
        if config_id and self.no_of_installment > config_id.max_term:
            raise ValidationError(_("You can't enter No. of Installments more than %d." %config_id.max_term))
                
        

    @api.one
    def sent_hr(self):
        if self.employee_id.req_count and self.employee_id.job_id.req_count \
        and self.req_count > self.employee_id.req_count:
            raise ValidationError(_('You have already requested %d times'
                              %self.employee_id.req_count))
        if self.employee_id.req_count and not self.employee_id.job_id.req_count \
         and self.req_count > self.employee_id.req_count:
            raise ValidationError(_('You have already requested %d times'
                              %self.employee_id.req_count))
        if not self.employee_id.req_count and self.employee_id.job_id.req_count \
        and self.req_count > self.employee_id.job_id.req_count:
            raise ValidationError(_('You have already requested %d times'
                              %self.employee_id.job_id.req_count))
        self.state = 'sent_hr'

    @api.multi
    def sent_admin(self):
        if self.approved_amt <= 0:
            raise ValidationError(_('Please enter "Approved Amount".'))
        self.state = 'sent_admin'

    @api.multi
    def disburse_amt(self):
        if int(date.today().month) != int(self.required_month):
            raise ValidationError(_('You can not pay before "%s"'%(datetime.strptime(self.required_month, '%m')).strftime('%B')))
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Advance Salary Disbursement'),
                'res_model': 'disburse.amt.wiz',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'
                }

    @api.one
    def cancel_request(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
        if employee.id == self.employee_id.id:
            self.state = 'cancelled'
        else:
            raise ValidationError(_('You have no rights to cancel the request.'))

    @api.one
    def approval_done(self):
        date_list = []
        config_id = self.env['res.config.settings'].search(([]), order='id desc', limit=1)
        interest = 0.0
        if config_id:
            interest = (self.approved_amt * config_id.interest_rate) / 100
        if self.payment_by == 'cheque':
            for line in range(1, int(self.no_of_installment)+1):
                if self.no_of_installment:
                    amount = (self.approved_amt + interest) / self.no_of_installment
                date_list.append((0, 0, {
                                'date': (date.today().replace(month=int(self.required_month), year=int(self.required_year)) +\
                                          relativedelta(months=line)).replace(day=1),
                                'amount': amount,
                                'state': 'draft',
                                'employee_id': self.employee_id.id,
                                'payment_by': self.payment_by,
                                'adv_sal_req_id': self.id
                                }))
        elif self.payment_by == 'next_salary':
            for line in range(1, int(self.no_of_installment)+1):
                if self.no_of_installment:
                    amount = (self.approved_amt + interest) / self.no_of_installment
                date_list.append((0, 0, {
                                'date': (date.today().replace(month=int(self.required_month), year=int(self.required_year)) + \
                                         relativedelta(months=line+1)).replace(day=1),
                                'amount': amount,
                                'employee_id': self.employee_id.id,
                                'state': 'draft',
                                'payment_by': self.payment_by
                                }))
        self.salary_payment_ids = date_list
        loan_app_ids = self.env['loan.application'].search([('employee_id', '=', self.employee_id.id),
                                                            ('state', '=', 'paid')])
        for line_deduct in self.salary_payment_ids:
            req_date = line_deduct.date.strftime('%m-%Y')
            for each_loan in loan_app_ids:
                for emi_lines in each_loan.loan_payment_ids:
                    for each_line in emi_lines:
                        loan_due_date = each_line.due_date.strftime('%m-%Y')
                        if loan_due_date == req_date \
                            and self.employee_id.contract_id \
                            and each_line.state == 'draft' \
                            and self.employee_id.contract_id.wage < line_deduct.amount + each_line.total:
                            self.salary_payment_ids = []
                            raise ValidationError(_('You are exceeding your wage limit.'))                      
                
        template = self.env.ref('flexi_hr_ee.email_advance_salary_template')
        if template:
            result=template.send_mail(self.ids[0], force_send=True)
        self.state = 'approved'
        self.approved_date = datetime.now().strftime('%Y-%m-%d')
        if self.approved_date:
            self.next_sal_date = (date.today() + relativedelta(months=1)).replace(day=1)

    @api.multi
    def approval_rejection(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Advance Salary Request Reject Reason'),
            'res_model': 'reject.request.reason',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }

#     @api.constrains('request_date')
#     def _check_request_date(self):
#         if self.request_date < datetime.now().strftime('%Y-%m-%d'):
#             raise ValidationError(_('Please enter valid Request Date.'))


class salary_payment(models.Model):
    _name = "salary.payment"

    date = fields.Date('Deduction Date', required=True)
    amount = fields.Float(string="Amount", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    payment_by = fields.Selection([('next_salary', 'Next Salary'),
                                   ('cheque', 'Cheque')],
                                  default='cheque', string="Payment By")
    adv_sal_req_id = fields.Many2one('hr.advance.salary.request', string="Request Id")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    state = fields.Selection([('draft', 'Draft'),
                              ('deducted', 'Deducted')],
                                  default='draft', string="Status", store=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: