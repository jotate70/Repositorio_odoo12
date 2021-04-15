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

from odoo import models, fields, api, SUPERUSER_ID, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import datetime
from datetime import date
from lxml import etree
from odoo.osv.orm import setup_modifiers


class employee_exit(models.Model):
    _name = 'employee.exit'
    _description = 'Employee Exit'
    _inherit = 'mail.thread'
    _order = 'id desc'

    @api.model
    def create(self, vals):
        seq_num = self.env['ir.sequence'].next_by_code('employee.exit.form.number')
        if seq_num:
            vals.update({'name': seq_num})
        docs = []
        checklist_setting_id = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)
        if checklist_setting_id:
            for each_doc in checklist_setting_id.exit_document_ids:
                doc_dict = {
                            'emp_doc_id': each_doc.id,
                            'state': 'draft'
                            }
                docs.append((0, 0, doc_dict))
        entry_id = self.env['employee.entry'].search([('employee_id', '=', vals.get('employee_id')),
                                                       ('state', '=', 'entry_done')], limit=1)
        if entry_id:
            entry_id.update({'emp_exit_init': True})
        
        employee_id = self.env['hr.employee'].search([('id', '=', vals.get('employee_id'))], limit=1)
        if employee_id:
            employee_id.update({'exit_initiated': True})
        product_list = []
        for each in entry_id.emp_entry_product_ids:
            if each.state_product == 'allocated':
                product_dict = {
                                'product_id': each.product_id.id,
                                'product_exit_id': self.id,
                                'state_product': 'allocated',
                                'state': 'draft',
                                'serial_num': each.serial_num.id
                                }
                product_list.append((0, 0, product_dict))
        pre_company_list = []
        for each in entry_id.previous_company_ids:
            pre_company_dict = {
                                'name': each.name,
                                'description': each.description,
                                'job_position': each.job_position,
                                'experience': each.experience
                                }
            pre_company_list.append((0, 0, pre_company_dict))
        vals.update({'emp_document_ids': docs,
                     'emp_product_ids': product_list,
                     'previous_company_ids': pre_company_list,
                     })
        return super(employee_exit, self).create(vals)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    resign_date = fields.Date(string="Resign Date",default=date.today(), required=True)
    department_id = fields.Many2one('hr.department', string="Department")
    notice_period = fields.Integer(string="Notice Period")
    leaving_date = fields.Date(string="Release Date", compute="onchange_notice_period", store=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('sent_admin', 'Sent to Manager'),
                              ('sent_hr', 'Sent to HR'),
                              ('verified', 'Verified'),
                              ('exit_done', 'Closed'),
                              ('cancel', 'Cancelled')], default='draft', string="State")
    name = fields.Char('Name')
    emp_document_ids = fields.One2many('emp.doc.line','exit_id', string="Documents")
    emp_product_ids = fields.One2many('emp.product.line', 'product_exit_id', string="Product(s)")
    manager_appr_req = fields.Boolean('Require Manager Approval?')
    previous_company_ids = fields.One2many('previous.company', 'exit_id', string="Previous Company")
    note = fields.Text(string="Note(s)")
    not_prod_collection = fields.Boolean(string='Product Allocation Done?', compute="_compute_collection_done")

    @api.one
    @api.depends('emp_product_ids')
    def _compute_collection_done(self):
        for each in self.emp_product_ids:
            if each.state_product == 'allocated':
                self.not_prod_collection = True

    @api.onchange('employee_id')
    def onchange_emp(self):
        self.job_id = self.employee_id.job_id.id
        self.department_id = self.employee_id.department_id.id
        
    @api.one
    @api.depends('notice_period','resign_date')
    def onchange_notice_period(self):
        if self.notice_period:
            self.leaving_date = datetime.datetime.strptime(self.resign_date, "%Y-%m-%d") + relativedelta(days=self.notice_period)
        else:
            self.leaving_date = self.resign_date
            
    @api.one
    @api.constrains('notice_period')
    def check_notice_period(self):
        erp_magr_gid = self.env.ref('base.group_erp_manager').id
        user_group_ids = self.env['res.users'].browse(self._uid).groups_id.ids
        hr_magr_gid = self.env.ref('hr.group_hr_manager').id
        if not self.manager_appr_req and hr_magr_gid not in user_group_ids and self.state == 'sent_hr':
            raise ValidationError(_('Only HR Manager can enter Notice Period.'))
        if self.manager_appr_req and self.state in ('sent_admin', 'sent_hr') \
            and erp_magr_gid not in user_group_ids \
            and self.employee_id.parent_id.user_id.id != self._uid:
                raise ValidationError (_('Only Employee Manager or Administrator can enter Notice Period.'))
            
    @api.multi
    def product_lot_collection(self):
        product_list = []
        line_ids = self.emp_product_ids.filtered(lambda r: r.state_product == 'allocated')
        for line in line_ids:
            product_list.append((0, 0 ,{
                                       'product_id': line.product_id.id,
                                       'serial_num': line.serial_num.id,
                                       'state_product': 'allocated'
                                       }))
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'exit.product.wiz',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'context': {'default_collection_product_line_ids': product_list}
                }
    
    @api.one
    def sent_admin(self):
        self.state='sent_admin'

    @api.multi
    def sent_hr(self):
        self.state = 'sent_hr'

    @api.multi
    def verify_resignation(self):
        for each in self.emp_document_ids:
            if not each.doc_image:
                raise ValidationError(_('Please upload the document for "%s".'
                                        %each.emp_doc_id.name))
            elif each.doc_image:
                each.state = 'allocated'
                self.state = 'verified'
        
        for each in self.emp_product_ids:
            if each.state_product != 'collected':
                raise ValidationError(_('"%s" is not Collected.\nPlease collect the product.'
                                        %each.product_id.name))
            elif each.state != 'completed':
                raise ValidationError(_('All returned product process must be completed.'))
        template = self.env.ref('flexi_hr_ee.email_emp_notice_period_template')
        if template:
            result=template.send_mail(self.ids[0], force_send=True)
        self.state = "verified"
        self.employee_id.update({'notice_period': self.notice_period,
                                 'employee_status': 'on_notice_period',
                                 'release_date': self.leaving_date
                                        })

    @api.multi
    def approve_resignation(self):
        self.state = 'exit_done'
        entry_id = self.env['employee.entry'].search([('employee_id', '=', self.employee_id.id)], limit=1, order='id desc')
        if entry_id:
            entry_id.update({'state': 'exited'})
        self.employee_id.update({'employee_status': 'ex_emp'})
        return {
                'type': 'ir.actions.act_window',
                'name': _('Review'),
                'res_model': 'exit.review',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'
            }

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda reg: reg.state not in ('draft'))):
            raise ValidationError(_("You cannot delete any employee details once it is created."))
        return super(employee_exit, self).unlink()

    @api.multi
    def cancel_reason(self):
        entry_id = self.env['employee.entry'].search([('employee_id', '=', self.employee_id.id)])
        if entry_id:
            entry_id.update({'state': 'entry_done'})
        self.employee_id.update({'employee_status': 'emp'})
        return {
                'type': 'ir.actions.act_window',
                'name': _('Reason of Cancellation'),
                'res_model': 'reason.cancel',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'
            }
    
    @api.multi
    def action_makeMeeting_custom(self):
        """ This opens Meeting's calendar view to schedule meeting on current applicant
            @return: Dictionary value for created Meeting view
        """
        if self.env.context.get('from_exit'):
            self.ensure_one()
            employees = self.employee_id | self.department_id.manager_id
            category = self.env.ref('hr_recruitment.categ_meet_interview')
            res = self.env['ir.actions.act_window'].for_xml_id('flexi_hr_ee', 'action_calendar_event_from_employee_form')
            res['context'] = {
                'default_emplpoyee_ids': employees.ids,
                'default_user_id': self.env.uid,
                'default_name': self.employee_id.name+' '+self.name,
                'default_categ_ids': category and [category.id] or False,
            }
            return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: