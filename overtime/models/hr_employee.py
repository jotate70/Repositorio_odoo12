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

    ot_rate_per_hour = fields.Float(string="Overtime Per Hour Rate")


class hr_job(models.Model):
    _inherit = "hr.job"

    ot_rate_per_hour = fields.Float(string="Overtime Per Hour Rate")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
