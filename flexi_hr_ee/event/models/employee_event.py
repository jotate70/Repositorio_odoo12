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
from odoo.exceptions import Warning
from datetime import datetime


class employee_event(models.Model):
    _name = 'employee.event'

    @api.constrains('start_date', 'end_date')
    def check_date_range(self):
        if self.start_date and self.end_date:
            if (str(self.end_date) < str(self.start_date)):
                raise Warning(_('end date should be greater than start date.'))
            if str(self.start_date) < datetime.today().date().strftime('%Y-%m-%d 00:00:00'):
                raise Warning(_('Event start date should be greater than current date.'))

    @api.multi
    def unlink(self):
        event_id = self.filtered(lambda l:l.state == 'confirm')
        if event_id:
            raise Warning(_('can\t delete event which is Confirmed.'))
        return super(employee_event, self).unlink()

    @api.one
    @api.depends('event_participant_ids')
    def count_event_participant(self):
        self.attendance_count = len(self.event_participant_ids)

    name = fields.Char(string="Name")
    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    seats_min = fields.Integer(string='Minimum Attendees')
    seats_availability = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')], 'Maximum Attendees', required=True, default='unlimited')
    seats_max = fields.Integer(string='Maximum Attendees Number')
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancelled'), ('confirm', 'Confirmed'), ('done', 'Done')],
                             string='Status', default='draft', copy=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('employee.event'))
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    employee_event_type_id = fields.Many2one('employee.event.type', string='Category')
    track_count = fields.Integer(string='Tracks')
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="State")
    zip = fields.Char(string="Zip")
    country_id = fields.Many2one('res.country', string="Country")
    event_type = fields.Selection([('Public', 'Public'), ('Private', 'Private')], string="Event Type", default="Private")
    attendance_count = fields.Integer(string='Attendance', compute='count_event_participant', store=True)
    event_participant_ids = fields.One2many('employee.event.participant', 'employee_event_id', string="Participant", copy=False)
    auto_subscribe = fields.Boolean(string="Auto Subscribe")
    cancel_note = fields.Text(string="Note", copy=False)
    extend_note = fields.Text(string="Note", copy=False)
    total_rating_count = fields.Integer(string="Total Count")

    @api.multi
    def button_event_extend(self):
        return {
            'name': _('Extend Event'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('flexi_hr_ee.wizard_cancel_event_form_view').id,
            'res_model': 'wizard.cancel.event',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'from_extend_event':True}
          }

    @api.multi
    def button_confirm(self):
        email_lst = ''
        if self.seats_min <= 0:
            raise  Warning(_('Please enter Minimum Attendees for event.'))
        self.state = 'confirm'
        template_id = self.env.ref('flexi_hr_ee.confirm_event_mail')
        for each_emp in self.env['hr.employee'].search([('work_email', '!=', False)]):
            email_lst += each_emp.work_email + ','
        if email_lst:
            template_id.with_context({'emp_email':email_lst}).send_mail(self.id, force_send=True, raise_exception=False)

    @api.multi
    def button_done(self):
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') < str(self.end_date):
            raise Warning(_("Can't complete event before event end date."))
        else:
            self.state = 'done'

    @api.model
    def make_event_done(self):
        for event in self.search([('state', '=', 'confirm')]):
            if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > str(event.end_date):
                event.state = 'done'

    @api.multi
    def button_cancel(self):
        return {
            'name': _('Cancel Event'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('flexi_hr_ee.wizard_cancel_event_form_view').id,
            'res_model': 'wizard.cancel.event',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context':{'from_cancel_event':True}
          }

    @api.multi
    def event_review(self):
        return {
                'name': _('Event Review'),
                'view_type': 'form',
                'view_mode': 'kanban',
                'view_id': self.env.ref('flexi_hr_ee.employee_rating_kanban_view').id,
                'res_model': 'employee.event.rating',
                'type': 'ir.actions.act_window',
                'domain':[('employee_event_id', '=', self.id)]
                }


class employee_event_type(models.Model):
    _name = 'employee.event.type'

    name = fields.Char(string="Name")


class employee_event_participant(models.Model):
    _name = 'employee.event.participant'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_event_id = fields.Many2one('employee.event', string="Event", ondelete="cascade")
    state = fields.Selection([('subscribe', 'Subscribe'), ('unsubscribe', 'Unsubscribe')],
                              string='Status', default='unsubscribe', copy=False)
    start_date = fields.Datetime(related='employee_event_id.start_date', string="Start Date")
    end_date = fields.Datetime(related='employee_event_id.end_date', string="End Date")

    @api.multi
    def make_subscribe(self):
        participant_id = self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'subscribe')], limit=1)
        if participant_id:
            raise  Warning(_('%s already participated in %s.') % (self.employee_id.name, self.employee_event_id.name))
        self.emp_holiday_leave_check()
        self.state = 'subscribe'
        if self.employee_id.work_email:
            template_id = self.env.ref('flexi_hr_ee.employee_event_participant_mail')
            template_id.with_context({'emp_email':self.employee_id.work_email}).send_mail(self.id, force_send=True, raise_exception=False)

    @api.multi
    def make_unsubscribe(self):
        self.state = 'unsubscribe'

    @api.multi
    def emp_holiday_leave_check(self):
        self._cr.execute(''' select date_from,date_to from hr_leave where state='validate' and  employee_id = '%s' ''' % self.employee_id.id)
        result = self._cr.dictfetchall()
        for each in result:
            if ((self.start_date <= each['date_from'] and self.end_date >= each['date_from']) or
                (self.start_date <= each['date_to'] and self.end_date >= each['date_to']) or
                (self.start_date >= each['date_from'] and self.start_date <= each['date_to']) or
                (self.end_date >= each['date_from'] and self.end_date <= each['date_to'])):
                raise  Warning(_("%s already on leave." % (self.employee_id.name)))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
