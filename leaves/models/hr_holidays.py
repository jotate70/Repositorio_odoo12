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
import datetime
import math
from odoo import tools
from datetime import timedelta as td
from odoo.exceptions import Warning, ValidationError


class hr_holidays(models.Model):
    _inherit = "hr.leave"

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")

    def _get_number_of_days(self, date_from, date_to, employee_id):
        data_list = []
        day_list = []
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)
        timedelta = to_dt - from_dt
        emp_rec = self.env['hr.employee'].browse(employee_id)
        aspl_leave_obj = self.env['leave.setting'].sudo().search([], order='id desc', limit=1)
        if emp_rec.week_off_ids:
            week_list = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for each_week_off in emp_rec.week_off_ids:
                if each_week_off.active and each_week_off.start_date <= date_from \
                        and each_week_off.end_date >= date_to:
                    for index, each_day in enumerate(week_list):
                        if getattr(each_week_off, each_day):
                            day_list.append(index)
                for i in range(timedelta.days + 1):
                    date = from_dt + td(days=i)
                    working_day = self.is_working(date)
                    if (aspl_leave_obj.leave_rule == 'enable_sandwich') \
                            and (aspl_leave_obj.want_to_include_weekoff == True) \
                            and (emp_rec.disable_sandwich_rule == False):
                        data_list.append(date)
                    if (aspl_leave_obj.leave_rule == 'skip_sat_sun') \
                            and (date.weekday() == 6 or date.weekday() == 5):
                        day_list.append(date.weekday())
                    if (working_day == True) and (date not in data_list):
                        data_list.append(date)
                    elif working_day == False:
                        continue;
                    elif working_day == True and aspl_leave_obj.leave_rule == 'enable_sandwich' and emp_rec.disable_sandwich_rule == True:
                        continue;
                    elif working_day == False and not aspl_leave_obj.leave_rule == 'enable_sandwich':
                        continue;
                    elif working_day == False and aspl_leave_obj.leave_rule == 'enable_sandwich' \
                            and emp_rec.disable_sandwich_rule == False:
                        data_list.append(date)
                    elif (date.weekday() not in day_list) and (date not in data_list):
                        data_list.append(date)
                diff_day = len(data_list) + float(timedelta.seconds) / 86400
                return diff_day
        elif not emp_rec.week_off_ids:
            day_list = []
            data_list = []
            for i in range(timedelta.days + 1):
                date = from_dt + td(days=i)
                working_day = self.is_working(date)
                if aspl_leave_obj.leave_rule == 'enable_sandwich' \
                        and (aspl_leave_obj.want_to_include_weekoff == True) \
                        and (emp_rec.disable_sandwich_rule == False):
                    data_list.append(date)
                if (aspl_leave_obj.leave_rule == 'skip_sat_sun') \
                        and (date.weekday() == 6 or date.weekday() == 5) and date.weekday() not in day_list:
                    day_list.append(6)
                    day_list.append(5)
                if (working_day == True) and (date not in data_list):
                    data_list.append(date)
                elif working_day == False:
                    continue;
                elif working_day == False:
                    continue;
                if (date.weekday() not in day_list) and date not in data_list:
                    data_list.append(date)
            diff_day = len(data_list) + float(timedelta.seconds) / 86400
            return diff_day
        else:
            diff_day = (timedelta.days + float(timedelta.seconds) / 86400) + 1
            return diff_day

    def is_working(self, date):
        phl_obj = self.env['hr.public.holiday.line']
        only_date = datetime.date.strftime(date, "%Y-%m-%d")
        public_holiday_ids = phl_obj.search([('holiday_date', '>=', only_date + " 00:00:00"),
                                             ('holiday_date', '<=', only_date + " 23:59:59"),
                                             ('type', '=', 'working')])
        phl_holiday_ids = phl_obj.search([('holiday_date', '>=', only_date + " 00:00:00"),
                                          ('holiday_date', '<=', only_date + " 23:59:59"),
                                          ('type', '=', 'holiday')])
        if public_holiday_ids:
            return True
        elif phl_holiday_ids:
            return False

    @api.onchange('date_from')
    def _onchange_date_from(self):
        date_from = self.date_from
        date_to = self.date_to
        employee_id = self.employee_id.id
        result = {'value': {'number_of_days_temp': 0}}
        if date_from and not date_to:
            date_to_with_delta = date_from
            result['value']['date_to'] = str(date_to_with_delta)
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to, employee_id)
            result['value']['number_of_days_temp'] = round(math.floor(diff_day))
        return result

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self.env['hr.leave.allocation']:
                domain = [
                    ('date_from', '<=', holiday.date_to),
                    ('date_to', '>=', holiday.date_from),
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('type', '=', holiday.type),
                    ('state', 'not in', ['cancel', 'refuse']),
                ]
                nholidays = self.search_count(domain)
                if nholidays:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))

    @api.multi
    def action_approve(self):
        res = super(hr_holidays, self).action_approve()
        holidays = self.env['hr.leave.allocation'].search([
                                                       ('date_from', '<=', self.date_from),
                                                       ('date_to', '>=', self.date_to),
                                                       ('state', '=', 'validate')])
        if not holidays:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please verify also the leaves waiting for validation.'))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
