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


class hr_employee(models.Model):
    _inherit = "hr.employee"

    weekday_ot_rate = fields.Float(string="Weekday OT Rate")
    weekend_ot_rate = fields.Float(string="Weekend OT Rate")
    overtime_count = fields.Integer(stirng="Overtime Count", compute='get_overtime_count')

    @api.multi
    def get_overtime_count(self):
        for each in self:
            each.overtime_count = self.env['hr.employee.overtime'].search_count([('employee_id', '=', each.id)])

    @api.multi
    def related_overtime_view(self):
        return {
                'type': 'ir.actions.act_window',
                'name': _('Employee Overtime'),
                'res_model': 'hr.employee.overtime',
                'view_type': 'form',
                'view_mode': 'tree',
                'target': 'current',
                'domain': [('employee_id', '=', self.id)]
                }


class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    employee_ot_id = fields.Many2one('hr.employee.overtime', string="Related Overtime", readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: