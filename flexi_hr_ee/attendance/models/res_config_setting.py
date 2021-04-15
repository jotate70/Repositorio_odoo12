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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def default_get(self, fieldsname):
        res = super(ResConfigSettings, self).default_get(fieldsname)
        record_id = self.search(([]), order='id desc', limit=1)
        if record_id:
            res.update({
                        'allow_diff_attendance_timesheet': record_id.allow_diff_attendance_timesheet
                        })
        return res

    allow_diff_attendance_timesheet = fields.Float(string='Allow Difference In Attendance and Timesheet')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: