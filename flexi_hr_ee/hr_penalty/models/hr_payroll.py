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

from datetime import datetime, timedelta
from odoo import fields, models, api, exceptions, _


class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_penalty_ids(self):
        penalty_ids = self.env['employee.late.penalty'].sudo().search([
                        ('employee_id', '=', self.employee_id.id),
                        ('date', '>=', self.date_from),
                        ('date', '<=', self.date_to),
                        ('state', '=', 'approve')
                        ])
        self.emp_penalty_ids = penalty_ids

    emp_penalty_ids = fields.One2many('employee.late.penalty', 'payslip_id', compute='compute_penalty_ids',
                                      string='Penalty')

    @api.multi
    def action_payslip_done(self):
        res = super(hr_payslip, self).action_payslip_done()
        for each in self.emp_penalty_ids:
            each.state = 'deduct'
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: