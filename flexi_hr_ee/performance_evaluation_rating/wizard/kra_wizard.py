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

from odoo import models,fields,api,_
import datetime

class kraevaluationwizard(models.Model):
    _name = 'kra.evaluation.wiz'
    _description = 'KRA Evaluation Wizard for Report'

    def get_years(self):
        year_list = []
        for i in range(2000, 2050):
            year_list.append((i, str(i)))
        return year_list

    def get_weeks(self):
        week_list = []
        for i in range(1, 54):
            week_list.append((i, str(i)))
        return week_list

    department_ids = fields.Many2many('hr.department', string="Department")
    job_ids = fields.Many2many('hr.job', string="Job Position")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    reviewer_plan = fields.Selection(string="Reviewer Plan Selection",
                                               selection=[("week", "Weekly"), ("month", "Monthly"), ("year", "Yearly")],
                                               default='week',  required=True)
    month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                              (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                              (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], default=datetime.datetime.now().month,
                             string='Month', required=True)
    year = fields.Selection(selection='get_years', string='Year',default=datetime.datetime.now().year, required=True)
    week_nu = fields.Selection(selection='get_weeks', string='Week Number', default=datetime.datetime.now().isocalendar()[1], required=True)
    select_report = fields.Selection([("detail", "Evaluation Detail"),("summary","Evaluation Summary")], string='View By', default="summary")

    @api.multi
    def action_print(self):
        datas = {
            'id': self.id
        }
        return self.env.ref('performance_evaluation_rating.kra_evaluation_wiz_report').report_action(self, data=datas)
