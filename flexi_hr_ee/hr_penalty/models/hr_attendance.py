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

from datetime import datetime, timedelta, date
from odoo import fields, models, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
import pytz
import math


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.multi
    def get_date(self, date_time):
        if self.env.user.tz:
            tz = pytz.timezone(self.env.user.tz)
        else:
            tz = pytz.utc
        c_time = datetime.now(tz)
        hour_tz = int(str(c_time)[-5:][:2])
        min_tz = int(str(c_time)[-5:][3:])
        sign = str(c_time)[-6][:1]
        if sign == '-':
            date = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=hour_tz, minutes=min_tz)
        if sign == '+':
            date = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=hour_tz, minutes=min_tz)
        #         date_from = pytz.utc.localize(datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(tz)
        #         date = date_from.strftime("%Y-%m-%d %H:%M:%S")
        return date

    @api.model
    def create(self, vals):
        res = super(HrAttendance, self).create(vals)
        SQL = """SELECT check_in AT TIME ZONE 'GMT' as check_in  from hr_attendance where id = %d
                    """ % (res.id)
        self._cr.execute(SQL)
        ressult = self._cr.dictfetchall()
        sign_in = str(ressult[0].get('check_in')).split('+')[0]
        attendance_setting_id = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)
        today_weekday = datetime.strptime(str(sign_in),"%Y-%m-%d %H:%M:%S").weekday()
        work_from = []
        work_to = []
        start_work = []
        end_work = []
        if res.employee_id.resource_calendar_id:
            for working_hour in res.employee_id.resource_calendar_id.attendance_ids: 
                if int(working_hour.dayofweek) == today_weekday:
#                     work_from.append(working_hour.hour_from)
                    start_min = math.ceil(float(("0."+str(working_hour.hour_from).split(".")[1]))*60)
                    end_min =  math.ceil(float(("0."+str(working_hour.hour_to).split(".")[1]))*60)
                    work_from.append((str(int(working_hour.hour_from)) + ":" +str(int(attendance_setting_id.allow_late_mins) + start_min)))
                    work_to.append((str(int(working_hour.hour_to)) + ":" +str(end_min)))
                    start_work.append(str(working_hour.hour_from))
                    end_work.append(str(working_hour.hour_to))

        dt=datetime.strptime(sign_in,"%Y-%m-%d %H:%M:%S").time()
        check_in_hour = str(dt.hour) + ":" + str(dt.minute)
        i = 0
        for d in work_from:
            emp_hour  = int(d.split(":")[0])
            emp_ext_min = math.floor(float("0."+str(int(d.split(":")[1])/60).split(".")[1])*60)
            check_date = datetime.now().replace(hour = emp_hour,minute = emp_ext_min)
            work_to_hour = int(work_to[i].split(":")[0])
            work_to_ext_hour = int(str(int(work_to[i].split(":")[1])/60).split(".")[0])
            work_to_ext_min = math.ceil(float(str("0."+str(int(work_to[i].split(":")[1])/60).split(".")[1]))*60)
            work_to_date = datetime.now().replace(hour = work_to_hour + work_to_ext_hour, minute = work_to_ext_min)

            emp_check_in_hour = int(check_in_hour.split(":")[0])
            emp_check_in_min = int(check_in_hour.split(":")[1])
            emp_check_date = datetime.now().replace(hour = emp_check_in_hour,minute = emp_check_in_min)
            late_time = emp_check_date - check_date
            late_time = str(late_time).split(".")[0]
            if emp_check_date > check_date and emp_check_date < work_to_date:
                now = datetime.now()
                p_ids = self.env['employee.late.penalty'].search([
                                                                ('employee_id', '=', res.employee_id.id)])
                amount = 0
                if attendance_setting_id.apply_penalty_after and len(p_ids) >= attendance_setting_id.apply_penalty_after:
                    amount = attendance_setting_id.penalty_amount


                if not attendance_setting_id.apply_penalty_after:
                    amount = attendance_setting_id.penalty_amount

                date_from = datetime.strftime(check_date, DTF)
                date_from = self.get_date(date_from)
                date_to = datetime.strftime(work_to_date, DTF)
                date_to = self.get_date(date_to)
                attend_ids = self.env['hr.attendance'].search([('check_out', '>=', str(date_from)),
                                                               ('check_out', '<=', str(date_to)),
                                                               ('employee_id', '=', res.employee_id.id),
                                                               ('id', '!=', res.id)])
                if not attend_ids:
                    self.env['employee.late.penalty'].create({
                       'employee_id': res.employee_id.id,
                       'check_in': int(d.split(":")[0]),
                       'late_min': check_in_hour,
                       'difference': late_time,
                       'date': res.check_in,
                       'penalty_amt': amount,
                       'state': 'draft'
                    })
                    if attendance_setting_id.rule_to_count_leave:
                        if attendance_setting_id.apply_panelty_on_leave and len(
                                p_ids) >= attendance_setting_id.apply_panelty_on_leave:
                            date_start = datetime.now().replace(hour=int(start_work[0].split('.')[0]), minute=00,
                                                                second=00)
                            date_end = datetime.now().replace(hour=int(end_work[1].split(".")[0]), minute=00, second=00)
                            record_id = self.env['hr.leave'].create({
                                'employee_id': res.employee_id.id,
                                # 'type': 'remove',
                                'holiday_status_id': self.env.ref('hr_holidays.holiday_status_unpaid').id,
                                'holiday_type': 'employee',
                                'request_date_from': date_start,
                                'request_date_to': date_end,
                                'name': "Late Panelty on Leave",
                            })
            i = i + 1
        return res


class hr_employee(models.Model):
    _inherit = "hr.employee"

    panelty_count = fields.Integer(string="Late Panelty", compute="get_late_panelty")

    @api.multi
    def get_late_panelty(self):
        for each in self:
            each.panelty_count = self.env['employee.late.penalty'].search_count([('employee_id','=',each.id)])

    @api.multi
    def late_coming_penalty(self):  
        return {
                'name': "Late Coming Details",
                "type": "ir.actions.act_window",
                "res_model": "employee.late.penalty",
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': [('employee_id', '=', self.id)]
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: