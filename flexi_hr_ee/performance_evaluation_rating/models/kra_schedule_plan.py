# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
import datetime

class krascheduleplan(models.Model):
    _name = 'kra.schedule.plan'
    _description = 'Create KRA Schedule Plan Choosing Interval'
    _rec_name = 'interval'

    department_id = fields.Many2one('hr.department', string="Department", required=True)
    job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    interval = fields.Selection(string="Interval",selection=[("week", "Weekly"), ("month", "Monthly"), ("year", "Yearly")], default='week', required=True)
    kra_template_id = fields.Many2one('kra.template', string="KRA Template", required=True, )

    @api.multi
    @api.constrains('department_id', 'job_id')
    def _check_duplicate(self):
        schedule_record = [rec for rec in self.env['kra.schedule.plan'].search([('department_id','=',self.department_id.id), ('job_id','=',self.job_id.id)])]
        if len(schedule_record) > 1:
            raise Warning(
                _('You already created schedule plan for %s and %s'%(self.department_id.name,self.job_id.name)))

    @api.onchange('department_id','job_id')
    def _onchange_job_id(self):
        if self.department_id and self.job_id:
            template_id = self.env['kra.template'].search([('job_id','=',self.job_id.id),('department_id','=',self.department_id.id),('is_active','=',True)])
            if template_id:
                self.kra_template_id = template_id
            else:
                raise Warning(_('Please configure KRA tempalte for "%s" job position of "%s" department' % (self.job_id.name, self.department_id.name)))

    @api.model
    def _run_schedule_plan(self):
        week_nu = int(datetime.date.today().strftime("%V"))
        curr_month = datetime.date.today().month
        curr_year = datetime.date.today().year
        employee_evaluation = self.env['kra.evaluation']
        schedule_week = self.env['kra.schedule.plan'].search([('interval','=','week')])
        schedule_month = self.env['kra.schedule.plan'].search([('interval', '=', 'month')])
        schedule_year = self.env['kra.schedule.plan'].search([('interval', '=', 'year')])
        if schedule_week:
            for rec in schedule_week:
                emp_records = self.env['hr.employee'].search([('job_id','=',rec.job_id.id),('department_id','=',rec.department_id.id),])
                for emp in emp_records:
                    evaluation_record = employee_evaluation.search([('week_nu','=',week_nu),('year','=',curr_year),
                                                                ('job_id','=',rec.job_id.id),('reviewer_plan','=','week'),
                                                                ('department_id','=',rec.department_id.id),('employee_id','=',emp.id)])
                    self.callevluation_record(evaluation_record,employee_evaluation,rec,emp,week_nu,curr_month,curr_year)

        if schedule_month:
            for rec in schedule_month:
                emp_records = self.env['hr.employee'].search([('job_id','=',rec.job_id.id),('department_id','=',rec.department_id.id),])
                for emp in emp_records:
                    evaluation_record = employee_evaluation.search([('month','=',curr_month),('year','=',curr_year),
                                                                ('job_id','=',rec.job_id.id),('reviewer_plan','=','month'),
                                                                ('department_id','=',rec.department_id.id),('employee_id','=',emp.id)])
                    self.callevluation_record(evaluation_record,employee_evaluation,rec,emp,week_nu,curr_month,curr_year)

        if schedule_year:
            for rec in schedule_year:
                emp_records = self.env['hr.employee'].search(
                    [('job_id', '=', rec.job_id.id), ('department_id', '=', rec.department_id.id), ])
                for emp in emp_records:
                    evaluation_record = employee_evaluation.search(
                        [('year', '=', curr_year), ('job_id', '=', rec.job_id.id),
                         ('department_id', '=', rec.department_id.id), ('employee_id', '=', emp.id),('reviewer_plan','=','year'),])
                    self.callevluation_record(evaluation_record,employee_evaluation,rec,emp,week_nu,curr_month,curr_year)

    def callevluation_record(self,evaluation_record,employee_evaluation,rec,emp,week_nu,curr_month,curr_year):
        if not evaluation_record:
            lst = []
            for record in rec.kra_template_id.questions_ids:
                lst.append((0, 0, {'questions': record.questions}))
            employee_evaluation.create({'employee_id': emp.id,
                                        'department_id': rec.department_id.id,
                                        'job_id': rec.job_id.id,
                                        'reviewer_id': emp.parent_id.id,
                                        'week_nu': week_nu,
                                        'month': curr_month,
                                        'year': curr_year,
                                        'reviewer_plan': rec.interval,
                                        'kra_template_id': rec.kra_template_id.id,
                                        'que_rating_ids': lst})



