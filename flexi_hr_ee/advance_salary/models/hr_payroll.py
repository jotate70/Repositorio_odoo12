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


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_done(self):
        self.compute_sheet()
        payment_id = self.env['salary.payment']
        sal_req_id = self.env['hr.advance.salary.request']
        if self.salary_pay_ids or self.adv_sal_req_ids:
            for each in self.salary_pay_ids:
                payment_ids = payment_id.search([('id', '=', each.id)])
                for each_id in payment_ids:
                    if not each_id.payslip_id:
                        each_id.update({'state': 'deducted', 'payslip_id': self.id})
                sal_payment_ids = payment_id.search_count([
                                                           ('state', '=', 'deducted'),
                                                           ('adv_sal_req_id', '=', each.adv_sal_req_id.id)])
                if sal_payment_ids == each.adv_sal_req_id.no_of_installment:
                    each.adv_sal_req_id.update({'state': 'closed'})
            for adv_sal in self.adv_sal_req_ids:
                adv_ids = sal_req_id.search([('id', '=', adv_sal.id)])
                for salary in adv_ids:
                    salary.update({'state': 'paid', 'payslip_id': self.id})
            return self.update({'state': 'done', 'paid': True})

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def salary_cheque(self):
        sal_payment_ids = self.env['salary.payment'].search([
                                                    ('state','=', 'draft'),
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

    salary_pay_ids = fields.One2many('salary.payment', 'adv_sal_req_id', compute="salary_cheque",
                                      string='Payment By')
    adv_sal_req_ids = fields.One2many('hr.advance.salary.request', 'payslip_id', compute='compute_salary_next_sal',
                                      string='Payment By', store=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: