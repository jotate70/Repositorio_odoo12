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

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class product_allocation(models.Model):
    _name = 'product.allocation'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    allocation_product_line_ids = fields.One2many('product.allocation.wiz.line', 'product_allocation_wiz_id', string="Product(s)")

    @api.multi
    def allocation_product_main(self):
        stock_config_id = self.env['res.config.settings'].sudo().search([],order="id desc", limit=1)
        if stock_config_id and stock_config_id.group_stock_multi_warehouses:
            prod_list = []
            emp_entry_id = self.env['employee.entry'].search([
                                                    ('state', '!=', 'exited'),
                                                    ('employee_id', '=', self.employee_id.id)])
            if emp_entry_id:
                for each in self.allocation_product_line_ids:
                    line_id = self.env['emp.product.line'].create({
                                                        'require': True,
                                                        'serial_num': each.serial_num.id if each.serial_num.id else "",
                                                        'product_id': each.product_id.id,
                                                        'product_entry_id': emp_entry_id.id,
                                                        'state_product': 'allocated'
                                                        })
                    emp_entry_id.write({'emp_entry_product_ids': [(4,line_id.id)]})
                company_id = self.env['res.company']._company_default_get('flexi_hr_ee')
                warehouse_id = self.env['stock.warehouse'].search([
                                                         ('company_id', '=', company_id.id)], 
                                                         limit=1)
                dest_location_id, loc_id = self.env['stock.warehouse']._get_partner_locations()
                if company_id:
                    picking_type_id = self.env['stock.picking.type'].search([
                                       ('default_location_dest_id', '=', warehouse_id.lot_stock_id.id), 
                                       ('code', '=', 'internal')], limit=1)
                stock_move_list = []
                move_line_list = []
                picking = self.env['stock.picking']
                for each_line in self.allocation_product_line_ids:
                    if each_line.product_id.type == 'product':
                        move_line_list.append((0, 0, {
                                                      'product_id': each_line.product_id.id,
                                                      'product_uom_id': each_line.product_id.uom_id.id,
                                                      'product_uom_qty': 0,
                                                      'qty_done': 1,
                                                      'location_id': warehouse_id.lot_stock_id.id,
                                                      'location_dest_id': dest_location_id.id,
                                                      'lot_id': each_line.serial_num.id if each_line.serial_num else False
                                                      }))
                if warehouse_id.lot_stock_id and picking_type_id and move_line_list:
                    picking_id = picking.create({
                                                'employee_id': emp_entry_id.employee_id.id,
                                                'origin': emp_entry_id.name,
                                                'location_id': warehouse_id.lot_stock_id.id,
                                                'location_dest_id': dest_location_id.id,
                                                'move_line_ids': move_line_list,
                                                'move_type': 'direct',
                                                'picking_type_id': picking_type_id.id,
                                                })
                    picking_id.action_confirm()
                    picking_id.force_assign()
                    picking_id.button_validate()
            else:
                raise ValidationError(_('This employee has no Entry details.'))
        else:
            raise ValidationError(_('Please enable multiple warehouse location from Inventory > Configuration > Setting.'))    
            

class product_allocation_wiz_line(models.Model):
    _name = 'product.allocation.wiz.line'

    product_id = fields.Many2one('product.product', string="Product(s)")
    serial_num =  fields.Many2one('stock.production.lot', string="Serial No.")
    product_allocation_wiz_id = fields.Many2one('product.allocation', string="Product(s)")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: