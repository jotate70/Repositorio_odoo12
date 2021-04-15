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


class leave_setting(models.Model):
    _name = 'leave.setting'

    @api.multi
    def execute(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def default_get(self, fields):
        res = super(leave_setting, self).default_get(fields)
        obj = self.search([], order='id desc', limit=1)
        if obj:
            dc = obj.read()[0]
            del dc["write_uid"], dc["id"], dc["__last_update"], dc["create_date"]
            res.update(dc)
        return res

    leave_rule = fields.Selection([('skip_sat_sun', 'Skip Sat-Sun'),
                                   ('enable_sandwich', 'Enable Sandwich')])
    want_to_include_weekoff = fields.Boolean("Want to Include Week Off")
    
    @api.onchange('leave_rule')
    def onchange_leave_rule(self):
        for employee in self.env['hr.employee'].search([]):
            if self.leave_rule == 'enable_sandwich': 
                employee.write({'leave_enable': True})
            else:
                employee.write({'leave_enable': False,'disable_sandwich_rule': False})
    
    
             

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: