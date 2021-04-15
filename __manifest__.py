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

{
    'name': 'Human Resource Solution (Enterprise)',
    'category': 'HR',
    'description': """
                   Flexi HR provides a complete solution for services related to Human Resources and it's relevant perspectives.
                 """,
    'summary': 'Manage Employee Loan, payroll, recruitment processes, employee contracts, employee attendance, employee timesheet, mass leave allocation and leave management, business trip request.',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'price': 0.00,
    'currency': 'EUR',
    'images': [
        'static/description/main_screenshot.png',
    ],
    'depends': ['base', 'stock', 'account',
                'hr_payroll', 'hr', 'hr_attendance',
                'hr_contract', 'hr_recruitment', 'project', 'hr_timesheet','hr_expense'
                ],
    'images': ['static/description/main_screenshot.png'],
    'data': [
        
        'hr_payroll/hr_payroll_data.xml',
        'hr_payroll/hr_payroll_view.xml',
        'loan/report/report.xml',
        'loan/data/loan_data.xml',
        'loan/views/loan_type_view.xml',
        'loan/views/loan_application_view.xml',
        'loan/wizard/loan_calc_view.xml',
        'loan/views/loan_setting_view.xml',
        'loan/wizard/wizard_loan_reject_view.xml',
        'loan/report/report_loan_summary.xml',
        'loan/report/report_loan_contract.xml',
        'loan/views/loan_prepayment_view.xml',
        'loan/views/loan_advance_payment_view.xml',
        'loan/views/loan_adjustment_view.xml',
        'loan/data/mail_template_view.xml',
        'loan/security/loan_security.xml',

        # Employee Checklist
        'checklist/views/checklist_setting_view.xml',
        'checklist/wizard/product_allocation_wiz_view.xml',
        'checklist/views/employee_document_view.xml',
        'checklist/views/employee_product_line_view.xml',
        'checklist/views/employee_entry_view.xml',
        'checklist/wizard/entry_product_wiz_view.xml',
        'checklist/views/employee_exit_view.xml',
        'checklist/wizard/disburse_amt_wiz_view.xml',
        'checklist/wizard/reason_cancel_view.xml',
        'checklist/wizard/exit_review_view.xml',
        'checklist/views/hr_employee_view.xml',
        'checklist/views/employee_checklist_data.xml',
        'checklist/views/stock_picking_view.xml',
        'checklist/views/employee_checklist_template.xml',
        
        
        # HR Recruitment
        'hr_recruitment/hr_recruitment_view.xml',
        'hr_recruitment/create_employee_view.xml',
        'calendar/calendar_views.xml',
        
        # overtime
#         'overtime/views/hr_employee_view.xml',
#         'overtime/views/account_analytic_line_view.xml',
        
        # Event
        'event/views/event_data.xml',
        'event/views/employee_event_track_view.xml',
        'event/views/employee_event_participant_view.xml',
        'event/views/employee_event_view.xml',
        'event/wizard/employee_event_attendance_view.xml',
        'event/views/hr_employee_view.xml',
        'event/wizard/wizard_employee_event_view.xml',
        'event/views/ir_cron_data.xml',
        
        # Advance Salary Request
        'advance_salary/views/advance_salary_setting_view.xml',
        'advance_salary/views/report.xml',
        'advance_salary/views/hr_adv_salary_req_data.xml',
        'advance_salary/views/hr_adv_salary_req_view.xml',
        'advance_salary/views/hr_employee_view.xml',
        'advance_salary/views/account_move_view.xml',
        'advance_salary/views/reject_reason_view.xml',
        'advance_salary/views/advance_salary_req_template.xml',
        'advance_salary/views/disburse_amt_wiz_view.xml',
        'advance_salary/views/summary_wiz_view.xml',
        'advance_salary/views/template_summary_wiz.xml',
        'advance_salary/security/security_view.xml',
        'advance_salary/security/ir.model.access.csv',
        
        #Leave
#         'leaves/data/leave_data.xml',
        'leaves/views/hr_public_holiday_view.xml',
        'leaves/views/weekly_off_group_view.xml',
        'leaves/views/leave_setting_view.xml',
        'leaves/views/hr_holidays_view.xml',
        'leaves/wizard/mass_leave_application.xml',
        'leaves/views/hr_employee_view.xml',
#         'leaves/wizard/leave_mass_allocation_view.xml',

        # attendance
        'attendance/res_config_view.xml',

        # Dynamic Payslip
        'dynamic_payslip/views/wizard_dynamic_payslip_view.xml',
        'dynamic_payslip/payslip_reports.xml', 
        'dynamic_payslip/security/ir.model.access.csv',
        'dynamic_payslip/views/dynamic_payslip_report.xml',
        'dynamic_payslip/data/design_data.xml',

        #leave encashment
        'leave_encash/security/leave_security.xml',
        'leave_encash/views/hr_job_views.xml',
        'leave_encash/wizard/leave_encash_process_views.xml',
        'leave_encash/views/leave_config_setting_views.xml',
        'leave_encash/views/leave_encash_views.xml',
        'leave_encash/views/hr_payroll_views.xml',
        'leave_encash/views/hr_payroll_data.xml',
        'leave_encash/views/report.xml',
        'leave_encash/wizard/leave_encash_report_wizard.xml',
        'leave_encash/report/leave_encash_report.xml',
        'leave_encash/security/ir.model.access.csv',
        'security/ir.model.access.csv',
        
        # Penalty
        
         'hr_penalty/views/penalty_config_setting_view.xml',
         'hr_penalty/views/hr_employee_view.xml',
         'hr_penalty/views/hr_payroll_data.xml',
         'hr_penalty/views/hr_payroll_view.xml',
         
        #overtime

        'hr_overtime/security/security_view.xml',
        'hr_overtime/data/overtime_schedular.xml',
        'hr_overtime/data/hr_employee_overtime_data.xml',
        'hr_overtime/data/payroll_data.xml',
        'hr_overtime/views/hr_employee_views.xml',
        'hr_overtime/views/res_config_views.xml',
        'hr_overtime/views/hr_employee_overtime_views.xml',
        'hr_overtime/views/hr_payslip_views.xml', 

        #travel request
        "employee_travel_request/security/aspl_hr_travel_security.xml",
        "employee_travel_request/security/ir.model.access.csv",
        "employee_travel_request/data/aspl_hr_travel_sequences.xml",
        "employee_travel_request/data/aspl_hr_travel_mail_templates.xml",
        "employee_travel_request/views/res_config_settings_views.xml",
        "employee_travel_request/views/hr_employee_view.xml",
        "employee_travel_request/views/emp_grade_expense_view.xml",
        "employee_travel_request/views/emp_grade_view.xml",
        "employee_travel_request/views/emp_travel_request_view.xml",
        "employee_travel_request/views/employee_proposed_expenses_view.xml",
        "employee_travel_request/views/emp_travel_place_view.xml",
        "employee_travel_request/views/emp_multi_currency_view.xml",
        "employee_travel_request/views/menu_views.xml",
        "employee_travel_request/wizard/hr_travel_reason_wizard.xml",

        #performance evaluation rating
        'performance_evaluation_rating/security/security.xml',
        'performance_evaluation_rating/security/ir.model.access.csv',
        'performance_evaluation_rating/views/res_config_setting.xml',
        'performance_evaluation_rating/views/kra_template.xml',
        'performance_evaluation_rating/views/kra_schedule_plan.xml',
        'performance_evaluation_rating/views/kra_evaluation.xml',
        'performance_evaluation_rating/wizard/kra_wizard.xml',
        'performance_evaluation_rating/report/report.xml',
        'performance_evaluation_rating/report/kra_evaluation_report.xml',
        'performance_evaluation_rating/report/kra_analysis_report.xml',

    ],
    'demo': [
        'data/flexi_hr_demo.xml'
    ],
    'external_dependencies': {
        'python': [
            'numpy'
        ],
    },
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
