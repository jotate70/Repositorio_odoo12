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
from datetime import date
import time


class hr_public_holiday(models.Model):
    _name = 'hr.public.holiday'

    @api.multi
    def ongoing_close(self):
        self.state = 'close'
        data_list = []
        phl_ids = self.env['hr.public.holiday.line'].search([('public_holiday_id','=',self._ids)])
        for line in phl_ids:
            data_list.append((0,0,{'name': line.name,'holiday_date': line.holiday_date}))
        for each in self.search([]):
            self.create({'name': str(date.today().year) + ' ' + 'Holidays' ,
                         'start_date': each.start_date,
                         'end_date': each.end_date,
                         'hr_phl_ids': data_list})

    name = fields.Char('Name', required=True)
    start_date = fields.Date('Starting Date', required=True)
    end_date = fields.Date('End Date', required=True)
    hr_phl_ids = fields.One2many('hr.public.holiday.line', 'public_holiday_id',
                                 'Public Hoildays')
    state = fields.Selection([('open','Open'), ('close','Close')], 'State', default='open')


class hr_public_holiday_line(models.Model):
    _name = "hr.public.holiday.line"

    @api.model
    def create(self, vals):
        res = super(hr_public_holiday_line, self).create(vals)
        if not res.holiday_date >= res.public_holiday_id.start_date or \
        not res.holiday_date <= res.public_holiday_id.end_date:
            raise Warning(_('Select the date between %s and %s') 
                          % (res.public_holiday_id.start_date, res.public_holiday_id.end_date))
        return res

    @api.multi
    def write(self, vals):
        res = super(hr_public_holiday_line, self).write(vals)
        if not self.holiday_date >= self.public_holiday_id.start_date or \
        not self.holiday_date <= self.public_holiday_id.end_date:
            raise Warning(_('Select the date between %s and %s') 
                          % (self.public_holiday_id.start_date, self.public_holiday_id.end_date))
        return res

    name = fields.Char('Name', required=True)
    holiday_date = fields.Date('Date', required=True)
    public_holiday_id = fields.Many2one('hr.public.holiday', 'Public Holiday')
    type = fields.Selection([('working','Working'), ('holiday','Holiday')], 
                              string='Type', default='holiday')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: