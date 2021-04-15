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


class penalty_config_setting(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_late_mins = fields.Integer(string="Allow Late Minute")
    penalty_amount = fields.Float(string="Penalty Amount")
    apply_penalty_after = fields.Integer(string="Apply Penalty After")
    apply_panelty_on_leave = fields.Integer(string="Apply Penalty On Leave After")
    rule_to_count_leave = fields.Boolean(string="To Count The Unpaid Leave")

    def get_values(self):
       res = super(penalty_config_setting, self).get_values()
       res.update({'allow_late_mins': 
                    int(self.env['ir.config_parameter'].sudo().get_param('allow_late_mins')) or False,
                  'penalty_amount': 
                  float(self.env['ir.config_parameter'].sudo().get_param('penalty_amount')) or False,
                  'apply_penalty_after': 
                  int(self.env['ir.config_parameter'].sudo().get_param('apply_penalty_after')) or False,
                  'rule_to_count_leave': 
                  (self.env['ir.config_parameter'].sudo().get_param('rule_to_count_leave')),
                   'apply_panelty_on_leave':
                       int(self.env['ir.config_parameter'].sudo().get_param('apply_panelty_on_leave')) or False,
                  })
       return res

    def set_values(self):
       res = super(penalty_config_setting, self).set_values()
       self.env['ir.config_parameter'].sudo().set_param('allow_late_mins',
                                                            self.allow_late_mins or '')
       self.env['ir.config_parameter'].sudo().set_param('penalty_amount',
                                                            self.penalty_amount or '')
       self.env['ir.config_parameter'].sudo().set_param('apply_penalty_after',
                                                            self.apply_penalty_after or '')
       self.env['ir.config_parameter'].sudo().set_param('rule_to_count_leave',
                                                             self.rule_to_count_leave or False)
       self.env['ir.config_parameter'].sudo().set_param('apply_panelty_on_leave',
                                                        self.apply_panelty_on_leave or False)
       return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4