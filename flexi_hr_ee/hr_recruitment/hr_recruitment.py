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
from datetime import date
from odoo.exceptions import ValidationError, UserError

class hr_recruitment(models.Model):
    _inherit = 'hr.applicant'
    
    type_ids = fields.Many2many('hr.recruitment.degree', 'degree_applicant_rel','deg_id', 'app_id', string="Degree")
    emp_entry_id = fields.Many2one('employee.entry', string="Employee Entry")
    emp_id = fields.Many2one('hr.employee', string="Employee")
    contract_id = fields.Many2one('hr.contract', string="Contract")
    assured_salary =fields.Float(string='Assured Salary')

    @api.constrains('assured_salary')
    def _check_assured_salary(self):
        if self.assured_salary < 0.0:
            raise ValidationError(_('Please enter valid Assured Salary.'))

    @api.multi
    def action_get_created_employee_entry(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('flexi_hr_ee', 'action_aspl_emp_entry_for_recruitment')
        action['res_id'] = self.mapped('emp_entry_id').ids[0]
        return action

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        if self._context.get('checkin'):
            if not self.job_id:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))
            else:
                view_id = self.env.ref('flexi_hr_ee.create_employee_wiz_form_view').id
                return {
                        'type': 'ir.actions.act_window',
                        'name': _('Create Employee Entry / Contract'),
                        'res_model': 'create.employee',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': view_id,
                        'target': 'new',
                        'context': {'default_contract_id': self.contract_id.id,
                                    'default_wage': self.assured_salary if self.assured_salary >= 0 else 0,
                                    'default_contract_date_start': self.availability if self.availability else date.today()}
                        }
        else:
            return super(hr_recruitment, self).create_employee_from_applicant()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: