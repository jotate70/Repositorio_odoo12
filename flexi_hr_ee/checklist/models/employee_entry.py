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
from dateutil.relativedelta import relativedelta
import datetime
from odoo.exceptions import ValidationError
from datetime import date


class employee_entry(models.Model):
    _name = 'employee.entry'
    _description = 'Employee Entry'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        entry_num = self.env['ir.sequence'].next_by_code('employee.entry.form.no')
        if entry_num:
            vals.update({'name': entry_num})
        res = super(employee_entry, self).create(vals)
        
        checklist_setting_id = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)

        docs = []
        product_list = []
        if checklist_setting_id:
            for each_doc in checklist_setting_id.entry_document_ids:
                doc_dict = {
                            'emp_doc_id': each_doc.id,
                            'state': 'draft'
                            }
                docs.append((0, 0, doc_dict))
            for each_product in checklist_setting_id.product_ids:
                prod_dict = {
                            'product_id': each_product.id,
                            'state_product': 'not_allocated'
                            }
                product_list.append((0, 0, prod_dict))
            res.update({
                        'emp_entry_product_ids': product_list,
                        'emp_document_ids': docs
                        })
        else:
            raise ValidationError(_('Please configure the checklist settings first.'))
        return res

    employee_id = fields.Many2one('hr.employee', string="Employee")
    job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    department_id = fields.Many2one('hr.department', string="Department")
    join_date = fields.Date(string="Join Date",default=date.today(), required=True)
    name = fields.Char('Reg. Number')
    emp_document_ids = fields.One2many('emp.doc.line','entry_id', string="Documents")
    emp_entry_product_ids = fields.One2many('emp.product.line', 'product_entry_id', string="Product(s)")
    state = fields.Selection([('draft', 'Draft'),
                              ('entry_done', 'Entry Done'),
                              ('exited', 'Exited')], default='draft', string="State")
    recruitment_id = fields.Many2one('hr.applicant', 'Application')
    emp_exit_init = fields.Boolean('Applied For Exit Process?')
    previous_company_ids = fields.One2many('previous.company', 'entry_id', string="Previous Company")
    not_prod_allocation = fields.Boolean(string='Product Allocation Done?', compute="_compute_allocation_done")

    @api.one
    @api.depends('emp_entry_product_ids')
    def _compute_allocation_done(self):
        for each in self.emp_entry_product_ids:
            if each.state_product == 'not_allocated':
                self.not_prod_allocation = True

    @api.multi
    def product_lot_allocation(self):
        product_list = []
        line_ids = self.emp_entry_product_ids.filtered(lambda r: r.state_product == 'not_allocated')
        for line in line_ids:
            product_list.append((0, 0 ,{
                                       'product_id': line.product_id.id,
                                       'serial_num': line.serial_num.id,
                                       'state_product': 'not_allocated'
                                       }))
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'entry.product.wiz',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'context': {'default_allocation_product_line_ids': product_list}
                }

    @api.multi
    def employee_details_verification(self):
        for each in self.emp_document_ids:
            if not each.doc_image:
                self.state = 'draft'
                raise ValidationError(_('Please upload the document for "%s".'
                                        %each.emp_doc_id.name))
            elif each.doc_image:
                each.state = 'uploaded'
                self.state = 'entry_done'
        for each in self.emp_entry_product_ids:
            if each.state_product != 'allocated':
                self.state = 'draft'
                raise ValidationError(_('"%s" is not allocated.\nPlease allocate the product.'
                                        %each.product_id.name))
            elif each.state_product == 'allocated':
                self.state = 'entry_done'

    @api.multi
    def emp_exit(self):
        return {
                'type': 'ir.actions.act_window',
                'name': _('Exit Form'),
                'res_model': 'employee.exit',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_employee_id': self.employee_id.id,
                            'default_job_id': self.job_id.id,
                            'default_department_id': self.department_id.id,
                           }
                }


class emp_doc_line(models.Model):
    _name = 'emp.doc.line'


    entry_id = fields.Many2one('employee.entry')
    exit_id = fields.Many2one('employee.exit')
    emp_doc_id = fields.Many2one('employee.document', string="Name")
    file_name = fields.Char(string="document", default="document")
    doc_image = fields.Binary(string="Document")
    state = fields.Selection([('draft', 'Draft'),
                              ('uploaded', 'Uploaded'),
                              ('allocated', 'Allocated')], default='draft', string="State",
                              readonly=False, store=True)


class employee_documents(models.Model):
    _name = 'employee.document'

    name = fields.Char(string="Name", required=True)
    doc_type = fields.Selection([('entry','Entry Document'),
                                 ('exit','Exit Document')], string="Type",
                                 readonly=True, invisible=True) 


class previous_company(models.Model):
    _name ='previous.company'
    
    name = fields.Char(string="Company")
    job_position = fields.Char(string='Job Position')
    description = fields.Char(string="Description")
    experience = fields.Float(String="Work Experience (Years)")
    
    exit_id = fields.Many2one('employee.exit', string="Exit id")
    entry_id = fields.Many2one('employee.entry', string="Entry id")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: