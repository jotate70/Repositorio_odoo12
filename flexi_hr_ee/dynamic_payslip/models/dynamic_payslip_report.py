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

from openerp import models, api, _
from datetime import datetime
import calendar


class dynamic_payslip_report_temp(models.AbstractModel):
    _name = 'report.flexi_hr_ee.dynamic_payslip_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('flexi_hr_ee.dynamic_payslip_report')
        return {
               'doc_ids': self.env['wizard.dynamic.payslip'].browse(data['ids']),
               'doc_model': report.model,
               'docs': self,
               'summary_emp': self.summary_emp,
               'get_date': self.get_date,
               }
    
    def get_date(self, obj):
        from_date = str(obj.from_year) + "-" + obj.from_month + "-01"
        to_date = str(obj.to_year) + "-" + obj.to_month + "-"\
                    + str(calendar.monthrange(int(obj.to_year), int(obj.to_month))[1])
        watermark_type = obj.watermark_text if obj.watermark_text else obj.watermark_image 
        return [from_date, to_date, watermark_type, obj.watermark_type]
    
    
    @api.model
    def summary_emp(self, obj):
        if not obj.department_ids:
            emp_ids = [emp.id for emp in self.env['hr.employee'].search([])]
        else:
            if not obj.employee_ids:
                emp_ids = [emp.id for emp in self.env['hr.employee'].search([]) if emp.department_id in obj.department_ids] 
            else:
                emp_ids = [emp.id for emp in obj.employee_ids] 
        payslip_ids = self.env['hr.payslip'].search([
                                            ('employee_id', 'in', emp_ids),
                                            ('date_from', '>=', self.get_date(obj)[0]),
                                            ('date_to', '<=', self.get_date(obj)[1]),
                                            ('state', '=', 'done')],
                                            order='employee_id')
        return payslip_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
