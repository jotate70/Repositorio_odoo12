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
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    weekday_ot_rate = fields.Float(string="Weekday OT Rate")
    weekend_ot_rate = fields.Float(string="Weekend OT Rate")
    ot_time_difference_limit = fields.Integer(string="OT Time Difference Limit")

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().get_param
        weekday_ot_rate = float(config_param_obj('aspl_hr_overtime.weekday_ot_rate'))
        weekend_ot_rate = float(config_param_obj('aspl_hr_overtime.weekend_ot_rate'))
        ot_time_difference_limit = int(config_param_obj('aspl_hr_overtime.ot_time_difference_limit'))
        res.update({'weekday_ot_rate':weekday_ot_rate,
                    'weekend_ot_rate':weekend_ot_rate,
                    'ot_time_difference_limit':ot_time_difference_limit,
                    })
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().set_param
        config_param_obj("aspl_hr_overtime.weekday_ot_rate", self.weekday_ot_rate)
        config_param_obj("aspl_hr_overtime.weekend_ot_rate", self.weekend_ot_rate)
        config_param_obj("aspl_hr_overtime.ot_time_difference_limit", self.ot_time_difference_limit)
        return res

    @api.one
    @api.constrains('weekday_ot_rate', 'weekend_ot_rate', 'ot_time_difference_limit')
    def _check_notice_period(self):
        if self.weekday_ot_rate < 0 or self.weekend_ot_rate < 0 or self.ot_time_difference_limit < 0:
            raise ValidationError(_('Please enter valid value.'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: