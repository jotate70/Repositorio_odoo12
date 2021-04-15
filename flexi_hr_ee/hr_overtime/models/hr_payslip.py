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
    def action_payslip_done(self):
        self.compute_sheet()
        overtime_id = self.env['hr.employee.overtime']
        for each in self.employee_overtime_ids:
            ot_ids = overtime_id.search([('id', '=', each.id)])
            for each_ot_id in ot_ids:
                each_ot_id.update({'state': 'paid', 'payslip_id': self.id})
        return self.update({'state': 'done', 'paid': True})

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_employee_overtime_ids(self):
        emp_overtime_ids = self.env['hr.employee.overtime'].sudo().search([
                        ('employee_id', '=', self.employee_id.id),
                        ('date', '>=', self.date_from),
                        ('date', '<=', self.date_to),
                        ('state', '=', 'approved')
                        ])
        self.employee_overtime_ids = emp_overtime_ids

    employee_overtime_ids = fields.One2many('hr.employee.overtime', 'payslip_id', compute='compute_employee_overtime_ids',
                                     string='Penalty')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: