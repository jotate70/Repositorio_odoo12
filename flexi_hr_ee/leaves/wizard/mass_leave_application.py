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
from datetime import datetime
from odoo.exceptions import UserError, Warning


class mass_leave_application(models.TransientModel):
    _name = 'mass.leave.application'

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    job_position_ids = fields.Many2many('hr.job', string="Job Position")
    exclude_employee_ids = fields.Many2many('hr.employee', 'exclude_mass_leave_employee_rel', string="Exclude Employee")
    employee_ids = fields.Many2many('hr.employee', 'mass_leave_employee_rel', string="Employee")
    mass_leave_line_ids = fields.One2many('mass.leave.application.line', 'mass_leav_id', string="Mass Leave Lines")

    @api.onchange('job_position_ids')
    def onchange_job_position_ids(self):
        hr_employee_obj = self.env['hr.employee']
        if self.job_position_ids:
            final_employee_ids = hr_employee_obj.search([('job_id', 'in', [x.id for x in self.job_position_ids])])
            final_employee_ids -= self.exclude_employee_ids
            return {'domain': {'employee_ids': [('id', 'in', [x.id for x in final_employee_ids])],
                               'exclude_employee_ids': [('id', 'in', [x.id for x in final_employee_ids])], } }
        else:
            return {'domain': {'employee_ids': [], 'exclude_employee_ids':[]}}

    @api.multi
    def create_mass_leave(self):
        leave_allocation_lst = []
        hr_leave_allocation_obj = self.env['hr.leave.allocation']
        hr_employee_obj = self.env['hr.employee']
        final_employee_ids = False
        if self.end_date < self.start_date:
            raise Warning(_("The start date must be anterior to the end date."))
        hr_holiday_status_obj = self.env['hr.leave.type']
        if not self.job_position_ids and not self.employee_ids:
            final_employee_ids = hr_employee_obj.search([])
        if self.employee_ids:
            final_employee_ids = self.employee_ids - self.exclude_employee_ids
        elif self.job_position_ids:
            final_employee_ids = hr_employee_obj.search([('job_id', 'in', [x.id for x in self.job_position_ids])])
            final_employee_ids = final_employee_ids - self.exclude_employee_ids
        start_date = self.start_date
        end_date = self.end_date
        days = (end_date - start_date).days
        extra_leave_count = self.mass_leave_line_ids.filtered(lambda line:line.leave > days)
        if extra_leave_count:
            raise UserError(_('You are exceeding the duration limit.Please assign proper leave.'))
        if final_employee_ids:
            for each_line in self.mass_leave_line_ids:
                if each_line.leave <= 0.00:
                    raise Warning(_('Please enter valid number for leave.'))
                hr_holiday_status_obj = hr_holiday_status_obj.search([('name', '=', each_line.leave_type)], limit=1)
                if not hr_holiday_status_obj:
                    hr_holiday_status_obj = hr_holiday_status_obj.create({'name':each_line.leave_type,
                                                  'double_validation':each_line.double_validation,
                                                  'limit':each_line.limit})
                for each_employee in final_employee_ids:
                    hr_leave_allocation_obj = hr_leave_allocation_obj.create({'name':each_line.leave_type,
                                            'holiday_status_id':hr_holiday_status_obj.id,
                                            'employee_id':each_employee.id,
                                            'number_of_days': each_line.leave,
                                            'date_from':self.start_date,
                                            'date_to':self.end_date,
                                            'state':each_line.status
                                            })
                    leave_allocation_lst.append(hr_leave_allocation_obj.id)
            action = self.env.ref('hr_holidays.hr_leave_allocation_action_approve_department').read()[0]
            action['domain'] = [('id', 'in', leave_allocation_lst)]
#             action['context']= {'default_type':'add'}
            return action
        else:
            raise Warning(_('There must be at least one employee to proceed..!'))


class hr_leave_allocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    @api.model
    def create(self, vals):
        return super(hr_leave_allocation, self).create(vals)


class mass_leave_application_line(models.TransientModel):
    _name = 'mass.leave.application.line'

    mass_leav_id = fields.Many2one('mass.leave.application', string="Mass Leave")
    leave_type = fields.Selection([('Paid', 'Paid'), ('Unpaid', 'Unpaid'),
                                   ('Sick Leave', 'Sick Leave'), ('Compensatory', 'Compensatory')], string="Leave Type")
    leave = fields.Integer(string="Leave")
    double_validation = fields.Boolean(string="Double Validation")
    limit = fields.Boolean(string="Allow to Override Limit")
    status = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'), ('confirm', 'To Approve'),
                               ('refuse', 'Refused'), ('validate1', 'Second Approval'), ('validate', 'Approved')],
                               default='draft', string="Status")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: