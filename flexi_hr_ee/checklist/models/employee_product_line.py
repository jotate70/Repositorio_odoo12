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
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from datetime import date
import calendar


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    
    @api.model
    def default_get(self, fieldsname):
        res = super(stock_production_lot, self).default_get(fieldsname)
        if self.env.context.get('product_id'):
            res.update({'product_id': self.env.context.get('product_id')})
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('product_id'):
            if args is None:
                args = []
            company_id = self.env['res.company']._company_default_get('flexi_hr_ee')
            warehouse_id = self.env['stock.warehouse'].search([
                                                     ('company_id', '=', company_id.id)], 
                                                     limit=1)
            lot_ids = self.search([('product_id', '=', self._context.get('product_id'))])
            quant_ids = self.env['stock.quant'].search([('location_id', '=', warehouse_id.lot_stock_id.id),
                                                        ('lot_id', 'in', lot_ids.ids),
                                                        ('quantity', '>', 0)])
            if lot_ids:
                return lot_ids.name_get()
        else:
            return super(stock_production_lot, self).name_search()


class emp_product_line(models.Model):
    _name = 'emp.product.line'

    product_entry_id = fields.Many2one('employee.entry', ondelete="cascade")
    product_exit_id = fields.Many2one('employee.exit', ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Product(s)")
    serial_num =  fields.Many2one('stock.production.lot', string="Serial No.")
    require_serial = fields.Boolean(string='Require Serial Number')
    state_product = fields.Selection([('not_allocated', 'Not Allocated'),
                                      ('allocated','Allocated'),
                                      ('collected','Collected')], default='not_allocated', string="State")
    state = fields.Selection([('draft','Allocated'),
                              ('collected', 'Collected'),
                              ('verified', 'Verified'),
                              ('paid','Paid'),
                              ('completed','Process Complete')], default='draft', string="State")
    product_is = fields.Selection([('damaged', 'Damaged'),
                                    ('lost', 'Lost')], string='Product is:')
    pay_check = fields.Boolean(string="Need to Pay")
    file_name = fields.Char(string="document", default="document")
    doc_image = fields.Binary(string="Attachment(optional)")
    charged_amt = fields.Integer(string='Charged Amount')
    payment_by = fields.Selection([('cheque', 'Cheque'),
                                   ('last_salary', 'Last Salary'),
                                   ('cash', 'Cash')], default='last_salary')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    last_sal_date = fields.Date('Last Salary Date')
    disburse_date = fields.Date('Disburse Date')
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    stock_picking_id = fields.Many2one("stock.picking", string="Picking", required=False)
    net_salary = fields.Float(string="Net Salary")
    journal_id = fields.Many2one('account.journal', string="Journal")
    
    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id and self.product_id.product_tmpl_id.tracking != 'none':
            self.require_serial = True
        else:
            self.require_serial = False
        
    @api.multi
    def assign_product(self):
        if self.product_id.type == 'product':
            stock_config_id = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)
            if stock_config_id and stock_config_id.group_stock_multi_warehouses:
                self.update({'state_product': 'allocated'})
                company_id = self.env['res.company']._company_default_get('flexi_hr_ee')
                warehouse_id = self.env['stock.warehouse'].search([
                                                         ('company_id', '=', company_id.id)], 
                                                         limit=1)
                dest_location_id, loc_id = self.env['stock.warehouse']._get_partner_locations()
                if company_id:
                    picking_type_id = self.env['stock.picking.type'].search([
                                       ('default_location_dest_id', '=', warehouse_id.lot_stock_id.id), 
                                       ('code', '=', 'internal')], limit=1)
                move_line_list = []
                picking = self.env['stock.picking']
                move_line_list.append((0, 0, {
                                              'product_id': self.product_id.id,
                                              'product_uom_id': self.product_id.uom_id.id,
                                              'product_uom_qty': 0,
                                              'qty_done': 1,
                                              'location_id': warehouse_id.lot_stock_id.id,
                                              'location_dest_id': dest_location_id.id,
                                              'lot_id': self.serial_num.id if self.serial_num else False
                                              }))
                if warehouse_id.lot_stock_id and picking_type_id:
                    picking_id = picking.create({
                                                'employee_id': self.product_entry_id.employee_id.id,
                                                'origin': self.product_entry_id.name,
                                                'location_id': warehouse_id.lot_stock_id.id,
                                                'location_dest_id': dest_location_id.id,
                                                'move_line_ids': move_line_list,
                                                'move_type': 'direct',
                                                'picking_type_id': picking_type_id.id,
                                                })
                    picking_id.action_confirm()
#                     picking_id.force_assign()  
                    picking_id.button_validate()
            else:
                raise ValidationError(_('Please enable multiple warehouse location from Inventory > Configuration > Setting.'))
        else:
            self.update({'state_product': 'allocated'})
        
         
    @api.onchange('payment_by', 'charged_amt')
    def payment_by_last_salar(self):
        if self.state_product == 'collected':
            date_list = []
            if self.payment_by == 'last_salary':
                if self.product_is == 'damaged' and self.charged_amt > 0:
                    self.last_sal_date = (datetime.strptime\
                                          (self.product_exit_id.leaving_date, "%Y-%m-%d")\
                                          ).replace(day=1)
                    contract_id  = self.env['hr.contract'].search([
                                   ('employee_id', '=', self.product_exit_id.employee_id.id)], 
                                   order="id desc", limit=1)
                    if contract_id:
                        from_dt = fields.Datetime.from_string(self.last_sal_date)
                        to_dt = fields.Datetime.from_string(self.product_exit_id.leaving_date)
                        diff = to_dt - from_dt
                        to_hour = 0
                        day_list = []
                        for working_hour in contract_id.employee_id.resource_calendar_id.attendance_ids:
                            if int(working_hour.dayofweek) not in day_list:
                                day_list.append(int(working_hour.dayofweek))
                            to_hour += working_hour.hour_to - working_hour.hour_from
            #                 current = time.time()
                        working_days = 0
                        working_days_monthly = 0
                        hr_hoilday_unpaid = self.env['hr.leave'].search([
                                            ('date_from', '>=', datetime.strptime(self.last_sal_date, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')),
                                            ('date_to', '<=', datetime.strptime(self.product_exit_id.leaving_date, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')),
                                            ('holiday_status_id.name', '=', 'Unpaid'),
                                            ('state', '=', 'validate')])
                        unpaid_days = 0
                        for unpaid in hr_hoilday_unpaid:
                            unpaid_from_dt = fields.Datetime.from_string(unpaid.date_from)
                            unpaid_to_dt = fields.Datetime.from_string(unpaid.date_to)
                            unpaid_diff = unpaid_to_dt - unpaid_from_dt
                            for i in range(unpaid_diff.days + 1):
                                unpaid_date = unpaid_from_dt + timedelta(days=i)
                                if unpaid_date.weekday() in day_list:
            #                         working_days += 1
                                    unpaid_days += 1
                        for i in range(diff.days + 1):
                            date = from_dt + timedelta(days=i)
                            if date.weekday() in day_list:
                                working_days += 1
                        total_working_days = working_days if working_days > 0 else 0
                        actual_working_days = total_working_days - unpaid_days
                        last_day = calendar.monthrange(int(datetime.strptime(self.last_sal_date, '%Y-%m-%d').strftime('%Y')) , int(datetime.strptime(self.last_sal_date, '%Y-%m-%d').strftime('%m')))
                        diff_whole_month = to_dt.replace(day=last_day[1]) - from_dt
                        
                        for i in range(diff_whole_month.days + 1):
                            date = from_dt + timedelta(days=i)
                            if date.weekday() in day_list:
                                working_days_monthly += 1
                        total_working_days_monthly = working_days_monthly if working_days_monthly > 0 else 0
                        
                        net_sal = contract_id.wage / total_working_days_monthly
                        self.net_salary = net_sal * actual_working_days
                        if self.net_salary < self.charged_amt:
                            raise ValidationError(_('Employee does not have enough last salary to pay damaged amount. \
                                                    Please select another payment option.')%self.net_salary)
                        else:
                            amount = self.charged_amt
                            date_list.append((0, 0, {
                                                    'date': self.last_sal_date,
                                                    'amount': amount,
                                                    'payment_by': self.payment_by
                                                    }))
                            self.damaged_product_ids = date_list
            else:
                self.last_sal_date = False 
                self.damaged_product_ids = []
                    
        else:
            raise ValidationError(_('Please collect the product first.'))

    @api.multi
    def not_assign_product(self):
        if self.product_exit_id.state == 'sent_hr':
            self.update({'state_product': 'collected',
                         'state': 'collected'})
            company_id = self.env['res.company']._company_default_get('flexi_hr_ee')
            warehouse_id = self.env['stock.warehouse'].search([
                                                        ('company_id', '=', company_id.id)], 
                                                        limit=1)
            source_location_id, loc_id = self.env['stock.warehouse']._get_partner_locations()
            picking_type_id = self.env['stock.picking.type'].search([
                                                       ('warehouse_id.company_id', '=', company_id.id), 
                                                       ('code', '=', 'internal')], limit=1)
            move_line_list = []
            picking = self.env['stock.picking']
            
            
            move_line_list.append((0, 0, {
                                          'product_id': self.product_id.id,
                                          'product_uom_id': self.product_id.uom_id.id,
                                          'product_uom_qty': 0,
                                          'qty_done': 1,
                                          'location_id': source_location_id.id,
                                          'location_dest_id': warehouse_id.lot_stock_id.id,
                                          'lot_id': self.serial_num.id if self.serial_num else False
                                          }))
            if warehouse_id.lot_stock_id and picking_type_id:
                picking_id = picking.create({
                                            'employee_id': self.product_entry_id.employee_id.id,
                                            'origin': self.product_exit_id.name,
                                            'location_id': source_location_id.id,
                                            'location_dest_id': warehouse_id.lot_stock_id.id,
                                            'move_line_ids': move_line_list,
                                            'move_type': 'direct',
                                            'picking_type_id': picking_type_id.id,
                                            })
            picking_id.action_confirm()
#             picking_id.force_assign()  
            picking_id.button_validate()
        else:
            raise ValidationError(_('Product can not be collected right now.'))

    @api.one
    def verify_product(self):
        self.update({'state': 'verified'})

    @api.one
    def pay_now(self):
        if self.state_product == 'collected':
            if self.payment_by == 'cash':
                move_line = []
                journal_id = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
                payable_acc_id = self.env['account.account'].search([('user_type_id.type','=', 'payable')], limit=1)
                rec_acc_id = self.env['account.account'].search([('user_type_id.type','=', 'receivable')], limit=1)
                if not journal_id:
                    raise ValidationError(_('Please create the journal for cash type.'))
                move_line.append((0, 0, {
                                         'account_id': rec_acc_id.id,
                                         'name': '/',
                                         'debit': self.charged_amt,
                                         'credit': 0
                                         }))
                move_line.append((0, 0, {
                                         'account_id': payable_acc_id.id,
                                         'name': '/',
                                         'debit': 0,
                                         'credit': self.charged_amt
                                         }))
                move_id = self.env['account.move'].create({
                                                           'date': date.today(),
                                                           'journal_id': journal_id.id,
                                                           'ref': self.product_exit_id.name,
                                                           'line_ids': move_line
                                                           })
                move_id.post()
                self.update({
                            'state': 'paid', 'move_id': move_id.id, 
                            'disburse_date':  date.today()
                            })
                return True
        else:
            raise ValidationError(_('Please collect the product first.'))

    @api.one
    def process_complete(self):
        self.update({'state': 'completed'})

    @api.multi
    def disburse_amt(self):
        return {
                'type': 'ir.actions.act_window',
                'name': _('Damaged Product Amount Disbursement'),
                'res_model': 'disburse.checklist.wiz',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {'journal_id': self.journal_id.id}
                }
