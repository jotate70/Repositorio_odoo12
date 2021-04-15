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

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    double_validation = fields.Boolean(string="Double Validation", implied_group='performance_evaluation_rating.kra_second_approve')
    self_review = fields.Boolean(string="Self Review", implied_group='performance_evaluation_rating.kra_approve_group')
    include_internal_msg = fields.Boolean(string="Include Internal Message")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter']
        res.update({
            'double_validation': param_obj.sudo().get_param('performance_evaluation_rating.double_validation'),
            'self_review': param_obj.sudo().get_param('performance_evaluation_rating.self_review'),
            'include_internal_msg': param_obj.sudo().get_param('performance_evaluation_rating.include_internal_msg'),
            })
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter']
        param_obj.sudo().set_param('performance_evaluation_rating.double_validation', self.double_validation)
        param_obj.sudo().set_param('performance_evaluation_rating.self_review', self.self_review)
        param_obj.sudo().set_param('performance_evaluation_rating.include_internal_msg', self.include_internal_msg)
        evaluation_records = self.env['kra.evaluation'].search([('state', 'not in', ['done'])])
        if evaluation_records:
            for rec in evaluation_records:
                rec.sudo().write({
                    'double_validation': self.double_validation,
                    'self_review': self.self_review,
                    'internal_msg': self.include_internal_msg
                })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
