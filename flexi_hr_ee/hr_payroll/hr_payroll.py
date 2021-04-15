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
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from calendar import monthrange


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('from_payslip'):
            args = args or []
            recs = self.browse()
            if name:
                recs = self.search([('name', 'ilike', name), ('employee_status', '!=', 'ex_emp')] + args, limit=limit)
            if not recs:
                recs = self.search([('employee_status', '!=', 'ex_emp')] + args, limit=limit)
            return recs.name_get()
        else:
            return super(hr_employee, self).name_search(name, args, operator, limit)


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    is_hourly_pay = fields.Boolean(string='Hourly Pay')


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

#     @api.constrains('date_from', 'date_to')
#     def _add_check_dates(self):
#         from_dt = fields.Datetime.from_string(self.date_from)
#         to_dt = fields.Datetime.from_string(self.date_to)
#         diff = to_dt - from_dt
#         month_last_day = monthrange(from_dt.year, from_dt.month)
#         if month_last_day:
#             if len(str(from_dt.month)) == 1:
#                 month_last_date = str(from_dt.year) + '-' + '0' + str(from_dt.month) + '-' + str(month_last_day[1]) + " 00:00:00"
#             else:
#                 month_last_date = str(from_dt.year) + '-' + str(from_dt.month) + '-' + str(month_last_day[1]) + " 00:00:00"
#         week_ago = from_dt + timedelta(days=7)
#         quarter_ago = from_dt + relativedelta(months=+3)
#         semi_annual_ago = from_dt + relativedelta(months=+6)
#         annual_ago = from_dt + relativedelta(months=+12)
#         if self.contract_id.schedule_pay == 'weekly':
#             if week_ago != to_dt:
#                 raise ValidationError(_("Please select the end date %s" % str(week_ago)))
# #         if self.contract_id.schedule_pay == 'monthly':
# #             if month_last_date != str(to_dt):
# #                 raise ValidationError(_("Please select the end date %s" %str(month_last_date)))
#         if self.contract_id.schedule_pay == 'quarterly':
#             if quarter_ago != to_dt:
#                 raise ValidationError(_("Please select the end date %s" % str(quarter_ago)))
#         if self.contract_id.schedule_pay == 'semi-annually':
#             if semi_annual_ago != to_dt:
#                 raise ValidationError(_("Please select the end date %s" % str(semi_annual_ago)))
#         if self.contract_id.schedule_pay == 'annually':
#             if annual_ago != to_dt:
#                 raise ValidationError(_("Please select the end date %s" % str(annual_ago)))
#         if any(self.filtered(lambda payslip: payslip.date_from > payslip.date_to)):
#             raise ValidationError(_("Payslip 'Date From' must be before 'Date To'."))

#     @api.multi
#     @api.depends('date_to', 'date_from', 'employee_id')
#     def _compute_employee_total_hours(self):
#         for payslip in self:
#             att_ids = self.env['hr.attendance'].search([('employee_id', '=', payslip.employee_id.id),
#                                             ('check_out', '>=', datetime.strptime(payslip.date_from, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')),
#                                             ('check_out', '<=', datetime.strptime(payslip.date_to, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')), ])
#             if att_ids:
#                 total_seconds = 0;
#                 for att in att_ids:
#                     record_time = str(timedelta(hours=att.worked_hours)).split(':')
#                     if record_time and len(record_time) >= 2:
#                         conv_time = datetime.strptime(record_time[0] + ':' + record_time[1], '%H:%M')
#                         if conv_time:
#                             total_seconds += conv_time.minute * 60 + conv_time.hour * 3600
#                 day = total_seconds // 86400
#                 hour = (total_seconds - (day * 86400)) // 3600
#                 minute = (total_seconds - ((day * 86400) + (hour * 3600))) // 60
#                 payslip.total_hours = str(hour + (24 * day)) + ':' + str(minute)

    @api.multi
    @api.depends('date_to', 'date_from', 'employee_id', 'contract_id.schedule_pay')
    def _compute_employee_working_days(self):
        for payslip in self:
            from_dt = fields.Datetime.from_string(payslip.date_from)
            to_dt = fields.Datetime.from_string(payslip.date_to)
            diff = to_dt - from_dt
            to_hour = 0
            day_list = []
            for working_hour in payslip.employee_id.resource_calendar_id.attendance_ids:
                if int(working_hour.dayofweek) not in day_list:
                    day_list.append(int(working_hour.dayofweek))
                to_hour += working_hour.hour_to - working_hour.hour_from
#                 current = time.time()
            working_days = 0
            hr_hoilday_unpaid = self.env['hr.leave'].search([
                                            ('date_from', '>=', payslip.date_from),
                                            ('date_to', '<=', payslip.date_to),
                                            ('holiday_status_id.name', '=', 'Unpaid'),
                                            ('state', '=', 'validate')])
            unpaid_days = 0
            for unpaid in hr_hoilday_unpaid:
                unpaid_from_dt = fields.Datetime.from_string(unpaid.date_from)
                unpaid_to_dt = fields.Datetime.from_string(unpaid.date_to)
                unpaid_diff = unpaid_to_dt - unpaid_from_dt
                for i in range(unpaid_diff.days + 1):
                    unpaid_date = unpaid_from_dt + timedelta(days=i)
                    if unpaid_date.weekday() in day_list:
#                         working_days += 1
                        unpaid_days += 1
            payslip.unpaid_leave_count = unpaid_days
            for i in range(diff.days + 1):
                date = from_dt + timedelta(days=i)
                if date.weekday() in day_list:
                    working_days += 1
            payslip.total_working_days = working_days
            actual_working_days = payslip.total_working_days - payslip.unpaid_leave_count
            if actual_working_days > 0:
                payslip.actual_working_days = actual_working_days

    @api.multi
    @api.depends('date_to', 'date_from', 'employee_id')
    def _compute_employee_ot_hours(self):
        for payslip in self:
            att_ids = self.env['account.analytic.line'].search([('employee_id', '=', payslip.employee_id.id),
                                            ('date', '>=', payslip.date_from),
                                            ('date', '<=', payslip.date_to),
                                           ])
            from_dt = fields.Datetime.from_string(payslip.date_from)
            to_dt = fields.Datetime.from_string(payslip.date_to)
            diff = to_dt - from_dt
            if att_ids:
                total_hour = 0;
                for att in att_ids:
                    total_hour += att.unit_amount
                to_hour = 0
                day_list = []
                for working_hour in payslip.employee_id.resource_calendar_id.attendance_ids:
                    if int(working_hour.dayofweek) not in day_list:
                        day_list.append(int(working_hour.dayofweek))
                    to_hour += working_hour.hour_to - working_hour.hour_from
                if len(day_list) != 0:
                    working_hour_per_day = to_hour / len(day_list)
                total_working_hours = working_hour_per_day * self.total_working_days
                ot_hour = 0
                if total_hour > total_working_hours:
                    ot_hour = total_hour - total_working_hours
                payslip.total_ot_hours = ot_hour

    @api.multi
    def action_payslip_done(self):
        self.compute_sheet()
        payment_id = self.env['salary.payment']
        sal_req_id = self.env['hr.advance.salary.request']
        for each in self.product_line_ids:
            if not each.payslip_id:
                each.update({
                            'state': 'paid',
                            'payslip_id': self.id})
        for each in self.salary_pay_ids:
            payment_ids = payment_id.search([('id', '=', each.id)])
            for each_id in payment_ids:
                if not each_id.payslip_id:
                    each_id.update({'state': 'deducted', 'payslip_id': self.id})
            sal_payment_ids = payment_id.search_count([
                                                   ('state', '=', 'deducted'),
                                                   ('adv_sal_req_id', '=', each.adv_sal_req_id.id)
                                                   ])
            if sal_payment_ids == each.adv_sal_req_id.no_of_installment:
                each.adv_sal_req_id.update({'state': 'closed'})
        for adv_sal in self.adv_sal_req_ids:
            adv_ids = sal_req_id.search([('id', '=', adv_sal.id)])
            for salary in adv_ids:
                salary.update({'state': 'paid', 'payslip_id': self.id})
        for each in self.loan_paymet_ids:
            each.write({'state': 'paid', 'payslip_id': self.id})
        return self.write({'state': 'done', 'paid': True})

    @api.multi
    def refund_sheet(self):
        for payslip in self:
            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.action_payslip_done()
        loans_emis = self.env['loan.payment'].search([('employee_id', '=', self.employee_id.id),
                                                      ('due_date', '>=', self.date_from),
                                                      ('due_date', '<=', self.date_to),
                                                      ('payslip_id', '=', self.id),
                                                      ('state', '=', 'paid'),
                                                      ('loan_app_id.state', '=', 'paid')])
        for loan in loans_emis:
             loan.write({'state': 'draft',
                         'payslip_id': False})
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_loan(self):
        loans_emis = self.env['loan.payment'].search([('employee_id', '=', self.employee_id.id),
                                                      ('due_date', '>=', self.date_from),
                                                      ('due_date', '<=', self.date_to),
                                                      ('state', '=', 'draft'),
                                                      ('loan_app_id.state', '=', 'paid')])
        self.loan_paymet_ids = loans_emis

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def salary_cheque(self):
        sal_payment_ids = self.env['salary.payment'].search([
                                                    ('state', '=', 'draft'),
                                                    ('adv_sal_req_id.employee_id', '=', self.employee_id.id),
                                                    ('date', '>=', self.date_from),
                                                    ('date', '<=', self.date_to),
                                                    ('adv_sal_req_id.state', '=', 'paid')])
        self.salary_pay_ids = sal_payment_ids

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_salary_next_sal(self):
        adv_sal_req_ids = self.env['hr.advance.salary.request'].sudo().search([
                                                    ('state', '=', 'approved'),
                                                    ('employee_id', '=', self.employee_id.id),
                                                    ('payment_by', '=', 'next_salary'),
                                                    ('next_sal_date', '>=', self.date_from),
                                                    ('next_sal_date', '<=', self.date_to)])
        self.adv_sal_req_ids = adv_sal_req_ids

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_checklist_last_sal(self):
        last_sal_ids = self.env['emp.product.line'].sudo().search([
                        ('state', '=', 'collected'),
                        ('payment_by', '=', 'last_salary'),
                        ('product_exit_id.employee_id', '=', self.employee_id.id),
                        ('product_exit_id.leaving_date', '>=', self.date_from),
                        ('product_exit_id.leaving_date', '<=', self.date_to)
                        ])
        self.product_line_ids = last_sal_ids

    product_line_ids = fields.One2many('emp.product.line', 'payslip_id', compute='compute_checklist_last_sal',
                                      string='Checklist - Last Salary Payment')
    salary_pay_ids = fields.One2many('salary.payment', 'adv_sal_req_id', compute="salary_cheque",
                                      string='Payment By')
    adv_sal_req_ids = fields.One2many('hr.advance.salary.request', 'payslip_id', compute='compute_salary_next_sal',
                                      string='Payment By', store=True)
    loan_paymet_ids = fields.One2many('loan.payment', 'payslip_id', compute='_compute_loan',
                                      string='Loan EMI')
#     total_hours = fields.Char(string="Total Hours", compute='_compute_employee_total_hours')
    total_ot_hours = fields.Float(string="Total Overtime Hours", compute='_compute_employee_ot_hours')
    total_working_days = fields.Float(string="Total Working Days", compute='_compute_employee_working_days')
    actual_working_days = fields.Float(string="Actual Working Days", compute='_compute_employee_working_days')
    unpaid_leave_count = fields.Float(string="Unpaid Leave", compute='_compute_employee_working_days')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
