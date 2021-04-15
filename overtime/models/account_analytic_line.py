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
from odoo.exceptions import Warning


class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'

    @api.one
    def approve_timesheet(self):
        self.state = 'approved'

    @api.one
    def send_to_manager(self):
        attendance_setting_id = self.env['res.config.settings'].sudo().search([],order="id desc", 
                                                                              limit=1)
        docs = []
        product_list = []
        timesheet_ids = self.search([('date', '=', self.date),
                                     ('employee_id', '=', self.employee_id.id)])
        attendance_ids = self.env['hr.attendance'].search([
                                    '|',('check_in', '>=', self.date),
                                    ('check_out', '<=', self.date),
                                    ('employee_id', '=', self.employee_id.id)])
        attendance_hours = 0
        for each_rec in attendance_ids:
            from_dt = False
            to_dt = False
            if each_rec.check_in:
                from_dt = fields.Datetime.from_string(each_rec.check_in)
            if each_rec.check_out:
                to_dt = fields.Datetime.from_string(each_rec.check_out)
            if from_dt and to_dt:
                diff = to_dt - from_dt
                attendance_hours += diff.seconds/3600
        timesheet_working_hours = 0
        for each in timesheet_ids:
            timesheet_working_hours += each.unit_amount
        diff_btw = attendance_hours - timesheet_working_hours
        if attendance_setting_id.allow_diff_attendance_timesheet \
        and diff_btw > attendance_setting_id.allow_diff_attendance_timesheet:
            raise Warning(_('Difference between attendance and timesheet is "%s" ,its exceeding the limit of "%s".'
                                        % ("%.2f" %(diff_btw),"%.2f" %(attendance_setting_id.allow_diff_attendance_timesheet))))
        self.state = 'send_to_manager'
    @api.one
    def cancel_timesheet(self):
        self.state = 'draft'

    state = fields.Selection([('draft', 'Draft'),
                              ('send_to_manager', 'Waiting For Manager Approval'),
                              ('approved', 'Approved')], default='draft', string="State")


class Task(models.Model):
    _inherit = "project.task"

    @api.depends('stage_id', 'timesheet_ids.unit_amount', 'planned_hours', 'child_ids.stage_id',
                 'child_ids.planned_hours', 'child_ids.effective_hours', 'child_ids.timesheet_ids.unit_amount',
                 'timesheet_ids.state')
    
    def _hours_get(self):
        for task in self.sorted(key='id', reverse=True):
            children_hours = 0.0
            for child_task in task.child_ids:
                if child_task.stage_id and child_task.stage_id.fold:
                    children_hours += child_task.effective_hours + child_task.children_hours
                else:
                    children_hours += max(child_task.planned_hours, child_task.effective_hours + child_task.children_hours)
            task.children_hours = children_hours
            effective_hours = 0
            for each in task.sudo().timesheet_ids:
                if each.state == 'approved':
                    effective_hours += each.unit_amount
            task.effective_hours = effective_hours # use 'sudo' here to allow project user (without timesheet user right) to create task
            task.remaining_hours = task.planned_hours - task.effective_hours - task.children_hours
            task.total_hours = max(task.planned_hours, task.effective_hours)
            task.total_hours_spent = task.effective_hours + task.children_hours
            task.delay_hours = max(-task.remaining_hours, 0.0)

            if task.stage_id and task.stage_id.fold:
                task.progress = 100.0
            elif (task.planned_hours > 0.0):
                task.progress = round(100.0 * (task.effective_hours + task.children_hours) / task.planned_hours, 2)
            else:
                task.progress = 0.0

    remaining_hours = fields.Float(compute='_hours_get',  string='Remaining Hours', help="Total remaining time, can be re-estimated periodically by the assignee of the task.")
    effective_hours = fields.Float(compute='_hours_get',  string='Hours Spent', help="Computed using the sum of the task work done.")
    progress = fields.Float(compute='_hours_get',  string='Progress', group_operator="avg")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: