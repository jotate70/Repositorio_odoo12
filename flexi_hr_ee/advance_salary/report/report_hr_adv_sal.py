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

from odoo import api, models
import calendar
from datetime import datetime
from collections import defaultdict, OrderedDict


class report_hr_adv_sal(models.AbstractModel):
    _name = 'report.flexi_hr_ee.template_hr_adv_sal'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('flexi_hr_ee.template_hr_adv_sal')
        return {
               'doc_ids': self.env['summary.wiz'].browse(data['ids']),
               'doc_model': report.model,
               'docs': self,
               'summary_emp': self.summary_emp,
               'get_date': self.get_date,
               }

    def get_date(self,obj):
        start_date = str(obj.required_year) + "-" + obj.summary_month + "-01"
        last_date = str(obj.required_year) + "-" + obj.summary_month + "-"\
                    +str(calendar.monthrange(int(obj.required_year), int(obj.summary_month))[1])
        summary_month = datetime.strftime(datetime.strptime(str(start_date),"%Y-%m-%d"),"%B")
        return [start_date, last_date, summary_month]

    @api.model
    def summary_emp(self,obj):
        if not obj.employee_ids:
           emp_ids = [emp.id for emp in self.env['hr.employee'].search([])]
        else:
            emp_ids = [emp.id for emp in obj.employee_ids]
        if obj.view_by == 'employee':
            query = "SELECT employee_id, name, request_date, approved_date,\
                    disburse_date, approved_amt, state \
                    from hr_advance_salary_request WHERE employee_id IN %s \
                    AND request_date >= %s \
                    AND request_date <= %s"
            params = (tuple(emp_ids), obj.date_from, obj.date_to)
            self.env.cr.execute(query, params)
            results = self.env.cr.dictfetchall()
            emp_dict = defaultdict(list)
            for each in results:
                emp_name = self.env['hr.employee'].browse(each['employee_id']).name
                each.update({'employee_id': emp_name})
                emp_dict[each['employee_id']].append(each)
            return OrderedDict(sorted(dict(emp_dict).items(), key=lambda t: t[0]))
        if obj.view_by == 'state' and not obj.state:
            query = "SELECT employee_id, name, request_date, approved_date,\
                    disburse_date, approved_amt, state \
                    from hr_advance_salary_request WHERE employee_id IN %s \
                    AND request_date >= %s \
                    AND request_date <= %s "
            params = (tuple(emp_ids), obj.date_from, obj.date_to)
            self.env.cr.execute(query, params)
            results = self.env.cr.dictfetchall()
            emp_dict = defaultdict(list)
            for each in results:
                emp_name = self.env['hr.employee'].browse(each['employee_id']).name
                each.update({'employee_id': emp_name})
                emp_dict[each['state']].append(each)
            return OrderedDict(sorted(dict(emp_dict).items(), key=lambda t: t[0]))
        if obj.view_by == 'state' and obj.state:
            adv_sal_ids = self.env['hr.advance.salary.request'].search([
                                                ('employee_id', 'in',emp_ids),
                                                ('state', '=', obj.state),
                                                ('request_date', '>=', obj.date_from),
                                                ('request_date', '<=', obj.date_to)], 
                                                order='employee_id')
            return adv_sal_ids
        if obj.view_by == 'month':
            adv_sal_ids = self.env['hr.advance.salary.request'].search([
                                                ('employee_id', 'in',emp_ids),
                                                ('request_date', '>=', self.get_date(obj)[0]),
                                                ('request_date', '<=', self.get_date(obj)[1])], 
                                                order='employee_id')
            return adv_sal_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: