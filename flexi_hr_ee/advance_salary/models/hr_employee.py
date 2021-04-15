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

    advance_salary_limit = fields.Float(string="Advance Salary Limit")
    req_count = fields.Integer(string="Advance Salary Request Limit")

    @api.multi
    def salary_request(self):
        return {
                'type': 'ir.actions.act_window',
                'name': _('Advance Salary Request'),
                'res_model': 'hr.advance.salary.request',
                'view_type': 'form',
                'view_mode': 'form',
                'domain': [('employee_id','=', self.id)],
                'context': {'default_employee_id': self.id}
                }


class hr_job(models.Model):
    _inherit = "hr.job"

    advance_salary_limit = fields.Float(string="Advance Salary Limit")
    req_count = fields.Integer(string="Advance Salary Request Limit")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: