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


class wizard_loan(models.TransientModel):
    _name = 'wizard.loan'
    _description = 'Wizard Loan'

    @api.multi
    def get_data(self):
        if self.env.context.get('active_model') and self.env.context.get('active_id'):
            loan_app_record_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
            if loan_app_record_id:
                if self.env.context.get('from_reject'):
                    loan_app_record_id.write({'reject_reason': self.reason})
                    payment_ids = self.env['loan.payment'].search([('loan_app_id' , '=', loan_app_record_id.id)])
                    payment_ids.unlink()
                    loan_app_record_id.state = 'rejected'
                    loan_app_record_id.rejected_mail_template()
                elif self.env.context.get('from_cancel'):
                    loan_app_record_id.write({'loan_cancel_reason': self.reason, 'state': 'cancel'})
                    loan_app_record_id.cancelled_mail_template()

    reason = fields.Text('Note', required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: