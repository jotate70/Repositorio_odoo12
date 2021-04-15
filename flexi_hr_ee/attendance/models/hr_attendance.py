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


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.constrains('check_in')
    def _check_timesheet_entry_previous_day(self):
        attendance_list = []
        for each in self.search([('employee_id', '=', self.employee_id.id)], order="id desc"):
            if each.check_in.date() != datetime.now().date():
               attendance_list.append(each.id)
        
        if attendance_list:
            past_date = self.browse([attendance_list[0]]).check_in.date()
            attendance_setting_id = self.env['res.config.settings'].sudo().search([],order="id desc", 
                                                                                  limit=1)
            timesheet_ids = self.env['account.analytic.line'].search([('employee_id', '=', self.employee_id.id), 
                                                                      ('date', '=', past_date)])
            if  timesheet_ids:
                attendance_ids = self.search([
                                            ('check_in', '>=', str(past_date) + " 00:00:00"),
                                            ('check_out', '<=', str(past_date) + " 23:59:59"),
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
                    raise exceptions.ValidationError(_('Difference between attendance and timesheet is "%s" ,its exceeding the limit of "%s".\
                    Please check your timehseet entries'
                                        % ("%.2f" %(diff_btw),"%.2f" %(attendance_setting_id.allow_diff_attendance_timesheet))))
            if not timesheet_ids:
                raise exceptions.ValidationError(_('Please fill the timesheet for "%s"'
                                    %past_date))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: