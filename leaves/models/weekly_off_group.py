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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class weekly_off_group(models.Model):
    _name = 'weekly.off.group'

    @api.model
    def create(self, vals):
        res = super(weekly_off_group, self).create(vals)
        if not vals.get('sunday') and not vals.get('monday') and not vals.get('tuesday') \
        and not vals.get('wednesday') and not vals.get('thursday') and not vals.get('friday') \
        and not vals.get('saturday'):
            raise Warning(_('Please select day for week off.'))
        if vals.get('res_group_ids'):
            existing_grp_id = self.search([('active', '=', True),
                                           ('res_group_ids', 'in', vals.get('res_group_ids')[0][2]),
                                           ('id' ,'!=', res.id)])
            if existing_grp_id:
                raise Warning(_('Group is already existing in active week off.'))
            user_ids = [user.id for each in res.res_group_ids for user in each.users]
            employee_ids = self.env['hr.employee'].search([('user_id','in',user_ids)])
            for each_emp in employee_ids:
                each_emp.write({'week_off_ids':[(4,[res.id])]})
        return res

    @api.multi
    def write(self, vals):
        res = super(weekly_off_group, self).write(vals)
        if vals.get('res_group_ids'):
            existing_grp_id = self.search([('active', '=', True),
                                           ('res_group_ids', 'in', vals.get('res_group_ids')[0][2]),
                                           ('id' ,'!=', self.id)])
            if existing_grp_id:
                raise Warning(_('Group is already existing in active week off .'))
            user_ids = [user.id for each in self.res_group_ids for user in each.users]
            employee_ids = self.env['hr.employee'].search([('user_id','in',user_ids)])
            for each_emp in employee_ids:
                each_emp.write({'week_off_ids':[(4,[self.id])]})
        return res

    active = fields.Boolean(string='Active', default=True)
    start_date = fields.Datetime('Starting Date', required=True)
    end_date = fields.Datetime('End Date', required=True)
    name = fields.Char('Name')
    sunday = fields.Boolean('Sunday')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    employee_ids = fields.Many2many('hr.employee', 'employee_week_off', 'week_off_id',
                                    'employee_id', 'Employees')
    res_group_ids = fields.Many2many('res.groups', 'emp_week_off_group', 'emp_week_off_id',
                                    'group_id', 'Groups')
    based_on = fields.Selection([
                              ('group', 'Group'),
                              ('employee','Employee')], string="Based On", default="employee", required=True) 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: