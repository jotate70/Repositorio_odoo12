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


class employee_late_penalty(models.Model):
    _name = "employee.late.penalty"
    _rec_name = 'employee_id'

    @api.multi
    def approved(self):
        self.state = 'approve'

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    check_in = fields.Char(string="Actual Check in")
    late_min = fields.Char(string="Late Check in")
    difference = fields.Char(string="Difference")
    date = fields.Date(string="Date")
    penalty_amt = fields.Float(string="Penalty Amount", store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('approve','Approved'),
                              ('cancel', 'Cancelled'),
                              ('deduct', 'Deducted')], string="State")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: