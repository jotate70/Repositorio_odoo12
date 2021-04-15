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

from odoo import models, fields, api,_
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class hr_employee_overtime(models.Model):
    _name= "hr.employee.overtime"
    _inherit = 'mail.thread'
    _description = 'HR Employee Overtime'
    _order = 'id desc'

    name = fields.Char(string="Name")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    date = fields.Date(string="Date", default=date.today())
    based_on = fields.Selection([('weekday', 'Weekday'),
                                 ('weekend', 'Weekend')],'Based On')
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved'),
                              ('paid', 'Paid'),
                              ('cancelled', 'Cancelled')], default='draft', string="State", track_visibility="onchange")
    ot_rate = fields.Float(string='OT Rate')
    overtime = fields.Float(string="Overtime")
    payslip_id = fields.Many2one('hr.payslip', string="Related Payslip") 

    @api.model
    def create(self, vals):
        ot_name = self.env['ir.sequence'].next_by_code('hr.employee.overtime')
        if ot_name:
            vals.update({'name': ot_name})
        return super(hr_employee_overtime, self).create(vals)

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
            date = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=hour_tz, minutes=min_tz)
        if sign == '+':
            date = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=hour_tz, minutes=min_tz)
        return date

    @api.model
    def generate_employee_overtime(self):
        config_id = self.env['res.config.settings'].search([], limit=1, order="id desc")
        for each in self.env['hr.employee'].search([]):
            is_weekday = False
            ot_rate = 0.0
            resource_calendar_id = each.resource_calendar_id if each.resource_calendar_id \
                                   else config_id.resource_calendar_id if config_id.resource_calendar_id \
                                   else False
                                   
            if resource_calendar_id:
                res_calendar_attendance_id = False
                for each_res_calendar_attendance in resource_calendar_id.attendance_ids:
                    if int(each_res_calendar_attendance.dayofweek) == date.today().weekday():
                        if not res_calendar_attendance_id or \
                           (res_calendar_attendance_id and res_calendar_attendance_id.hour_to <= each_res_calendar_attendance.hour_to):
                            res_calendar_attendance_id = each_res_calendar_attendance
                        is_weekday = True

                ot_time_difference_limit = config_id.ot_time_difference_limit if config_id and config_id.ot_time_difference_limit else 0.0
                if res_calendar_attendance_id:
                    ot_rate = each.weekday_ot_rate if each.weekday_ot_rate \
                                      else config_id.weekday_ot_rate if (config_id and config_id.weekday_ot_rate)\
                                      else 0.0
                else:
                    ot_rate = each.weekend_ot_rate if each.weekend_ot_rate \
                                      else config_id.weekend_ot_rate if (config_id and config_id.weekend_ot_rate)\
                                      else 0.0

            hour_to_hr = (str(res_calendar_attendance_id.hour_to).split(".")[0] if '.' in str(res_calendar_attendance_id.hour_to)\
                         else str(res_calendar_attendance_id.hour_to)) if res_calendar_attendance_id else '00'
            hour_to_minute = (str(int(float(str(res_calendar_attendance_id.hour_to).split(".")[1]) * 0.6)) if '.' in str(res_calendar_attendance_id.hour_to)\
                               else '00') if res_calendar_attendance_id else '00'
                               
            date_to_add = datetime.now().replace(hour=int(hour_to_hr),minute=int(hour_to_minute),second=0)
            if ot_time_difference_limit:
                date_to_add = date_to_add + timedelta(minutes=ot_time_difference_limit)
            date_to_compare = self.get_date(str(date_to_add.strftime("%Y-%m-%d %H:%M:%S")))
            
            
            
            if is_weekday:
                attendance_ids = self.env['hr.attendance'].search([('employee_id', '=', each.id),
                                                                    ('check_out', '>=', str(date_to_compare)),
                                                                    ('check_out', '<=', str(self.get_date(str(date.today()) + " 23:59:59"))),
                                                                    ('employee_ot_id', '=', False)])
                
                
            else:
                attendance_ids = self.env['hr.attendance'].search([('employee_id', '=', each.id),
                                                                    ('check_out', '>=', str(self.get_date(str(date.today()) + " 00:00:00"))),
                                                                    ('check_out', '<=', str(self.get_date(str(date.today()) + " 23:59:59"))),
                                                                    ('employee_ot_id', '=', False)])
            
            overtime = 0.0
            for each_attendance_id in attendance_ids:
                if is_weekday:
                    date1 = date_to_compare if date_to_compare > fields.Datetime.from_string(each_attendance_id.check_in)\
                            else fields.Datetime.from_string(each_attendance_id.check_in)
                else:
                    date1 = fields.Datetime.from_string(each_attendance_id.check_in)
                
                date2 = fields.Datetime.from_string(each_attendance_id.check_out)
                duration = (date2 - date1).total_seconds()
                overtime += divmod(duration, 60)[0]
            if overtime and ot_rate:
                employee_ot_id = self.env['hr.employee.overtime'].create({'employee_id': each.id,
                                                         'date': date.today(),
                                                         'based_on': 'weekday' if is_weekday else 'weekend',
                                                         'ot_rate': ot_rate,
                                                         'overtime': overtime
                                                         })

                attendance_ids.update({'employee_ot_id': employee_ot_id.id})

    @api.multi
    def emp_overtime_approve(self):
        self.ensure_one()
        self.state = 'approved'

    @api.multi
    def emp_overtime_cancel(self):
        self.ensure_one()
        attendance_ids = self.env['hr.attendance'].search([('employee_ot_id', '=', self.id)])
        if attendance_ids:
            attendance_ids.update({'employee_ot_id': False})
        self.state = 'cancelled'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: