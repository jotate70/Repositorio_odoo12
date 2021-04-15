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
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    entry_document_ids = fields.Many2many('employee.document', 'entry_doc_config_rel',
                                           string="Entry Document(s)")
    product_ids = fields.Many2many('product.product', 'config_product_rel',
                                   'config_product_id', 'config_id', string="Product(s)")
    exit_document_ids = fields.Many2many('employee.document', 'exit_doc_config_rel', string="Exit Document(s)")
    notice_period = fields.Integer(string="Notice Period", default=60)

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().get_param
        entry_document_ids = config_param_obj('flexi_hr_ee.entry_document_ids')
        entry_document_ids = ast.literal_eval(entry_document_ids) if entry_document_ids else entry_document_ids
        exit_document_ids = config_param_obj('flexi_hr_ee.exit_document_ids')
        exit_document_ids = ast.literal_eval(exit_document_ids) if exit_document_ids else exit_document_ids
        product_ids = config_param_obj('flexi_hr_ee.product_ids')
        product_ids = ast.literal_eval(product_ids) if product_ids else product_ids
        notice_period = int(config_param_obj('flexi_hr_ee.notice_period'))
        res.update({'entry_document_ids':entry_document_ids,
                    'exit_document_ids':exit_document_ids,
                    'product_ids':product_ids,
                    'notice_period':notice_period
                    })
        return res

    @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        config_param_obj = self.env['ir.config_parameter'].sudo().set_param
        config_param_obj("flexi_hr_ee.entry_document_ids", self.entry_document_ids.ids)
        config_param_obj("flexi_hr_ee.exit_document_ids", self.exit_document_ids.ids)
        config_param_obj("flexi_hr_ee.product_ids", self.product_ids.ids)
        config_param_obj("flexi_hr_ee.notice_period", self.notice_period)
        return res

    @api.one
    @api.constrains('notice_period')
    def _check_notice_period(self):
        if self.notice_period < 0:
            raise ValidationError(_('Please enter valid Notice Period.'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: