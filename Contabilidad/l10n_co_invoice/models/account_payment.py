
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

MAP_ACCOUNT_TYPE_PARTNER_TYPE = {
    'receivable': 'customer',
    'payable': 'supplier',
}

class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'

    @api.model
    def default_get(self, fields):
        #self.ensure_one()
        # Añadir una línea adicional para default get
        rec = models.Model.default_get(self, fields)
        #rec = super(AccountPaymentGroup, self).default_get(fields)
        to_pay_move_line_ids = self._context.get('to_pay_move_line_ids')
        to_pay_move_lines = self.env['account.move.line'].browse(
            to_pay_move_line_ids).filtered(lambda x: (
                x.account_id.reconcile and
                x.account_id.internal_type in ('receivable', 'payable')))
        if to_pay_move_lines:
            partner = to_pay_move_lines.mapped('partner_id')
            if len(partner) != 1:
                raise ValidationError(_(
                    'You can not send to pay lines from different partners'))

            internal_type = to_pay_move_lines.mapped(
                'account_id.internal_type')

            if len(internal_type) != 1:
                third_active = to_pay_move_lines.mapped('invoice_id.add_third')[0]
                if third_active:
                    pass
                else:
                    raise ValidationError(_(
                        'You can not send to pay lines from different partners'))
            rec['partner_id'] = self._context.get(
                'default_partner_id', partner[0].id)
            rec['partner_type'] = MAP_ACCOUNT_TYPE_PARTNER_TYPE[
                internal_type[0]]
            # rec['currency_id'] = invoice['currency_id'][0]
            # rec['payment_type'] = (
            #     internal_type[0] == 'receivable' and
            #     'inbound' or 'outbound')
            rec['to_pay_move_line_ids'] = [(6, False, to_pay_move_line_ids)]
        return rec

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.multi
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        """
        If we are paying a payment gorup with paylines, we use account
        of lines that are going to be paid
        """
        for rec in self:
            to_pay_account = rec.payment_group_id.to_pay_move_line_ids.mapped(
                'account_id')
            # if len(to_pay_account) > 1:
            #     raise ValidationError(_(
            #         'To Pay Lines must be of the same account!'))
            # elif len(to_pay_account) == 1:
            #     rec.destination_account_id = to_pay_account[0]
            if len(to_pay_account) >= 1:
                rec.destination_account_id = to_pay_account[0]
            else:
                super(AccountPayment, rec)._compute_destination_account_id()

    # def get_lines(self,invoices,amount):
    #     lines = None
    #     for inv in invoices:
    #         if inv.type in ('out_invoice','out_refund'):
    #             lines = inv.move_id.line_ids.filtered(lambda x : x.account_id in ('receivable'))
    #
    #     if lines:
    #

    def _create_payment_entry_third(self,amount):
        # self.get_lines(self.invoice_ids,amount)
        counter_aml = []

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        lines = self.invoice_ids.move_id.line_ids.filtered(lambda x: x.account_id.internal_type in ('receivable'))
        move = self.env['account.move'].create(self._get_move_vals())

        d, c, ac, c_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id,
                                                           self.company_id.currency_id)

        t = c
        for l in lines:
            if l.balance > 0:
                debit_line, credit_line, amount_currency_line, currency_id_line = aml_obj.with_context(
                    date=self.payment_date)._compute_amount_fields(-l.balance, l.currency_id,
                                                              self.company_id.currency_id)
                t_o = t
                t = t - credit_line
                if t >=0.0:
                    amount_paid = - credit_line
                else:
                    amount_paid = - abs(t_o)

                debit, credit, amount_currency, currency_id = aml_obj.with_context(
                    date=self.payment_date)._compute_amount_fields(amount_paid, l.currency_id,
                                                                   self.company_id.currency_id)
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id,False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml_dict.update({'account_id': l.account_id.id})
                counterpart_aml_dict.update({'name': l.name})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)

                #AÑADO ESTA LISTA PARA UNA POSIBLE VERIFICACIÓN DE CUADRE
                counter_aml.append(counterpart_aml)

                if t<0.0:
                    break
        # Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(abs(amount), 0.0, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        return move

    @api.multi
    def post(self):
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            if rec.invoice_ids.type in ('out_invoice') and rec.invoice_ids.add_third==True:
                move = rec._create_payment_entry_third(amount) #CREAR LIENAS DE ENTRADAS PARA TERCEROS
            else:
                move = rec._create_payment_entry(amount)
            persist_move_name = move.name

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
                persist_move_name += self._get_move_name_transfer_separator() + transfer_debit_aml.move_id.name

            rec.write({'state': 'posted', 'move_name': persist_move_name})
        return True