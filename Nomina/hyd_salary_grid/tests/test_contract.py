# -*- coding: utf-8 -*-
from odoo.tests import common
# from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TestContract(common.TransactionCase):

    post_install = True

    def setUp(self):

        super(TestContract, self).setUp()

        self.type_contrat = self.env.ref(
            "hr_contract.hr_contract_type_emp")

        # creer un echellon
        self.echellon = self.env["hyd_salary_grid.echelon_salariale"].create(
            {'name': '10', 'code': '10', 'num_ordre': 10})

        # creer une categorie
        self.categorie = self.env[
            "hyd_salary_grid.categorie_salariale"].create(
            {'name': 'A', 'code': 'A', 'num_ordre': 1})

        # TODO: creer une grille salariale
        self.grille = self.env["hyd_salary_grid.grille_salaire"].create({
            'types_contrat': (4, False, self.type_contrat.id),
            'name': "grille test",
            'code': "A10",
            'montant': 200000,
            'categ_id': self.categorie.id,
            'ech_id': self.echellon.id,
            'num_ordre': 11,
            })

        # TODO: CREATE an employee
        self.employee = self.env["hr.employee"].create({'name': "TOTO TEST"})

    @common.post_install(True)
    def test_creer_contrat(self):
        """Teste la creation d'un contrat."""
        self.assertEqual("done", "done")

        # create a new contract
        contrat = self.env["hr.contract"].new({
            'name': "C000004",
            'employee_id': self.employee.id,
            'type_id': self.type_contrat.id,
            'grille_salaire': self.grille.id,
            'struct_id': self.env.ref("hr_payroll.structure_base").id})
        contrat.onchange_grille_salaire()
        self.assertEqual(contrat.grille_salaire.montant, 200000)
        self.assertEqual(contrat.wage, 200000)

        contrat = self.env["hr.contract"].create({
            'name': "C000004",
            'employee_id': self.employee.id,
            'type_id': self.type_contrat.id,
            'grille_salaire': self.grille.id,
            'struct_id': self.env.ref("hr_payroll.structure_base").id,
            'wage': self.grille.montant})
        self.assertIsNotNone(contrat)
        self.assertEqual(self.grille.masse, 200000)
        contrat.unlink()
        self.assertEqual(self.grille.masse, 0)
