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

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().get_param
        interest_rate = float(config_param_obj('flexi_hr_ee.interest_rate'))
        max_term = int(config_param_obj('flexi_hr_ee.max_term'))
        res.update({'interest_rate':interest_rate,'max_term':max_term})
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().set_param
        config_param_obj("flexi_hr_ee.interest_rate", self.interest_rate)
        config_param_obj("flexi_hr_ee.max_term", self.max_term)
        return res

    interest_rate = fields.Float(string="Interest Rate", default=0.0)
    max_term = fields.Integer(string="Max. Term", default=1)

    @api.one
    @api.constrains('max_term')
    def _check_max_term(self):
        if self.max_term < 0:
            raise ValidationError(_('Please enter valid number of term.'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: