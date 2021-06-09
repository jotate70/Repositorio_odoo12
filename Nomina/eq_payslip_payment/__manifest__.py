# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Payslip Payment",
    'category': 'Payroll',
    'version': '12.0.1.0',
    'author': 'Equick ERP',
    'description': """ This module allows you to do payslip payment. """,
    'summary': """Payslip Payment | Payroll Payment | employee payslip payment | employee payroll payment | employee payment | payslip payment register. | payroll payment register.""",
    'depends': ['base', 'hr_payroll_account'],
    'price': 18,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'views/emp_payslip_payment_view.xml',
        'views/hr_payslip_view.xml'
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: