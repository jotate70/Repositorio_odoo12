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

from odoo import tools
from odoo import api, fields, models

class KRAnalysisReport(models.Model):
    _name = "kra.analysis.report"
    _description = "KRA Analysis Report"
    _auto = False

    week_nu = fields.Integer(string="Week Number", readonly=True)
    month = fields.Integer(string="Month", readonly=True)
    year = fields.Char(string="Year", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    job_id = fields.Many2one('hr.job', string="Job Position", readonly=True)
    reviewer_plan = fields.Selection(string="Reviewer Plan Selection",
                                               selection=[("week", "Weekly"), ("month", "Monthly"), ("year", "Yearly")])
    self_total = fields.Float(string="Employee Rating", readonly=True)
    manager_total = fields.Float(string="Manager Rating", readonly=True)
    hr_total = fields.Float(string="HR Rating", readonly=True)
    final_score = fields.Float(string="Final Score", readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(kqr.id) as id,
            CASE WHEN sum(kqr.self_rating) is not null THEN sum(kqr.self_rating) ELSE 0 END as self_total,
            CASE WHEN sum(kqr.manager_rating) is not null THEN sum(kqr.manager_rating) ELSE 0 END as manager_total,
            CASE WHEN sum(kqr.hr_rating) is not null THEN sum(kqr.hr_rating) ELSE 0 END as hr_total,
            sum(CASE WHEN kqr.self_rating is not null THEN kqr.self_rating ELSE 0 END+
                CASE WHEN kqr.manager_rating is not null THEN kqr.manager_rating ELSE 0 END+
                CASE WHEN kqr.hr_rating is not null THEN kqr.hr_rating ELSE 0 END) as final_score,
            ke.department_id as department_id,
            ke.job_id as job_id,
            ke.reviewer_plan,
            ke.employee_id as employee_id,
            ke.month as month,
            ke.year as year,
            ke.week_nu as week_nu
        """
        for field in fields.values():
            select_ += field

        from_ = """
                   kra_question_rating kqr
                   join kra_evaluation ke on (kqr.rating_id=ke.id)
                   join hr_employee emp on ke.employee_id = emp.id
                   join hr_department dept on ke.department_id = dept.id
                   join hr_job job on ke.job_id = job.id
                    %s
               """ % from_clause

        groupby_ = """
                    ke.employee_id,
                    ke.month,
                    ke.year,
                    ke.week_nu,
                    ke.reviewer_plan,
                    ke.department_id,
                    ke.job_id %s
                """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE ke.employee_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
