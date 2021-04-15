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
from datetime import datetime, timedelta
import pytz


class wizard_employee_event(models.TransientModel):
    _name = 'wizard.employee.event'

    event_type = fields.Selection([('current', 'Current'), ('up_comming', 'Upcoming')], 'Event')
    employee_event_lines = fields.Many2many('wizard.employee.event.line', 'employee_event_wizard_rel', string="Wizard")

    @api.onchange('event_type')
    def onchange_event_type(self):
        lst = domain = []
        wizard_emp_line_obj = self.env['wizard.employee.event.line']
        if self.event_type == 'current':
            domain = [('state', '=', 'confirm'),
                      ('start_date', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00')),
                      ('start_date', '<=', datetime.now().strftime('%Y-%m-%d 23:59:59'))]
        if self.event_type == 'up_comming':
            domain = [('state', '=', 'confirm'), ('start_date', '>=', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))]
        if domain:
            event_ids = self.env['employee.event'].search(domain)
            for each_event in event_ids:
                wizard_emp_line_obj = wizard_emp_line_obj.create({'employee_event_id': each_event.id,
                                                                  'start_date':each_event.start_date,
                                                                  'end_date':each_event.end_date})
                lst.append(wizard_emp_line_obj.id)
        return {'value': {'employee_event_lines': lst}}


class wizard_employee_event_line(models.TransientModel):
    _name = 'wizard.employee.event.line'

    employee_event_id = fields.Many2one('employee.event', string="Event")
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    @api.one
    def join_event(self):
        emp_event_part_obj = self.env['employee.event.participant']
        template_id = self.env.ref('flexi_hr_ee.employee_join_event_mail')
        email_lst = ''
        employee_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))

        self.check_emp_holiday_record(employee_id, self.employee_event_id)
        participant_id = emp_event_part_obj.search([('employee_id', '=', employee_id.id), ('employee_event_id', '=', self.employee_event_id.id), ], limit=1)
        if participant_id:
            if participant_id.state == 'subscribe':
                raise  Warning(_('Already participated in %s.') % self.employee_event_id.name)
            else:
                raise  Warning(_('Employee already participated in %s. make sure subscribe it.') % self.employee_event_id.name)
        if self.employee_event_id.seats_min <= 0:
            raise  Warning(_('Please enter Minimum Attendees for event.'))
        if self.employee_event_id.seats_availability == 'limited':
            participant_count = emp_event_part_obj.search_count([('state', '=', 'subscribe'), ('employee_event_id', '=', self.employee_event_id.id)])
            if participant_count == self.employee_event_id.seats_max:
                raise  Warning(_("You Can't allow more than %s employee for %s.") % (self.employee_event_id.seats_max, self.employee_event_id.name))
        self.employee_event_id.write({'event_participant_ids':[(0, 0, {
                               'employee_id':employee_id.id,
                               'state': 'subscribe' if self.employee_event_id.auto_subscribe else 'unsubscribe',
                                })]})
        employee_id.event_ids += self.employee_event_id

        if not self.employee_event_id.auto_subscribe:
            group_id = self.env.ref('hr.group_hr_manager')
            for each_user in group_id.users.filtered(lambda l:l.email):
                email_lst += each_user.email + ','
            if email_lst:
                template_id.with_context({'user_email':email_lst, 'emp_name':employee_id.name}).send_mail(self.id, force_send=True, raise_exception=False)


    def check_emp_holiday_record(self, employee_id, event_id):
        if employee_id and event_id:
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
                start_date = event_id.start_date - timedelta(hours=hour_tz, minutes=min_tz)
                end_date = event_id.end_date - timedelta(hours=hour_tz, minutes=min_tz)
            if sign == '+':
                start_date = event_id.start_date - timedelta(hours=hour_tz, minutes=min_tz)
                end_date = event_id.end_date - timedelta(hours=hour_tz, minutes=min_tz)

            self._cr.execute('''select count(*) from hr_leave where employee_id = '%d' and state='validate'
                        and ((date_from <= '%s' and date_to >= '%s') or
                             (date_from <= '%s' and date_to >= '%s') or
                             (date_from >= '%s' and date_from <= '%s') or
                             (date_to >= '%s' and date_to <= '%s')
                        ) ''' % (employee_id.id, start_date, start_date,
                                 end_date, end_date,
                                 start_date, end_date,
                                 start_date, end_date))
            result = self._cr.dictfetchall()
            if result and result[0] and result[0]['count'] > 0:
                raise  Warning(_(' You can\t participant in %s because you are on leave.') % (self.employee_event_id.name))


class employee_event_rating(models.Model):
    _name = 'employee.event.rating'

    employee_event_id = fields.Many2one('employee.event', string="Event")
    rating = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], string="Rating")
    review = fields.Text(string="Review")
    rating_readonly = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
                                       related='rating', readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            return {'domain': {'employee_event_id': [('id', 'in', [x.id for x in self.employee_id.event_ids])]}}
        else:
            return {'domain': {'employee_event_id': []}}

    @api.multi
    def add_event_rating(self):
        self.employee_event_id.total_rating_count += 1

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: