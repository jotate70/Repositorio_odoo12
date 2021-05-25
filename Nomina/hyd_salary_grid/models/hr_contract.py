# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrContract(models.Model):

    _inherit = 'hr.contract'

    grille_salaire = fields.Many2one(
        string='Grille salariale',
        readonly=False,
        required=False,
        help="grille salariale de ce contrat",
        comodel_name='hyd_salary_grid.grille_salaire',
        track_visibility='onchange')

    @api.onchange('type_id')
    def onchange_type_id(self):
        domain = []
        if self.type_id:
            grilles_ids = self.type_id.grilles_salaire.mapped('id')
            domain = [('id', 'in', grilles_ids)]
        return {'domain': {'grille_salaire': domain}}

    @api.onchange("grille_salaire")
    def onchange_grille_salaire(self):
        self.wage = self.grille_salaire.montant

    @api.multi
    def unlink(self):
        grilles = self.mapped('grille_salaire')
        res = super(HrContract, self).unlink()
        grilles.update_masse()
        return res

    @api.multi
    def update_salary(self):
        for record in self:
            if record.grille_salaire:
                record.wage = record.grille_salaire.montant

    @api.constrains('grille_salaire', 'wage')
    def check_update_masse(self):
        for record in self:
            if record.grille_salaire:
                record.grille_salaire.update_masse()
