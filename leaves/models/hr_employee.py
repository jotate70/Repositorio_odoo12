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


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    disable_sandwich_rule = fields.Boolean("Disable Sandwich Rule")
    leave_enable = fields.Boolean("Leave Enable")
    week_off_ids = fields.Many2many('weekly.off.group', 'employee_week_off', 'employee_id',
                                    'week_off_id', 'Week Off')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: