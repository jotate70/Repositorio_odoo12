# -*- coding: utf-8 -*-
{
    'name': "l10n_co_invoice",

    'summary': """
        Facturas Terceros""",

    'description': """
        Modulo que agrega la funcion de ingresos para terceros
    """,
    'author': "Jhonny Merino Samillán, Chiclayo-Perú",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['account','base','account','account_standard_report'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_view.xml',
        'views/account_invoice_third_views.xml',
        'report/invoice_customer_third_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
            ],
}