# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning

class kratemplate(models.Model):
    _name = 'kra.template'
    _description = 'KRA Template'

    name = fields.Char(string="Name", required=True)
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    active = fields.Boolean(string='Active', default=True)
    is_active = fields.Boolean(string="Is Active")
    questions_ids = fields.One2many('kra.question','kr_tmpl_id', string="KRA Questions")

    @api.multi
    @api.constrains('is_active')
    def _check_is_active(self):
        if self.is_active == True:
            kra_template = self.env['kra.template'].search([('department_id','=',self.department_id.id),
                                                            ('job_id','=',self.job_id.id),
                                                            ('is_active','=',True),('id','!=',self.id)])
            if kra_template:
                raise Warning(_('You already have active template for job position "%s" for "%s" department' %(self.job_id.name, self.department_id.name)))


class kraquestion(models.Model):
    _name = 'kra.question'
    _description = 'KRA Template Questions'

    kr_tmpl_id = fields.Many2one('kra.template', string="KRA Questions")
    questions = fields.Char(string="Questions", required=True)
