# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import _, models 
from odoo.tools import float_is_zero


class TrialBalanceXslx(models.AbstractModel):
    _name = 'report.a_f_r.report_trial_balance_xlsx'
    _inherit = 'report.account_financial_report.abstract_report_xlsx'

    def _get_report_name(self, report):
        report_name = _('Trial Balance')
        return self._get_report_complete_name(report, report_name)

    def _get_report_columns(self, report):
        if not report.show_partner_details:
            res = {
                0: {'header': _('Code'), 'field': 'code', 'width': 20},
                1: {'header': _('Account'), 'field': 'name', 'width': 70},
                2: {'header': _('Initial balance'),
                    'field': 'initial_balance',
                    'type': 'amount',
                    'width': 20},
                3: {'header': _('Debit'),
                    'field': 'debit',
                    'type': 'amount',
                    'width': 20},
                4: {'header': _('Credit'),
                    'field': 'credit',
                    'type': 'amount',
                    'width': 20},
                5: {'header': _('Period balance'),
                    'field': 'period_balance',
                    'type': 'amount',
                    'width': 20},
                6: {'header': _('Ending balance'),
                    'field': 'final_balance',
                    'type': 'amount',
                    'width': 20},
            }
            if report.foreign_currency:
                foreign_currency = {
                    7: {'header': _('Cur.'),
                        'field': 'currency_id',
                        'field_currency_balance': 'currency_id',
                        'type': 'many2one', 'width': 7},
                    8: {'header': _('Initial balance'),
                        'field': 'initial_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 20},
                    9: {'header': _('Ending balance'),
                        'field': 'final_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 20},
                }
                res = {**res, **foreign_currency}
            return res
        else:
            res = {
                0: {'header': _('Code'), 'field': 'code', 'width': 20},
                1: {'header': _('Partner'), 'field': 'name', 'width': 70},
                2: {'header': _('Initial balance'),
                    'field': 'initial_balance',
                    'type': 'amount',
                    'width': 20},
                3: {'header': _('Debit'),
                    'field': 'debit',
                    'type': 'amount',
                    'width': 20},
                4: {'header': _('Credit'),
                    'field': 'credit',
                    'type': 'amount',
                    'width': 20},
                5: {'header': _('Period balance'),
                    'field': 'period_balance',
                    'type': 'amount',
                    'width': 20},
                6: {'header': _('Ending balance'),
                    'field': 'final_balance',
                    'type': 'amount',
                    'width': 20},
            }
            if report.foreign_currency:
                foreign_currency = {
                    7: {'header': _('Cur.'),
                        'field': 'currency_id',
                        'field_currency_balance': 'currency_id',
                        'type': 'many2one', 'width': 7},
                    8: {'header': _('Initial balance'),
                        'field': 'initial_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 20},
                    9: {'header': _('Ending balance'),
                        'field': 'final_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 20},
                }
                res = {**res, **foreign_currency}
            return res

    def _get_report_filters(self, report):
        return [
            [_('Date range filter'),
             _('From: %s To: %s') % (report.date_from, report.date_to)],
            [_('Target moves filter'),
             _('All posted entries') if report.only_posted_moves else _(
                 'All entries')],
            [_('Account at 0 filter'),
             _('Hide') if report.hide_account_at_0 else _('Show')],
            [_('Show foreign currency'),
             _('Yes') if report.foreign_currency else _('No')],
            [_('Limit hierarchy levels'),
             _('Level %s' % report.show_hierarchy_level) if
             report.limit_hierarchy_level else _('No limit')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _generate_report_content(self, workbook, report):
        Utilidad_suma = 0
        Utilidad_resta = 0
        Utilidad = 0

        self.write_array_header()

        # For each account
        for account in report.account_ids.filtered(lambda a: not a.hide_line):
            # Total compute
            if account.code == '1':
                initial_balance = account.initial_balance
                debit = account.debit
                credit = account.credit
                period_balance = account.period_balance 
                final_balance = account.final_balance
            elif account.code == '2':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
            elif account.code == '3':
                initial_balance = initial_balance + account.initial_balance                      
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
            elif account.code == '4':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
                Utilidad_suma = abs(account.final_balance)
            elif account.code == '5':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
                Utilidad_resta = abs(account.final_balance)
            elif account.code == '6':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
                Utilidad_resta = Utilidad_resta + abs(account.final_balance)
            elif account.code == '7':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
                Utilidad_resta = Utilidad_resta + abs(account.final_balance)
            elif account.code == '8':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
            elif account.code == '9':
                initial_balance = initial_balance + account.initial_balance  
                debit = debit + account.debit
                credit = credit + account.credit
                period_balance = period_balance + account.period_balance 
                final_balance = final_balance + account.final_balance
            # Print trial balance
            if not report.show_partner_details:
                # Display account lines
                self.write_line(account, 'account')
            # Print trial balance details
            else:

                # Display account lines
                self.write_line(account, 'account')
                # For each partner
                for partner in account.partner_ids:
                    partner.code = account.code         # Agrega el codigo de subcuenta al tercero
                    # Display partner lines
                    self.write_line(partner, 'partner')

        # Total p
        account.code = ''
        account.name = 'TOTAL'
        account.initial_balance = initial_balance
        account.debit = debit
        account.credit = credit
        account.period_balance = period_balance
        account.final_balance = final_balance
        # printf total trial balance
        self.write_account_footer(account, 
                                            account.name + '' + ':' )           
        # Utilidad
        Utilidad = Utilidad_suma-Utilidad_resta
        partner.code = ''
        partner.name = 'UTILIDAD'
        partner.initial_balance = ''
        partner.debit = ''
        partner.credit = ''
        partner.period_balance = ''
        partner.final_balance = Utilidad
        # printf total trial balance
        self.write_account_footer(partner, 
                                            partner.name + '' + ':' )

    def write_line(self, line_object, type_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        if type_object == 'partner':
            line_object.currency_id = line_object.report_account_id.currency_id
        elif type_object == 'account':
            line_object.currency_id = line_object.currency_id
        super(TrialBalanceXslx, self).write_line(line_object)

    def write_account_footer(self, account, name_value):
        """Specific function to write account footer for Trial Balance"""
        format_amt = self._get_currency_amt_header_format(account)
        for col_pos, column in self.columns.items():
            if column['field'] == 'name':
                value = name_value
            else:
                value = getattr(account, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '',
                                        self.format_header_left)
            elif cell_type == 'amount':
                self.sheet.write_number(self.row_pos, col_pos, float(value),
                                        self.format_header_amount)
            elif cell_type == 'many2one':
                self.sheet.write_string(
                    self.row_pos, col_pos, value.name or '',
                    self.format_header_right)
            elif cell_type == 'amount_currency' and account.currency_id:
                self.sheet.write_number(
                    self.row_pos, col_pos, float(value),
                    format_amt)
            else:
                self.sheet.write_string(
                    self.row_pos, col_pos, '',
                    self.format_header_right)
        self.row_pos += 1
