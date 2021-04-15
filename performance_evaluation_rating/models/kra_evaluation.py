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
from lxml import etree

class kraevaluation(models.Model):
    _name = 'kra.evaluation'
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'

    week_nu = fields.Integer(string="Week Number")
    month = fields.Integer(string="Month")
    year  = fields.Char(string="Year")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    reviewer_id = fields.Many2one('hr.employee', string="Reviewer")
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    reviewer_plan = fields.Selection(string="Reviewer Plan", selection=[("week", "Weekly"), ("month", "Monthly"), ("year", "Yearly")], default='week')
    kra_template_id = fields.Many2one('kra.template', string="KRA Template", readonly=False)
    state = fields.Selection([('draft', 'Draft'),('submit','Waiting For Approval'), ('waiting', 'Waiting For HR Approval'),
                             ('done', 'Approved')], string='Status',
                             required=True, readonly=True, copy=False, default='draft',track_visibility='onchange')
    self_review = fields.Boolean(string="Self Review" ,readonly=False, default=False)
    double_validation = fields.Boolean(string="Double Validation" ,readonly=False, default=False)
    internal_msg = fields.Boolean(string="Internal Message" ,readonly=False, default=False)
    que_rating_ids = fields.One2many('kra.question.rating', 'rating_id', string="Questions Rating")
    current_user_id = fields.Boolean(compute="change_reviewer_id")
    hr_manager_user_ids = fields.Many2many('res.users', compute="hr_manager_user_ids_get")

    @api.multi
    def hr_manager_user_ids_get(self):
        self.ensure_one()
        for each in self:
            hr_group_ids = self.env.ref('hr.group_hr_manager').users.ids
            each.hr_manager_user_ids = [(6, 0, hr_group_ids)]

    @api.multi
    def change_reviewer_id(self):
        self.ensure_one()
        for each in self:
            if each.reviewer_id.user_id.id == self._uid:
                each.current_user_id = True
            elif self.env.user.has_group('hr.group_hr_manager'):
                each.current_user_id = True
            else:
                each.current_user_id = False

    @api.model
    def check_user_group(self, group_name):
        has_group = self.env.user.has_group(group_name)
        return has_group

    @api.onchange('department_id', 'job_id')
    def _onchange_job_id(self):
        if self.department_id and self.job_id:
            template_id = self.env['kra.template'].search([('job_id', '=', self.job_id.id), ('department_id', '=', self.department_id.id),('is_active', '=', True)])
            if template_id:
                self.kra_template_id = template_id
            else:
                raise Warning(_('Please configure KRA tempalte for "%s" job position of "%s" department' % (self.job_id.name, self.department_id.name)))

    @api.model
    def create(self, vals):
        config_id = self.env['res.config.settings'].search([], limit=1, order="id desc")
        if config_id:
            vals.update({'self_review': config_id.self_review,
                     'double_validation': config_id.double_validation,
                     'internal_msg': config_id.include_internal_msg})
        res = super(kraevaluation, self).create(vals)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(kraevaluation, self).default_get(fields_list)
        template_id = self.env['kra.template'].search([])
        if not template_id:
            raise Warning(_('Please configure KRA template'))
        return res

    @api.onchange('kra_template_id','department_id','job_id')
    def _change_kra_template(self):
        lst = []
        template_id = self.env['kra.template'].search(
            [('job_id', '=', self.job_id.id), ('department_id', '=', self.department_id.id), ('is_active', '=', True)])
        self.kra_template_id = template_id.id
        for rec in self.kra_template_id.questions_ids:
            lst.append((0,0,{'questions': rec.questions}))
        self.que_rating_ids = lst

    def action_first_approval(self):
        self.state = 'done'

    def action_second_approval(self):
        self.state = 'waiting'

    def action_submit_manager(self):
        self.state = 'submit'

    @api.model
    def find_evaluation(self,rec_id):
        return [self.browse(rec_id[0]).read(), self.browse(rec_id[0]).reviewer_id.user_id.id]


class kraquestionsrating(models.Model):
    _name = 'kra.question.rating'
    _description = 'KRA Questions Rating'

    rating_id = fields.Many2one('kra.evaluation', string="Questions Rating")
    questions = fields.Char(string="Questions")
    self_rating = fields.Selection([(0,'0'),(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], default=0, string="Self Rating")
    self_comment = fields.Char(string="Self Comment")
    manager_rating = fields.Selection([(0,'0'),(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], default=0, string="Manager Rating")
    manager_comment = fields.Char(string="Manager Comment")
    hr_rating = fields.Selection([(0,'0'),(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),(9,'9'),(10,'10')], default=0, string="HR Rating")
    hr_comment = fields.Char(string="HR Comment")








