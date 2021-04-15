# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models,fields,api,_

class report_kra(models.AbstractModel):
    _name = 'report.performance_evaluation_rating.kra_eval'
    _description = "Print report for KRA Evaluation"

    @api.multi
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('performance_evaluation_rating.kra_eval')
        docargs = {
            'doc_ids': self.env['kra.evaluation.wiz'].browse(data['id']),
            'doc_model': report.model,
            'docs': self,
            'query': self._get_summary_data
        }
        return docargs


    def _get_summary_data(self, obj):
        if obj.select_report == 'detail':
            dict = {}
            domain = [('year', '=', obj.year),('reviewer_plan','=',obj.reviewer_plan)]
            if obj.department_ids:
                domain += [('department_id.id', 'in', obj.department_ids.ids)]
            if obj.job_ids:
                domain += [('job_id.id', 'in', obj.job_ids.ids)]
            if obj.employee_ids:
                domain += [('employee_id','in', obj.employee_ids.ids)]
            if obj.reviewer_plan == 'month':
                domain += [('month', '=', obj.month)]
                evaluation_record = self.env['kra.evaluation'].search(domain)
            elif obj.reviewer_plan == 'week':
                domain += [('week_nu','=',obj.week_nu),('month', '=', obj.month)]
                evaluation_record = self.env['kra.evaluation'].search(domain)
            else:
                evaluation_record = self.env['kra.evaluation'].search(domain)
            for rec in evaluation_record:
                lst=[]
                for record in rec.que_rating_ids:
                    lst.append({'question': record.questions,
                                  'self_rating': record.self_rating if record.self_rating else '-----',
                                  'manager_rating': record.manager_rating if record.manager_rating else '-----',
                                  'hr_rating': record.hr_rating if record.hr_rating else '-----'})

                dict[rec.employee_id.name] = lst
            return dict
        else:
            lst = []
            domain = [('year', '=', obj.year), ('reviewer_plan', '=', obj.reviewer_plan)]
            if obj.department_ids:
                domain += [('department_id.id', 'in', obj.department_ids.ids)]
            if obj.job_ids:
                domain += [('job_id.id', 'in', obj.job_ids.ids)]
            if obj.reviewer_plan == 'month':
                domain += [('month', '=', obj.month)]
                evaluation_record = self.env['kra.evaluation'].search(domain)
            elif obj.reviewer_plan == 'week':
                domain += [('week_nu', '=', obj.week_nu), ('month', '=', obj.month)]
                evaluation_record = self.env['kra.evaluation'].search(domain)
            else:
                evaluation_record = self.env['kra.evaluation'].search(domain)
            for rec in evaluation_record:
                total_self = 0
                total_manager = 0
                total_hr = 0
                for record in rec.que_rating_ids:
                    total_self += record.self_rating
                    total_manager += record.manager_rating
                    total_hr += record.hr_rating
                lst.append({'name': rec.employee_id.name,
                            'reviewer': rec.reviewer_id.name,
                            'department': rec.department_id.name,
                            'job_pos': rec.job_id.name,
                            'total_self': total_self,
                            'total_manager': total_manager,
                            'total_hr': total_hr})
            return lst




