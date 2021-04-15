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


class employee_event_attendance(models.TransientModel):
    _name = 'employee.event.attendance'

    event_id = fields.Many2one('employee.event', 'Event', required=True, ondelete="cascade")
    department_ids = fields.Many2many('hr.department', 'employee_event_attendance_department_rel', string="Department")
    job_ids = fields.Many2many('hr.job', 'employee_event_attendance_job_rel', string="Job")
    employee_ids = fields.Many2many('hr.employee', 'employee_event_attendance_employee_rel', string="Employee")

    @api.onchange('department_ids')
    def onchange_department_ids(self):
        if self.department_ids:
            job_ids = self.env['hr.job'].search([('department_id', 'in', [x.id for x in self.department_ids])])
            return {'domain': {'job_ids': [('id', 'in', [x.id for x in job_ids])]}}
        else:
            return {'domain': {'job_ids':[], 'department_ids':[]}}

    @api.multi
    def confirm_attendance(self):
        hr_employee_obj = self.env['hr.employee']
        emp_event_participant_obj = self.env['employee.event.participant']
        final_employee_ids = False

        if not self.job_ids and not self.employee_ids and not self.department_ids:
            raise Warning(_('Please select at least one.'))
        if self.employee_ids:
            final_employee_ids = self.employee_ids
        elif self.job_ids:
            final_employee_ids = hr_employee_obj.search([('job_id', 'in', [x.id for x in self.job_ids])])
        elif self.department_ids:
            final_employee_ids = hr_employee_obj.search([('department_id', 'in', [x.id for x in self.department_ids])])

        if not final_employee_ids:
            raise  Warning(_('No Employee Found.'))
        participant_id = emp_event_participant_obj.search([('employee_id', 'in', [x.id for x in final_employee_ids]), ('state', '=', 'subscribe')], limit=1)

        if participant_id:
            raise  Warning(_('Employee already participated in another event.'))
        if self.event_id.seats_min <= 0:
            raise  Warning(_('Please enter Minimum Attendees for event.'))
        if self.event_id.seats_availability == 'limited':
            participant_count = emp_event_participant_obj.search_count([('state', '=', 'subscribe'), ('employee_event_id', '=', self.event_id.id)])
            if (len(final_employee_ids) + participant_count) > self.event_id.seats_max:
                raise  Warning(_("You Can't allow more than %s employee for %s.") % (self.event_id.seats_max, self.event_id.name))

        template_id = self.env.ref('flexi_hr_ee.emp_event_confirm_email')
        email_lst = ''
        for each_employee in final_employee_ids:
            already_part_emp = emp_event_participant_obj.search([('employee_id', '=', each_employee.id),
                                                  ('employee_event_id', '=', self.event_id.id),
                                                  ('state', '=', 'unsubscribe')], limit=1)
            if not already_part_emp:
                if self.event_id.auto_subscribe and each_employee.work_email:
                    email_lst += each_employee.work_email + ','
                self.event_id.write({'event_participant_ids':[(0, 0, {
                                   'employee_id':each_employee.id,
                                   'state': 'subscribe' if self.event_id.auto_subscribe else 'unsubscribe',
                                    })]})
                each_employee.write({'event_ids':[(4, self.event_id.id)]})
        if email_lst:
            template_id.with_context({'emp_email':email_lst}).send_mail(self.id, force_send=True, raise_exception=False)


class wizard_cancel_event(models.TransientModel):
    _name = 'wizard.cancel.event'

    name = fields.Text(string="Reason")
    end_date = fields.Datetime(string="End Date")

    @api.one
    def cancel_event(self):
        if self._context.get('active_model') and self._context.get('active_id'):
            event_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            if event_id:
                email_lst = ''
                if self._context.get('from_cancel_event'):
                    template_id = self.env.ref('flexi_hr_ee.cancel_event_mail')
                    event_id.state = 'cancel'
                    event_id.cancel_note = self.name
                    for each_participant in event_id.event_participant_ids:
                        if each_participant.state == 'subscribe':
                            each_participant.state = 'unsubscribe'
                        if each_participant.employee_id.work_email:
                            email_lst += each_participant.employee_id.work_email + ','
                    if email_lst:
                        template_id.with_context({'emp_email':email_lst, 'event_name':event_id.name}).send_mail(self.id, force_send=True, raise_exception=False)

                if self._context.get('from_extend_event'):
                    if (self.end_date < event_id.start_date):
                        raise Warning(_('end date should be greater than start date.'))
                    if self.end_date < event_id.end_date:
                        raise Warning(_('end date should be greater than current event end date.'))
                    template_id = self.env.ref('flexi_hr_ee.extend_event_mail')
                    event_id.extend_note = self.name
                    event_id.end_date = self.end_date
                    for each_participant in event_id.event_participant_ids:
                        if each_participant.employee_id.work_email:
                            email_lst += each_participant.employee_id.work_email + ','
                    if email_lst:
                        template_id.with_context({'emp_email':email_lst, 'event_name':event_id.name}).send_mail(self.id, force_send=True, raise_exception=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: