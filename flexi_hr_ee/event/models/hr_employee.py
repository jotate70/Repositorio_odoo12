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
from odoo.exceptions import Warning


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('department_ids') and self._context.get('department_ids')[0][2]:
            employee_ids = self.search([('department_id', 'in', self._context.get('department_ids')[0][2])])
            employee_ids = self.search_holiday_emp_record(employee_ids, self._context.get('event_id'))
            if employee_ids:
                args += [('id', 'in', [x.id for x in employee_ids])]
        elif self._context.get('job_ids') and self._context.get('job_ids')[0][2]:
            employee_ids = self.search([('job_id', 'in', self._context.get('job_ids')[0][2])])
            employee_ids = self.search_holiday_emp_record(employee_ids, self._context.get('event_id'))
            if employee_ids:
                args += [('id', 'in', [x.id for x in employee_ids])]
        elif self._context.get('event_id'):
            employee_ids = self.search([])
            employee_ids = self.search_holiday_emp_record(employee_ids, self._context.get('event_id'))
            if employee_ids:
                args += [('id', 'in', [x.id for x in employee_ids])]
        return super(hr_employee, self).name_search(name, args, operator, limit)

    def search_holiday_emp_record(self, employee_ids, event_id):
        if employee_ids and event_id:
            event_id = self.env['employee.event'].browse(event_id)
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

            self._cr.execute(''' select employee_id from hr_leave where state='validate'
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
                employee_ids -= holiday_emp.browse(each['employee_id'])
            return employee_ids

    @api.multi
    def view_employee_event(self):
        view_id = self.env.ref('flexi_hr_ee.wizard_employee_event_form_view')
        return {
                'type': 'ir.actions.act_window',
                'name': _('Event'),
                'res_model': 'wizard.employee.event',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'view_id':view_id.id
            }

    @api.multi
    def review_on_event(self):
        view_id = self.env.ref('flexi_hr_ee.wizard_employee_event_rating_form_view')
        return {
                'type': 'ir.actions.act_window',
                'name': _('Review'),
                'res_model': 'employee.event.rating',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'view_id':view_id.id,
                'context':{'default_employee_id':self.id}
            }

    @api.multi
    def show_emp_event(self):
        view_id = self.env.ref('flexi_hr_ee.view_employee_event_tree')
        return {
                'type': 'ir.actions.act_window',
                'name': _('Event'),
                'res_model': 'employee.event.participant',
                'view_type': 'form',
                'view_mode': 'tree',
                'view_id':view_id.id,
                'domain':[('employee_id', '=', self.id)],
                'context':{'default_employee_id':self.id}
            }

    @api.depends('event_ids')
    @api.one
    def _total_event_count(self):
        self.total_event_count = len(self.event_ids)

    event_ids = fields.Many2many('employee.event', 'emp_event_rel', 'event_id', 'employee_id', string="Event")
    total_event_count = fields.Float(string="Total Event Count", compute='_total_event_count')


class hr_holidays(models.Model):
    _inherit = 'hr.leave'

    event_check = fields.Boolean(string="Event Check")

    @api.multi
    def action_confirm(self):
        self.emp_event_check()
        res = super(hr_holidays, self).action_confirm()
        return res

    @api.multi
    def action_approve(self):
        self.emp_event_check()
        res = super(hr_holidays, self).action_approve()
        return res

    @api.multi
    def emp_event_check(self):
        if not self.event_check:
            if self._context.get('tz'):
                tz = pytz.timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '-':
                start_date = self.date_from - timedelta(hours=hour_tz, minutes=min_tz)
                end_date = self.date_to - timedelta(hours=hour_tz, minutes=min_tz)
            if sign == '+':
                start_date = self.date_from - timedelta(hours=hour_tz, minutes=min_tz)
                end_date = self.date_to - timedelta(hours=hour_tz, minutes=min_tz)

            self._cr.execute(''' select start_date,end_date,name from employee_event where state ='confirm' and id in (select employee_event_id from employee_event_participant where state ='subscribe' and employee_id  = '%d' ) ''' % self.employee_id.id)
            result = self._cr.dictfetchall()
            for each in result:
                if ((self.date_from <= each['start_date'] and self.date_to >= each['start_date']) or
                    (self.date_from <= each['end_date'] and self.date_to >= each['end_date']) or
                    (self.date_from >= each['start_date'] and self.date_from <= each['end_date']) or
                    (self.date_to >= each['start_date'] and self.date_to <= each['end_date'])):
                    self.event_check = True
                    self._cr.commit()
                    raise  Warning(_('%s already participated in %s.') % (self.employee_id.name, each['name']))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: