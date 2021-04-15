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


class exit_review(models.TransientModel):
   _name = 'exit.review'

   name = fields.Text(string="Review(s)", required=True)

   @api.one
   def add_review(self):
       res = self.env['employee.exit'].search([('id','=',self._context.get('active_id'))])
       res.write({'review':self.name})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: