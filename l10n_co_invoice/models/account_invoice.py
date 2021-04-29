# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

# Inherit
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _description = "income third party"

    add_third = fields.Boolean(string='Activar ingreso para tercero',states={'draft': [('readonly', False)]})

    invoice_third_line_ids = fields.One2many('account.invoice.third.line', 'invoice_id', string='Invoice Third Lines',
                                             states={'draft': [('readonly', False)]}, copy=False)

    amount_third = fields.Monetary(string='Total Tercero',store=True, readonly=True, compute='_compute_amount',
                                   track_visibility='always', copy=False)

    amount_third_signed = fields.Monetary(string=u'Monto terceros moneda compañia',
                                            currency_field='company_currency_id',
                                            store=True, readonly=True, compute='_compute_amount', copy=False)

    amount_general = fields.Monetary(string='TOTAL COMPROBANTE',store=True, readonly=True, compute='_compute_amount',
                                     copy=False)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'date','invoice_third_line_ids.amount')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for inv in self:
            if inv.add_third:
                amount_third = sum(line.amount for line in self.invoice_third_line_ids)
                amount_third_signed = amount_third
                if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
                    currency_id = self.currency_id
                    rate_date = self._get_currency_rate_date() or fields.Date.today()
                    amount_third_signed = currency_id._convert(self.amount_third, self.company_id.currency_id, self.company_id, rate_date)

                self.amount_third = amount_third
                self.amount_third_signed = amount_third_signed

                self.amount_general = self.amount_third + self.amount_total

    # @api.one
    # @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
    #              'currency_id', 'company_id', 'date_invoice', 'type', 'date', 'invoice_third_line_ids.amount')
    # def _compute_amount(self):
    #     round_curr = self.currency_id.round
    #     self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
    #     self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
    #
    #     '''SE AÑADE A LA SUMA CAMPO AMOUNT_THIRD INDIVIDUAL'''
    #     amount_third = sum(line.amount for line in self.invoice_third_line_ids)
    #     self.amount_third = amount_third or 0.0
    #     self.amount_third_signed = amount_third_signed = self.amount_third
    #     # self.amount_total = self.amount_untaxed + self.amount_tax
    #
    #     '''SE AÑADE A LA SUMA AMOUNT_THIRD AL TOTAL'''
    #     self.amount_total = self.amount_untaxed + self.amount_tax + self.amount_third
    #     amount_total_company_signed = self.amount_total
    #     amount_untaxed_signed = self.amount_untaxed
    #     if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
    #         currency_id = self.currency_id
    #         rate_date = self._get_currency_rate_date() or fields.Date.today()
    #         amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
    #                                                            self.company_id, rate_date)
    #         amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
    #                                                      self.company_id, rate_date)
    #
    #         amount_third_signed = currency_id._convert(self.amount_third, self.company_id.currency_id,
    #                                                    self.company_id, rate_date)  # ADD THIRD
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     self.amount_third_signed = amount_third_signed * sign  # ADD THIRD
    #     self.amount_total_company_signed = amount_total_company_signed * sign
    #     self.amount_total_signed = self.amount_total * sign
    #     self.amount_untaxed_signed = amount_untaxed_signed * sign

    def _get_aml_for_amount_residual(self):
        """ Get the aml to consider to compute the amount residual of invoices """
        self.ensure_one()
        if self.add_third:
            line_o = self.sudo().move_id.line_ids.filtered(lambda l: l.account_id == self.account_id)

            def get_account_ids(account_id):
                #lines = [(0, 0, None)]
                for line in self.invoice_third_line_ids:
                    if account_id == line.account_debit_id:
                        return line.account_debit_id
            line_third = self.sudo().move_id.line_ids.filtered(lambda t: t.account_id == get_account_ids(t.account_id))
            lines_r = line_o + line_third
            return lines_r

        else:
            return self.sudo().move_id.line_ids.filtered(lambda l: l.account_id == self.account_id)

    def move_line_third_get(self):
        res = []
        for line in self.invoice_third_line_ids:
            company_currency = self.company_id.currency_id
            if self.currency_id != company_currency:
                rate_date = self._get_currency_rate_date() or fields.Date.today()
                amount_currency = self.currency_id._convert(line.amount,company_currency, self.company_id,rate_date)
            else:
                amount_currency = False
            move_line_debit_dict = {
                'name': 'Ingreso tercero / ' + line.name,
                'amount_currency': line.amount if amount_currency!=False else 0.0,
                'currency_id': self.currency_id.id if amount_currency!=False else False,
                'debit': amount_currency if amount_currency!=False else line.amount,
                'credit': 0.0,
                'partner_id': self.partner_id.id,
                'account_id': line.account_debit_id.id,
                'move_id': line.invoice_id.move_id.id,
                'invoice_id': line.invoice_id.id
            }
            res.append(move_line_debit_dict)
            move_line_credit_dict = {
                'name': 'Ingreso tercero',
                'amount_currency': - line.amount if amount_currency!=False else 0.0,
                'currency_id': self.currency_id.id if amount_currency!=False else False,
                'debit': 0.0,
                'credit': amount_currency if amount_currency!=False else line.amount,
                'partner_id': self.partner_id.id,
                'account_id': line.account_credit_id.id,
                'move_id': line.invoice_id.move_id.id
            }
            res.append(move_line_credit_dict)

        self.env['account.move.line'].create(res)

    @api.multi
    def invoice_validate(self):
        r = super(AccountInvoice, self).invoice_validate()
        self.move_line_third_get()
        return r


class AccountInvoiceThirdLine(models.Model):
    _name = "account.invoice.third.line"
    _description = "Invoice Line Third"
    _order = "invoice_id,sequence,id"

    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference',
                                 ondelete='cascade', index=True)

    sequence = fields.Integer(default=10,help="Secuencia")
    product_id = fields.Many2one('product.product', string='Concepto',index=True)
    name = fields.Text(string=u'Descripción', required=True)
    account_credit_id = fields.Many2one('account.account', string='Cuenta',
                                  states={'draft': [('readonly', False)]},required=True)
    account_debit_id = fields.Many2one('account.account', string=u'Cuenta Débito')
    company_id = fields.Many2one('res.company', string='Company',related='invoice_id.company_id', store=True, readonly=True, related_sudo=False)
    company_currency_id = fields.Many2one('res.currency', related='invoice_id.company_currency_id', readonly=True, related_sudo=False)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id',string='Moneda',store=True, related_sudo=False, readonly=False)
    amount = fields.Monetary(string='Monto',store=True,required=True)
    amount_signed = fields.Monetary(string=u'Monto Compañia', currency_field='company_currency_id',
                                            store=True, readonly=True, compute='_compute_amount_third')
    #aditional
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Adicionales")

    @api.one
    @api.depends('amount','product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_amount_third(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        amount_signed = self.amount
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            amount_signed = currency._convert(self.amount, self.invoice_id.company_id.currency_id,
                                                      self.company_id or self.env.user.company_id,
                                                      date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_signed = amount_signed * sign

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.name = self.product_id.name or '/'
        self.account_credit_id = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if self.product_id:
            if self.account_credit_id.type_third_parties=='customer':
                account_debit_id = self.account_credit_id.account_debit_id
                if not account_debit_id:
                    raise UserError(_('Estimado usuario: Activó ingreso para tercero pero, no asignó una cuenta débito.'))
                else:
                    self.account_debit_id = account_debit_id
            else:
                raise UserError(_('Estimado usuario: No activó ingreso para tercero y tampoco una cuenta débito.'))

