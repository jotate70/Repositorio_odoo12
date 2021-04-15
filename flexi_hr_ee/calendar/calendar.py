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
from datetime import datetime, timedelta 
import pytz


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    event_ids = fields.Many2many('hr.employee.meeting', 'calendar_event_hr_employee_rel', 'event_id', 'emp_id')

    @api.multi
    def employee_meetings(self):
        meeting_ids = self.env['hr.employee.meeting'].search([('employee_ids', 'in', self.id)])
        view_id = self.env.ref('flexi_hr_ee.employee_meeting_tree_view')
        return {
                'type': 'ir.actions.act_window',
                'name': _('Event'),
                'res_model': 'hr.employee.meeting',
                'view_type': 'form',
                'view_mode': 'tree',
                'view_id':view_id.id,
                'domain':[('id', 'in', [x.id for x in meeting_ids])],
            }


class hr_employee_meeting(models.Model):
    _name = 'hr.employee.meeting'

    def _compute_is_highlighted(self):
        if self.env.context.get('active_model') == 'res.partner':
            partner_id = self.env.context.get('active_id')
            for event in self:
                if event.partner_ids.filtered(lambda s: s.id == partner_id):
                    event.is_highlighted = True

    name = fields.Char(string='Meeting Subject', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    employee_ids = fields.Many2many('hr.employee', 'custom_calender_meeting_rel')
    categ_ids = fields.Many2many('calendar.event.type', 'calendar_custom_event_type_rel', 'catg_id', 'event_id', string="Tags")
    location = fields.Char(string="Location")
    description = fields.Text('Description')
    display_time = fields.Char('Event Time', compute='_compute_display_time')
    display_start = fields.Char('Date', compute='_compute_display_start', store=True)
    start = fields.Datetime('Start', help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop', help="Stop date of an event, without time for full days events")
    allday = fields.Boolean('All Day', default=False)
    start_date = fields.Date('Start Date', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    start_datetime = fields.Datetime('Start DateTime', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    stop_date = fields.Date('End Date', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    stop_datetime = fields.Datetime('End Datetime', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')  # old date_deadline
    duration = fields.Float('Duration')
    is_highlighted = fields.Boolean(compute='_compute_is_highlighted', string='# Meetings Highlight')

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
                return round(duration, 2)
            return 0.0

    @api.multi
    def _compute_display_time(self):
        for meeting in self:
            meeting.display_time = self._get_display_time(meeting.start, meeting.stop, meeting.duration, meeting.allday)

    @api.multi
    @api.depends('allday', 'start_date', 'start_datetime')
    def _compute_display_start(self):
        for meeting in self:
            meeting.display_start = meeting.start_date if meeting.allday else meeting.start_datetime

    @api.multi
    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        """ Adapt the value of start_date(time)/stop_date(time) according to start/stop fields and allday. Also, compute
            the duration for not allday meeting ; otherwise the duration is set to zero, since the meeting last all the day.
        """
        for meeting in self:
            if meeting.allday:
                meeting.start_date = meeting.start
                meeting.start_datetime = False
                meeting.stop_date = meeting.stop
                meeting.stop_datetime = False
                meeting.duration = 0.0
            else:
                meeting.start_date = False
                meeting.start_datetime = meeting.start
                meeting.stop_date = False
                meeting.stop_datetime = meeting.stop
                meeting.duration = self._get_duration(meeting.start, meeting.stop)

    @api.multi
    def _inverse_dates(self):
        for meeting in self:
            if meeting.allday:
                tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc

                enddate = fields.Datetime.from_string(meeting.stop_date)
                enddate = tz.localize(enddate)
                enddate = enddate.replace(hour=18)
                enddate = enddate.astimezone(pytz.utc)
                meeting.stop = fields.Datetime.to_string(enddate)

                startdate = fields.Datetime.from_string(meeting.start_date)
                startdate = tz.localize(startdate)  # Add "+hh:mm" timezone
                startdate = startdate.replace(hour=8)  # Set 8 AM in localtime
                startdate = startdate.astimezone(pytz.utc)  # Convert to UTC
                meeting.start = fields.Datetime.to_string(startdate)
            else:
                meeting.start = meeting.start_datetime
                meeting.stop = meeting.stop_datetime

    @api.onchange('start_datetime', 'duration')
    def _onchange_duration(self):
        if self.start_datetime:
            start = fields.Datetime.from_string(self.start_datetime)
            self.start = self.start_datetime
            self.stop = fields.Datetime.to_string(start + timedelta(hours=self.duration))


class calendar_contacts_custom(models.Model):
    _name = 'calendar.contacts.custom'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', 'Attendees')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('user_id_employee_id_unique', 'UNIQUE(user_id,employee_id)', 'An user cannot have twice the same contact.')
    ]

    @api.model
    def unlink_from_employee_id(self, employee_id):
        return self.search([('employee_id', '=', employee_id)]).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
