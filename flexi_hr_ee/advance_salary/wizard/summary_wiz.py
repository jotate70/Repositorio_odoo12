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

from odoo import models, api, fields, _
from datetime import date,datetime


YEARS = []
for year in range(int(date.today().strftime('%Y')) , int(date.today().strftime('%Y')) + 10):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), 
          ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'), 
          ('11', 'November'), ('12', 'December')]


class summary_wiz(models.TransientModel):
    _name = 'summary.wiz'

    view_by = fields.Selection([('employee','Employee'),
                                ('state','State'),
                                ('month','Month')], default='employee', required=True)
    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    employee_ids = fields.Many2many('hr.employee',
                                    'hr_emp_sum_wiz_rel', 
                                    'emp_id', 'wiz_id' ,string="Employee")
    state = fields.Selection([('draft', 'Draft'),
                              ('sent_hr', 'Waiting for HR Manager'),
                              ('sent_admin','Waiting for Manager'),
                              ('approved', 'Waiting For Disbursement'),
                              ('reject', 'Rejected'),
                              ('paid', 'Paid'),
                              ('closed','Closed')], default='paid', string="State")
    summary_month = fields.Selection(PERIOD, string="Required Month", default=date.today().strftime('%m'))
    required_year = fields.Selection(YEARS, string="Required Year",default=date.today().strftime('%Y'))

    @api.multi
    def summary_details(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
                'ids': self.ids,
                'model': 'summary.wiz',
                'form': data
                }
        return self.env.ref('flexi_hr_ee.report_summary_wiz').report_action(self, data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: