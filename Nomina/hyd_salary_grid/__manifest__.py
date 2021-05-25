# -*- coding: utf-8 -*-
{
    'name': "Payroll: salary grid in the contract",

    'summary': "Add salary grid in the contract",

    'description': """ Register all the salary grid of your enterprise """
                   """ and set inside the salary of contract form the """
                   """ salary using his grid. By the way update all """
                   """ salary of employee by modifying the grid. """,

    'author': "HyD Freelance",
    'website': "http://",
    'category': 'Generic Modules/Human Resources',
    'version': '12.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_contract', 'hr_payroll'],

    # always loaded
    'data': [
            # data
            # views
            "views/menu.xml",
            "views/hr_contract_type_views.xml",
            "views/hr_contract_views.xml",
            "views/categorie_salariale_views.xml",
            "views/echelon_salariale_views.xml",
            "views/grille_salaire_views.xml",

            # workflow
            # security
            "security/ir.model.access.csv",
            # reports
            ],

    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'price': 0,
    'currency': 'EUR',
    'images': ['static/images/main_screenshot.png']
}
