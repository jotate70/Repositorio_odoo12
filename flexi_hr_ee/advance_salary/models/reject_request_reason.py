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


class reject_request_reason(models.TransientModel):
    _name = 'reject.request.reason'

    name = fields.Text(string="Reason", required=True)

    @api.one
    def add_reason(self):
        res = self.env['hr.advance.salary.request'].search([('id','=',self._context.get('active_id'))])
        res.write({'reason':self.name,'state':'reject'})
        template = self.env.ref('aspl_hr_advance_salary.email_advance_salary_reject_template')
        if template:
            result=template.send_mail(res.id, force_send=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
