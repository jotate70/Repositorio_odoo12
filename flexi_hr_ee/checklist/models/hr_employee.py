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

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class hr_employee(models.Model):
    _inherit = "hr.employee"

    employee_status = fields.Selection([('trainee', 'Trainee'),
                                        ('on_probation_period', 'On Probation Period'),
                                        ('emp', 'Employed'),
                                        ('on_notice_period', 'On Notice Period'),
                                        ('ex_emp', 'Ex Employee')], string="Employee Status", default='emp')
    notice_period = fields.Integer(string="Notice Period")
    exit_initiated = fields.Boolean(string="Exit Process Initiated")

    @api.one
    @api.constrains('notice_period')
    def _check_notice_period(self):
        if self.notice_period < 0:
            raise ValidationError(_('Please enter valid Notice Period.'))
   
    @api.multi
    def stock_quant_redirect(self):
        picking_ids = self.env['stock.picking'].search([('employee_id', '=', self.id),
                                                        ('state', 'in', ('assigned', 'done'))])
        list_picking_ids = picking_ids.ids
        for each_picking_1 in picking_ids:
            for each_picking_2 in picking_ids:
                if 'Return of ' + each_picking_1.name == each_picking_2.origin:
                    list_picking_ids.remove(each_picking_1.id)
        stock_move_ids = self.env['stock.move'].search([('picking_id', 'in', list_picking_ids)])
        move_ids = []
        for each in stock_move_ids:
            if each.location_id.usage == 'internal' and each.location_dest_id.usage == 'customer':
                move_ids.append(each.id)
        return {
                'type': 'ir.actions.act_window',
                'name': _('Stock Move'),
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree, form',
                'domain': [('id','in', move_ids)],
                'target': 'current'
                }

    @api.multi
    def emp_exit_form(self):
        entry_id = self.env['employee.entry'].search([('employee_id', '=', self.id)], limit=1)
        if not entry_id:
            raise ValidationError(_("You must create Entry Process for the current employee first."))
        else:
            return {
                    'type': 'ir.actions.act_window',
                    'name': _('Exit Form'),
                    'res_model': 'employee.exit',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'current',
                    'context': {'default_employee_id': self.id,
                                'default_job_id': self.job_id.id if self.job_id else "",
                                'default_department_id': self.department_id.id if self.department_id else ""
                               }
                    }


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    entry_id = fields.Many2one('employee.entry', string='Entry ID')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: