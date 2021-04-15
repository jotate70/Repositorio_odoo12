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

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import Warning
import pytz


class employee_event_track(models.Model):
    _name = 'employee.event.track'

    name = fields.Char('Title', required=True)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    speaker_name = fields.Char('Speaker Name')
    speaker_email = fields.Char('Speaker Email')
    speaker_phone = fields.Char('Speaker Phone')
    speaker_biography = fields.Html('Speaker Biography')
    description = fields.Text('Description')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    duration = fields.Float('Duration', compute="compute_event_track_hour", store=True)
    minutes = fields.Float('Minutes', compute="compute_event_track_hour", store=True)
    event_id = fields.Many2one('employee.event', 'Event', required=True, ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    event_type = fields.Selection(related='event_id.event_type', string="Event Type", strore=True)

    def check_employee_track(self):
        self._cr.execute(''' select count(*) from employee_event_track where employee_id='%d' and event_id='%d'
                    and ((start_date <= '%s' and end_date >= '%s') or
                         (start_date <= '%s' and end_date >= '%s') or
                         (start_date >= '%s' and start_date <= '%s') or
                         (end_date >= '%s' and end_date <= '%s')
                    ) ''' % (self.employee_id.id, self.event_id.id, self.start_date, self.start_date,
                             self.end_date, self.end_date,
                             self.start_date, self.end_date,
                             self.start_date, self.end_date))
        result = self._cr.dictfetchall()
        for each in result:
            if each['count'] > 1:
                raise Warning(_('Can\t create Track on same date time.'))

    @api.constrains('start_date', 'end_date', 'event_id')
    def check_date_range(self):
        if self.start_date and self.end_date:
            if (self.start_date < self.event_id.start_date) or (self.start_date > self.event_id.end_date) or (self.end_date < self.event_id.start_date) or (self.end_date > self.event_id.end_date):
                    raise Warning(_('Event Track not more time to event start and event date.'))
            if self.event_id.event_type == 'Private' and self.employee_id:
                self.check_employee_track()

    @api.one
    @api.depends('start_date', 'end_date')
    def compute_event_track_hour(self):
        start_date = end_date = False
        if self.start_date:
            start_date = self.start_date
        if self.end_date:
            end_date = self.end_date
        if start_date and end_date:
            duration = (end_date - start_date)
            days, seconds = duration.days, duration.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            self.duration = hours
            self.minutes = minutes

    @api.model
    def create(self, vals):
        res = super(employee_event_track, self).create(vals)
        res.event_id.track_count += 1
        return res

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.speaker_name = self.employee_id.name
            self.speaker_email = self.employee_id.work_email
            self.speaker_phone = self.employee_id.work_phone
        else:
            self.speaker_name = self.speaker_email = self.speaker_phone = False
            employee_ids = self.env['hr.employee'].search([])
            employee_ids = self.search_holiday_emp_record(employee_ids)
            return {'domain': {'employee_id': [('id', 'in', [x.id for x in employee_ids])]}}

    def search_holiday_emp_record(self, employee_ids):
        if employee_ids and self.event_id:
            holiday_emp = self.env['hr.employee']
            if self._context.get('tz'):
                tz = pytz.timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '-':
                start_date = self.event_id.start_date- timedelta(hours=hour_tz, minutes=min_tz)
                end_date = self.event_id.end_date - timedelta(hours=hour_tz, minutes=min_tz)
            if sign == '+':
                start_date = self.event_id.start_date - timedelta(hours=hour_tz, minutes=min_tz)
                end_date = self.event_id.end_date - timedelta(hours=hour_tz, minutes=min_tz)
            self._cr.execute('''select employee_id from hr_leave where state='validate'
                        and ((date_from <= '%s' and date_to >= '%s') or
                             (date_from <= '%s' and date_to >= '%s') or
                             (date_from >= '%s' and date_from <= '%s') or
                             (date_to >= '%s' and date_to <= '%s')
                        ) ''' % (start_date, start_date,
                                 end_date, end_date,
                                 start_date, end_date,
                                 start_date, end_date))
            result = self._cr.dictfetchall()
            for each in result:
                employee_ids -= holiday_emp.browse(each.get('employee_id'))
            return employee_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: