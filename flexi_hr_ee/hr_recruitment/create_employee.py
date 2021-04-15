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
from datetime import date
from odoo.exceptions import ValidationError,UserError


class family_member_detail(models.Model):
    _name = 'family.member.detail'
    
    name = fields.Char(string="Name")
    relation = fields.Char(string="Relation")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    

class employee_additionalcertificate(models.Model):
    _name = 'employee.additional.certificate'
    
    YEARS = []
    for year in range(int(date.today().strftime('%Y')) - 10 , int(date.today().strftime('%Y')) + 1):
        YEARS.append((str(year), str(year)))
    
    name = fields.Char(string="Name")
    year = fields.Selection(YEARS, string="Year",default=date.today().strftime('%Y'))
    employee_id = fields.Many2one('hr.employee', string="Employee")


class employee_additional_benefit(models.Model):
    _name = 'employee.additional.benefit'
    
    name = fields.Char(string="Benefit Name")
    employee_id = fields.Many2one('hr.employee', string="Employee")


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    trainee_start_date = fields.Date("Start Date")
    trainee_end_date = fields.Date("End Date")
    join_date = fields.Date('Join Date')
    release_date = fields.Date('Release Date')
    training_history_ids = fields.One2many('employee.training.history', 'employee_id')
    entry_id = fields.Many2one('employee.entry', string="Entry ID")
    is_trainee = fields.Boolean(string="Is Trainee?")
    emp_entry = fields.Boolean('Employee Entry created?', compute="_compute_emp_entry", store=True)
    family_member_ids = fields.One2many('family.member.detail', 'employee_id', string="Family Members")
    certificate_ids = fields.One2many('employee.additional.certificate', 'employee_id', string="Certificates")
    benefit_ids = fields.One2many('employee.additional.benefit', 'employee_id', string="Benefits")
    perm_street = fields.Char(string="Permanent Address")
    perm_street2 = fields.Char(string="Street2")
    perm_city = fields.Char(string="City")
    perm_state_id = fields.Many2one('res.country.state', string="State")
    perm_zip = fields.Char(string="ZIP")
    perm_country_id = fields.Many2one('res.country', string="Country")
    pre_street = fields.Char(string="Present Street") 
    pre_street2 = fields.Char(string="Street2")
    pre_city = fields.Char(string="City")
    pre_state_id = fields.Many2one('res.country.state', string="State")
    pre_zip = fields.Char(string="ZIP") 
    pre_country_id = fields.Many2one('res.country', string="Country")
    type_ids = fields.Many2many('hr.recruitment.degree', 'degree_emp_rel', 'deg_id', 'emp_id', string="Degree")
    
    @api.multi
    @api.depends('entry_id')
    def _compute_emp_entry(self):
        for each in self:
            if each.entry_id:
                each.emp_entry = True
            else:
                each.emp_entry = False
    
    @api.one
    @api.constrains('trainee_start_date', 'trainee_end_date')
    def _dates_validation(self):
        if self.trainee_end_date and self.trainee_start_date:
            if datetime.datetime.strptime(self.trainee_end_date, "%Y-%m-%d") < datetime.datetime.strptime(self.trainee_start_date, "%Y-%m-%d"):
                raise ValidationError(_("End Date should be grater than Start Date."))
    
    @api.multi
    def create_entry(self):
        if not self.job_id:
            raise ValidationError(_('Please select Job Position to start Entry Process.'))
        elif self.trainee_end_date and self.trainee_end_date > date.today():
            raise ValidationError(_("Trainee must complete his training first."))
        else:
            if not self.emp_entry:
                emp_entry_id = self.env['employee.entry'].create({'employee_id': self.id,
                                                                  'job_id': self.job_id.id,
                                                                  'join_date': self.join_date if self.join_date else datetime.date.today(),
                                                                  'department_id': self.department_id.id,
                                                                  'state': 'draft'})
                self.write({'entry_id': emp_entry_id.id,
                            'emp_entry': True})
                employee_action = self.env.ref('flexi_hr_ee.action_aspl_emp_entry_for_recruitment')
                dict_act_window = employee_action.read([])[0]
                dict_act_window['res_id'] = emp_entry_id.id
                dict_act_window['view_mode'] = 'form, tree'
                return dict_act_window
  
    @api.multi
    def extend_period(self):
        view_id = self.env.ref('flexi_hr_ee.employee_training_history_form_view').id
        return {
                'type': 'ir.actions.act_window',
                'name': _('Extend Training'),
                'res_model': 'employee.training.history',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'new',
                'context': {'default_employee_id': self.id,
                            'default_start_date': datetime.datetime.strptime(self.trainee_end_date, "%Y-%m-%d") + relativedelta(days=1),
                            'default_end_date': (datetime.datetime.strptime(self.trainee_end_date, "%Y-%m-%d") + relativedelta(days=1)) if self.trainee_end_date else False}                }


class employee_training_history(models.Model):
    _name = 'employee.training.history'
    
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    duration = fields.Float("Duration (Days)", compute="_compute_duration")
    reason = fields.Text("Reason")

    @api.multi
    def extend_training_save(self):
        return True

    @api.model
    def create(self, vals):
        res = super(employee_training_history, self).create(vals)
        emp_id = self.env['hr.employee'].browse(vals.get('employee_id'))
        emp_id.update({'trainee_end_date': res.end_date})
        return res
        

    @api.multi
    @api.depends('end_date', 'start_date')
    def _compute_duration(self):
        for each in self:
            if each.end_date and each.start_date:
                diff = datetime.datetime.strptime(each.end_date, "%Y-%m-%d") - datetime.datetime.strptime(each.start_date, "%Y-%m-%d")
                each.duration = diff.days
   
    @api.one
    @api.constrains('start_date', 'end_date')
    def _dates_validation(self):
        if datetime.datetime.strptime(self.end_date, "%Y-%m-%d") < datetime.datetime.strptime(self.start_date, "%Y-%m-%d"):
            raise ValidationError(_("End Date should be grater than Start Date."))


class create_employee(models.TransientModel):
    _name = 'create.employee'

    @api.model
    def default_get(self, fieldlist):
        res = super(create_employee, self).default_get(fieldlist)
        contract_type_id = self.env['hr.contract.type'].search([], limit=1)
        config_id = self.env['res.config.settings'].search([], order='id desc', limit=1)
        res.update({'contract_type_id':contract_type_id.id,
                    'resource_id':config_id.resource_calendar_id.id if config_id and config_id.resource_calendar_id else False
                    })
        return  res

    contract_id = fields.Many2one('hr.contract', string="Contract")
    application_for = fields.Selection([('employee', 'Employee'),
                                        ('trainee', 'Trainee'),
                                        ('on_probation_period', 'Employee On Probation Period')],
                                        string="Application For", default='employee')
    stipend = fields.Boolean("Stipend")
    contract = fields.Boolean("Contract")
    contract_name = fields.Char(string='Contract Name')
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type")
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    wage = fields.Float('Wage', help="Employee's monthly gross wage.")
    contract_date_start = fields.Date("Start Date", default=datetime.date.today())
    contract_date_end = fields.Date("End Date")
    resource_id = fields.Many2one("resource.calendar", 'Working Schedule')

    @api.one
    @api.constrains('contract_date_start', 'contract_date_end')
    def _dates_validation(self):
        if self.contract_date_end and self.contract_date_start:
            if datetime.datetime.strptime(self.contract_date_end, "%Y-%m-%d") < datetime.datetime.strptime(self.contract_date_start, "%Y-%m-%d"):
                raise ValidationError(_("End Date should be grater than Start Date."))

    @api.multi
    @api.onchange('application_for')
    def _onchange_application_for(self):
        if self.application_for == 'trainee':
            self.contract = False
            self.contract_date_end = datetime.datetime.strptime(self.contract_date_start, "%Y-%m-%d") + relativedelta(months=6)
        else:
            self.contract = True

    @api.one
    @api.constrains('wage')
    def _check_wage(self):
        if self.wage <= 0.0:
            if self.contract or self.stipend:
                raise ValidationError(_("Please enter valid Wage."))
    
    @api.multi
    def create_employee_custom(self):
        applicant = self.env['hr.applicant'].browse(self.env.context.get('active_id'))
        if not applicant.emp_id:
            employee = False
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else :
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id and applicant.company_id.partner_id
                            and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.email or False,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.phone or False,
                    'employee_status': 'trainee' if self.application_for == 'trainee' else 'on_probation_period' if self.application_for == 'on_probation_period' else 'emp' ,
                    'trainee_start_date': self.contract_date_start if self.application_for == 'trainee' else False,
                    'trainee_end_date': self.contract_date_end if self.application_for == 'trainee' else False,
                    'is_trainee': True if self.application_for == 'trainee' else False,
                    'join_date': self.contract_date_start,
                    'type_ids': [(6, 0, applicant.type_ids.ids)] if applicant.type_ids else False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
#                 employee._broadcast_welcome()
            else:
                raise ValidationError(_('You must define an Applied Job and a Contact Name for this applicant.'))
        if self.application_for == 'trainee':
            training_history_id = self.env['employee.training.history'].create({
                                                                            'employee_id':applicant.emp_id.id,
                                                                            'start_date': self.contract_date_start if self.application_for == 'trainee' else False,
                                                                            'end_date': self.contract_date_end if self.application_for == 'trainee' else False
                                                                                })
            
        if not self.contract_id:
            if self.contract or self.stipend:
                journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                hr_contarct_id = self.env['hr.contract'].create({'employee_id': applicant.emp_id.id,
                                                                  'department_id': applicant.department_id.id,
                                                                  'job_id': applicant.job_id.id,
                                                                  'name': self.contract_name,
                                                                  'type_id': self.contract_type_id.id,
                                                                  'struct_id': self.struct_id.id,
                                                                  'wage': self.wage,
                                                                  'date_start': self.contract_date_start,
                                                                  'date_end': self.contract_date_end if self.contract_date_start else False,
                                                                  'resource_calendar_id': self.resource_id.id,
                                                                  'state': 'draft',
                                                                  'journal_id': journal_id.id if journal_id else False })
                
                applicant.write({'contract_id': hr_contarct_id.id})
                self.write({'contract_id': hr_contarct_id.id})
        if self.application_for != 'trainee':
            
            emp_entry_search_id = self.env['employee.entry'].search([('employee_id', '=', applicant.emp_id.id)])
        
            if emp_entry_search_id:
                applicant.emp_id.write({'entry_id': emp_entry_search_id.id})
                applicant.write({'emp_entry_id': emp_entry_search_id.id})
                employee_action = self.env.ref('flexi_hr_ee.action_aspl_emp_entry_for_recruitment')
                dict_act_window = employee_action.read([])[0]
                dict_act_window['res_id'] = emp_entry_search_id.id
                dict_act_window['view_mode'] = 'form, tree'
                return dict_act_window
            else:
                employee_entry_id = self.env['employee.entry'].create({'employee_id': applicant.emp_id.id,
                                                                       'job_id': applicant.emp_id.job_id.id,
                                                                       'department_id': applicant.emp_id.department_id.id,
                                                                       'state': 'draft',
                                                                       'join_date': applicant.emp_id.join_date if applicant.emp_id.join_date else datetime.date.today(),  
                                                                       'recruitment_id': applicant.id})
                if employee_entry_id:
                    applicant.write({'emp_entry_id': employee_entry_id.id})
                    applicant.emp_id.write({'entry_id': employee_entry_id.id})
                    employee_action = self.env.ref('flexi_hr_ee.action_aspl_emp_entry_for_recruitment')
                    dict_act_window = employee_action.read([])[0]
                    dict_act_window['res_id'] = employee_entry_id.id
                    dict_act_window['view_mode'] = 'form, tree'
        
                    return dict_act_window
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
