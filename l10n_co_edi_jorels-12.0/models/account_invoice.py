# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2020)
#
# This file is part of l10n_co_edi_jorels.
#
# l10n_co_edi_jorels is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# l10n_co_edi_jorels is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_jorels.  If not, see <https://www.gnu.org/licenses/>.
#
# email: info@jorels.com
#

import base64

from odoo import api, fields, models, tools

from odoo.exceptions import Warning

import json
import requests

import qrcode
from io import BytesIO

import zipfile, tempfile
from pathlib import Path

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _description = "Facturación electrónica"

    state = fields.Selection(selection_add=[('validate', 'Validando DIAN')])

    ei_number = fields.Char(string="Número", copy=False)
    ei_type_document_id = fields.Many2one(comodel_name='l10n_co_edi_jorels.type_documents', string="Tipo de documento",
                                          copy=False)
    ei_customer = fields.Text(string="customer json", copy=False)
    ei_legal_monetary_totals = fields.Text(string="legal_monetary_totals json", copy=False)
    ei_invoice_lines = fields.Text(string="invoice_lines json", copy=False)

    # Permiten almacenar modo sincrono y de produccion usados al facturar
    ei_sync = fields.Boolean(string="Sync", default=False, copy=False)
    ei_is_not_test = fields.Boolean(string="En producción", default=False, copy=False)

    # API Response:
    ei_is_valid = fields.Boolean(string="Valido", copy=False)
    ei_uuid = fields.Char(string="UUID", copy=False)
    ei_issue_date = fields.Date(string="Fecha del tramite", copy=False)
    ei_zip_key = fields.Char(string="Llave del archivo zip", copy=False)
    ei_status_code = fields.Char(string="Codigo del estado", copy=False)
    ei_status_description = fields.Char(string="Descripcion del estado", copy=False)
    ei_status_message = fields.Char(string="Mensaje del estado", copy=False)
    ei_xml_file_name = fields.Char(string="Nombre del archivo xml", copy=False)
    ei_zip_name = fields.Char(string="Nombre del archivo", copy=False)
    ei_url_acceptance = fields.Char(string="URL de aprobacion", copy=False)
    ei_url_rejection = fields.Char(string="URL de rechazo", copy=False)
    ei_xml_bytes = fields.Boolean(string="XML Bytes", copy=False)
    ei_errors_messages = fields.Text("Mensajes", copy=False)
    ei_qr_data = fields.Text(string="Datos del qr", copy=False)
    ei_application_response_base64_bytes = fields.Binary("Respuesta de la aplicacion", attachment=True, copy=False)
    ei_attached_document_base64_bytes = fields.Binary("Documento adjunto", attachment=True, copy=False)
    ei_pdf_base64_bytes = fields.Binary('Documento PDF', attachment=True, copy=False)
    ei_zip_base64_bytes = fields.Binary('Documento ZIP', attachment=True, copy=False)
    ei_dian_response_base64_bytes = fields.Binary('Respuesta de la DIAN', attachment=True, copy=False)

    ei_attached_zip_base64_bytes = fields.Binary('Zip adjunto', attachment=True, copy=False)

    # QR image
    ei_qr_image = fields.Binary("QR Code", attachment=True, copy=False)

    # Total de impuestos solo/sin retenciones
    ei_amount_tax_withholding = fields.Monetary("Retenciones", compute="_compute_amount", store=True)
    ei_amount_tax_no_withholding = fields.Monetary("Impuestos sin retenciones", compute="_compute_amount", store=True)
    ei_amount_total_no_withholding = fields.Monetary("Total sin retenciones", compute="_compute_amount", store=True)

    def action_invoice_sent(self):
        self.ensure_one()
        action = super().action_invoice_sent()

        # Por compatibilidad con registros ya creados anteriormente sin este campo
        if self.ei_is_valid and not self.ei_attached_zip_base64_bytes:
            self.ei_attached_zip_base64_bytes = self.compute_ei_attached_zip_base64_bytes()

        if self.ei_is_not_test and self.ei_attached_zip_base64_bytes:
            action['context']['attach_ei_zip_file'] = True

        return action

    def _generate_email_attachment(self, filename, file_string):
        self.ensure_one()

        attachments = self.env['ir.attachment']

        if self.type in ('out_invoice', 'out_refund') and self.state in ('open', 'paid'):
            return attachments.with_context({}).create({
                'name': filename,
                'res_model': str(self._name),
                'res_id': self.id,
                'datas': file_string,
                'datas_fname': filename,
                'type': 'binary',
            })

        return attachments

    @api.multi
    def write_response(self, json_response):
        try:
            json_request = json.loads(json.dumps(json_response))

            for rec in self:
                rec.ei_is_valid = json_request['is_valid']
                rec.ei_uuid = json_request['uuid']
                rec.ei_issue_date = json_request['issue_date']
                rec.ei_zip_key = json_request['zip_key']
                rec.ei_status_code = json_request['status_code']
                rec.ei_status_description = json_request['status_description']
                rec.ei_status_message = json_request['status_message']
                rec.ei_xml_file_name = json_request['xml_file_name']
                rec.ei_zip_name = json_request['zip_name']
                rec.ei_url_acceptance = json_request['url_acceptance']
                rec.ei_url_rejection = json_request['url_rejection']
                rec.ei_xml_bytes = json_request['xml_bytes']
                rec.ei_errors_messages = str(json_request['errors_messages'])
                rec.ei_qr_data = json_request['qr_data']
                rec.ei_application_response_base64_bytes = json_request['application_response_base64_bytes']
                rec.ei_attached_document_base64_bytes = json_request['attached_document_base64_bytes']
                rec.ei_pdf_base64_bytes = json_request['pdf_base64_bytes']
                rec.ei_zip_base64_bytes = json_request['zip_base64_bytes']
                rec.ei_dian_response_base64_bytes = json_request['dian_response_base64_bytes']

                if rec.ei_is_valid:
                    try:
                        rec.ei_attached_zip_base64_bytes = self.compute_ei_attached_zip_base64_bytes()
                    except Exception as e:
                        _logger.debug("No ha podido crear el adjunto zip: %s", e)

                # QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=2,
                    border=2,
                )
                qr.add_data(self.ei_qr_data)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.ei_qr_image = qr_image
        except Exception as e:
            _logger.debug("Write response: %s", e)
            raise Warning("Write response: %s" % e)

    @api.multi
    def get_ei_number(self):
        for rec in self:
            rec.ei_number = ''.join([i for i in rec.number if i.isdigit()])
            return int(rec.ei_number)

    @api.multi
    def get_type_document_identification_id(self):
        for rec in self:
            document_type = rec.partner_id.l10n_co_document_type
            if document_type:
                values = {
                    'civil_registration': 1,
                    'id_card': 2,
                    'id_document': 3,
                    'national_citizen_id': 3,
                    'residence_document': 4,
                    'foreign_id_card': 5,
                    'rut': 6,
                    'passport': 7,
                    'external_id': 8,
                    'diplomatic_card': 0,
                }
                document_type_id = values[document_type]
                if 1 <= document_type_id <= 8:
                    return document_type_id
            else:
                return False

    @api.multi
    def get_ei_customer(self):
        for rec in self:
            type_document_identification_id = self.get_type_document_identification_id()
            if type_document_identification_id:
                if rec.partner_id.vat:
                    identification_number_general = ''.join([i for i in rec.partner_id.vat if i.isdigit()])

                    # Si es Nit elimina el digito de verificación
                    if type_document_identification_id == 6:
                        identification_number = identification_number_general[:-1]
                    else:
                        identification_number = identification_number_general

                    if identification_number:
                        name = rec.partner_id.name
                        if rec.partner_id.email_edi:
                            email_edi = str(rec.partner_id.email_edi)
                        else:
                            raise Warning("El cliente debe tener un correo electrónico donde enviar la factura.\n"
                                          "Agreguelo e intente nuevamente.")

                        if rec.partner_id.is_company:
                            type_organization_id = 1
                        else:
                            type_organization_id = 2

                        customer_data = {
                            "type_document_identification_id": type_document_identification_id,
                            "identification_number": identification_number,
                            "type_organization_id": type_organization_id,
                            "name": name,
                            "email": email_edi,
                            # Por ahora no se ha incluido este campo en el modulo de contactos
                            # Así que dejamos por defecto "No tiene"
                            "merchant_registration": 'No tiene'
                        }

                        if rec.partner_id.municipality_id:
                            customer_data['municipality_id'] = rec.partner_id.municipality_id.id
                        else:
                            raise Warning("Debe asignarle al cliente una municipalidad")

                        if rec.partner_id.type_regime_id:
                            customer_data['type_regime_id'] = rec.partner_id.type_regime_id.id
                        else:
                            raise Warning("Debe asignarle al cliente un tipo de regimen")

                        if rec.partner_id.type_liability_id:
                            customer_data['type_liability_id'] = rec.partner_id.type_liability_id.id
                        else:
                            raise Warning("Debe asignarle al cliente un tipo de responsabilidad")

                        return customer_data
                else:
                    raise Warning(
                        "El cliente no tiene un número de documento de identificación, agregelo e intente nuevamente.")
            else:
                raise Warning(
                    "El cliente no tiene asociado un tipo de documento de identificación, agregelo e intente nuevamente.")
        return False

    @api.multi
    def get_ei_legal_monetary_totals(self):
        for rec in self:
            line_extension_amount = rec.amount_untaxed
            tax_exclusive_amount = rec.amount_untaxed
            tax_inclusive_amount = rec.ei_amount_total_no_withholding
            allowance_total_amount = 0.0
            charge_total_amount = 0.0
            payable_amount = tax_inclusive_amount

        return {
            "line_extension_amount": line_extension_amount,
            "tax_exclusive_amount": tax_exclusive_amount,
            "tax_inclusive_amount": tax_inclusive_amount,
            "allowance_total_amount": allowance_total_amount,
            "charge_total_amount": charge_total_amount,
            "payable_amount": payable_amount
        }

    @api.multi
    def get_ei_lines(self):

        lines = []

        for rec in self:
            for invoice_line_id in rec.invoice_line_ids:
                if invoice_line_id.account_id:
                    price_unit = invoice_line_id.price_unit
                    # el diccionario temporal de elementos que pertenecen a la linea especifica
                    invoice_temps = {}
                    products = {}
                    allowance_charges = {}
                    tax_totals = {'tax_totals': []}
                    products.update({'price_amount': price_unit})
                    products.update({'base_quantity': 1.000000})

                    if invoice_line_id.product_id.code:
                        products.update({'code': invoice_line_id.product_id.code})
                    else:
                        raise Warning("Todos los productos deben tener asignada una 'Referencia interna'.\n"
                                      "Revise, por favor.")

                    products.update({'description': invoice_line_id.name})

                    if invoice_line_id.product_id.edi_unit_measure_id.id:
                        products.update({'unit_measure_id': invoice_line_id.product_id.edi_unit_measure_id.id}),
                    else:
                        raise Warning("Todos los productos deben tener asignada una 'Unidad de medida (DIAN)'.\n"
                                      "Revise, por favor.")

                    products.update({'invoiced_quantity': invoice_line_id.quantity})
                    products.update({'line_extension_amount': invoice_line_id.price_subtotal})
                    # [4]: Estándar de adopción del contribuyente ('999')
                    products.update({'type_item_identification_id': 4})
                    # ALLOWANCE_CHARGES_CONFIGURATION
                    discount = False
                    # descargos
                    if invoice_line_id.discount:
                        discount = True
                        products.update({'free_of_charge_indicator': False})
                        products.update({'reference_price_id': 3})  # Otro valor ('03')
                        allowance_charges.update({'charge_indicator': False})
                        amount = (invoice_line_id.discount / 100.0) * (
                                invoice_line_id.quantity * invoice_line_id.price_unit)
                        base_amount = invoice_line_id.discount
                        allowance_charge_reason = "Discount"
                    else:
                        discount = False
                        products.update({'free_of_charge_indicator': False})
                        products.update({'reference_price_id': 1})  # Valor comercial ('01')
                        allowance_charges.update({'charge_indicator': False})
                        amount = 0
                        base_amount = 0
                        allowance_charge_reason = ""

                    allowance_charges.update({'base_amount': base_amount})
                    allowance_charges.update({'amount': amount})
                    allowance_charges.update({'allowance_charge_reason': allowance_charge_reason})

                    taxable_amount = invoice_line_id.price_subtotal
                    # total_line_price = price_unit * invoice_line_id.quantity

                    for invoice_line_tax_id in invoice_line_id.invoice_line_tax_ids:  # itercion_para_obtener_los_impuestos
                        tax_total = {}

                        if invoice_line_tax_id.edi_tax_id.id:
                            edi_tax_name = invoice_line_tax_id.edi_tax_id.name
                            tax_name = invoice_line_tax_id.name
                            # La informacion enviada a la DIAN no debe incluir las retefuentes
                            if edi_tax_name[:4] != 'Rete' and tax_name != 'IVA Excluido':
                                tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                                tax_total.update({'tax_amount': (taxable_amount * invoice_line_tax_id.amount) / 100.0})
                                tax_total.update({'taxable_amount': taxable_amount})
                                tax_total.update({'percent': invoice_line_tax_id.amount})
                                tax_totals['tax_totals'].append(tax_total)
                        else:
                            raise Warning("Todos los impuestos deben tener asignado un 'Tipo de impuesto (DIAN)'.\n"
                                          "Revise por favor e intente nuevamente")

                    # en esta parte concateno los elementos del json
                    # ACTUALIZA TODOS LOS ELEMENTOS DEL PRODUCTO
                    invoice_temps.update(products)

                    # ACTUALIZA TODOS LOS DESCUENTOS DEL PRODUCTO (*SE SUPONE UNO SOLO*)
                    if discount:
                        invoice_temps.update({'allowance_charges': [allowance_charges]})

                    # los impuestos se adjuntan dentro de este json
                    if tax_totals['tax_totals']:
                        invoice_temps.update({'tax_totals': tax_totals['tax_totals']})

                    lines.append(invoice_temps)

        return lines
        # [
        #     {
        #         "unit_measure_id": 642,
        #         "invoiced_quantity": 1.000000,
        #         "line_extension_amount": 500000.00,
        #         "free_of_charge_indicator": False,
        #         "allowance_charges": [
        #             {
        #                 "charge_indicator": False,
        #                 "allowance_charge_reason": "Discount",
        #                 "amount": 0.00,
        #                 "base_amount": 0.00
        #             }
        #         ],
        #         "tax_totals": [
        #             {
        #                 "tax_id": 15,
        #                 "tax_amount": 0.00,
        #                 "taxable_amount": 500000.00,
        #                 "percent": 0.00
        #             }
        #         ],
        #         "description": "Envio de Caja",
        #         "code": "1002004",
        #         "type_item_identification_id": 3,
        #         "price_amount": 500000.00,
        #         "base_quantity": 1.000000
        #     }
        # ]

    # Calculo de las retenciones
    @api.one
    def _compute_amount(self):
        res = super(AccountInvoice, self)._compute_amount()

        amount_tax_withholding = 0
        amount_tax_no_withholding = 0
        for tax_line_id in self.tax_line_ids:
            if tax_line_id.tax_id.edi_tax_id:
                edi_tax_name = tax_line_id.tax_id.edi_tax_id.name
                if edi_tax_name[:4] != 'Rete':
                    amount_tax_no_withholding = amount_tax_no_withholding + tax_line_id.amount_total
                else:
                    amount_tax_withholding = amount_tax_withholding + tax_line_id.amount_total
            else:
                tax_name = tax_line_id.tax_id.name
                if tax_name[:3] != 'Rte':
                    amount_tax_no_withholding = amount_tax_no_withholding + tax_line_id.amount_total
                else:
                    amount_tax_withholding = amount_tax_withholding + tax_line_id.amount_total

        self.ei_amount_tax_withholding = amount_tax_withholding
        self.ei_amount_tax_no_withholding = amount_tax_no_withholding
        self.ei_amount_total_no_withholding = self.amount_untaxed + amount_tax_no_withholding
        return res

    @api.multi
    def get_ei_type_document_id(self):
        for rec in self:
            type_documents_env = self.env['l10n_co_edi_jorels.type_documents']
            # Por ahora el tipo de documento siempre es "Facturacion electronica" (Codigo '01')
            # Nota debito (Código '92')
            # O Nota credito (Código '91')
            # La factura de exportacion, contingencia y otros quedan pendientes de revisar
            type_edi_document = self.get_type_edi_document()
            if type_edi_document != 'none':
                if type_edi_document == 'invoice':
                    # Factura de venta
                    type_documents_rec = type_documents_env.search([('code', '=', '01')])
                elif type_edi_document == 'credit-note':
                    # Nota credito
                    type_documents_rec = type_documents_env.search([('code', '=', '91')])
                elif type_edi_document == 'debit-note':
                    # Nota debito
                    type_documents_rec = type_documents_env.search([('code', '=', '92')])
            else:
                raise Warning("Este tipo de documento no necesita ser enviado a la DIAN")

            rec.ei_type_document_id = type_documents_rec.id

            return rec.ei_type_document_id.id

    @api.multi
    def get_ei_sync(self):
        for rec in self:
            rec.ei_sync = rec.ei_is_not_test
            return rec.ei_sync

    @api.multi
    def get_ei_is_not_test(self):
        for rec in self:
            return rec.ei_is_not_test

    @api.multi
    def get_ei_resolution_id(self):
        resolution_id = 0
        for rec in self:
            type_edi_document = self.get_type_edi_document()
            if type_edi_document != 'none':
                if type_edi_document == 'invoice' and rec.journal_id.sequence_id.resolution_id:
                    # Factura de venta
                    resolution_id = rec.journal_id.sequence_id.resolution_id.resolution_id
                elif type_edi_document == 'credit-note' and rec.journal_id.refund_sequence_id.resolution_id:
                    # Nota credito
                    resolution_id = rec.journal_id.refund_sequence_id.resolution_id.resolution_id
                elif type_edi_document == 'debit-note' and rec.journal_id.debitnote_sequence_id.resolution_id:
                    # Nota debito
                    resolution_id = rec.journal_id.debitnote_sequence_id.resolution_id.resolution_id
                else:
                    raise Warning("Este tipo de documento no tiene asignada una resolucion DIAN")
            else:
                raise Warning("Este tipo de documento no necesita ser enviado a la DIAN")

        return resolution_id

    @api.multi
    def get_json_request(self):
        for rec in self:
            # Si es factura de venta o Nota credito o Nota debito.
            if rec.type == 'out_invoice' or rec.type == 'out_refund':
                json_request = {
                    'number': self.get_ei_number(),
                    'type_document_id': self.get_ei_type_document_id(),
                    'resolution_id': self.get_ei_resolution_id(),
                    'sync': self.get_ei_sync(),
                    'customer': self.get_ei_customer(),
                }

                # Fecha de vencimiento
                if rec.date_due:
                    json_request['due_date'] = fields.Date.to_string(rec.date_due)

                # Compatibilidad con multimonedas
                if rec.currency_id and rec.company_id and rec.currency_id != rec.company_id.currency_id:
                    company_currency_code = rec.company_id.currency_id.name
                    invoice_currency_code = rec.currency_id.name

                    type_currencies_env = self.env['l10n_co_edi_jorels.type_currencies']
                    company_currency_search = type_currencies_env.search([('code', '=', company_currency_code)])
                    invoice_currency_search = type_currencies_env.search([('code', '=', invoice_currency_code)])

                    # El if es para asegurarse que el name en currency_id,
                    # tenga una correspondencia en el code en type_currencies de la DIAN
                    if company_currency_search and invoice_currency_search:

                        # El inverso de Odoo,
                        # pues por ejemplo para company=COP y invoice=USD,
                        # la taza debe ser USD->COP, no COP->USD como viene por defecto
                        # Esto puede originar errores de redondeo que hay que revisar en mayor detalle.
                        #
                        # Por ejemplo existe un modulo de OCA que permite usar tazas inversas y evitar estos problemas,
                        # pero se encontró que podria causar conflictos en el calculo automatico de los precios.
                        #
                        # Por ahora se revisa si existe un hipotetico campo booleano rate_inverted, como seria
                        # el caso del modulo de OCA; aunque no se considera una verdadera solución al problema.
                        # Lo mejor seria 'quizas' elevar la precision del campo 'rate' de modo que incluso en una
                        # inversion el valor se mantenga dentro del margen esperado.
                        if hasattr(rec.currency_id, 'rate_inverted') and rec.currency_id.rate_inverted:
                            calculation_rate = rec.currency_id.rate
                        else:
                            calculation_rate = 1.0 / rec.currency_id.rate

                        rate_date = self._get_currency_rate_date() or fields.Date.context_today(self)

                        json_request['type_currency_id'] = invoice_currency_search.id
                        json_request['payment_exchange_rate'] = {
                            'type_currency_id': company_currency_search.id,
                            'calculation_rate': calculation_rate,
                            'date': str(rate_date)
                        }
                    else:
                        raise Warning("Un tipo de moneda en Odoo no corresponde con ningun tipo de moneda DIAN")

                # json_request y billing_reference
                billing_reference = False
                type_edi_document = self.get_type_edi_document()
                if type_edi_document != 'none':
                    if type_edi_document == 'invoice':
                        # Factura de venta
                        json_request['legal_monetary_totals'] = self.get_ei_legal_monetary_totals()
                        json_request['invoice_lines'] = self.get_ei_lines()
                    elif type_edi_document == 'credit-note':
                        # Nota credito
                        json_request['legal_monetary_totals'] = self.get_ei_legal_monetary_totals()
                        json_request['credit_note_lines'] = self.get_ei_lines()
                        billing_reference = True
                    elif type_edi_document == 'debit-note':
                        # Nota debito
                        json_request['requested_monetary_totals'] = self.get_ei_legal_monetary_totals()
                        json_request['debit_note_lines'] = self.get_ei_lines()
                        billing_reference = True
                else:
                    raise Warning("Este tipo de documento no necesita ser enviado a la DIAN")

                # Billing reference
                if billing_reference:
                    invoice_env = self.env['account.invoice']
                    invoice_rec = invoice_env.search([('number', '=', rec.origin)])
                    if invoice_rec.ei_uuid:
                        json_request["billing_reference"] = {
                            "number": invoice_rec.number,
                            "uuid": invoice_rec.ei_uuid,
                            "issue_date": fields.Date.to_string(invoice_rec.ei_issue_date)
                        }
                    else:
                        raise Warning("La factura de referencia aun no ha sido validada ante la DIAN")
            else:
                raise Warning("Este tipo de documento no necesita ser enviado a la DIAN")

        return json_request

    # API Response with sync=true:
    #            {'is_valid': True, 'number': 'XXXXxxxxxxxxx',
    #            'uuid': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    #            'issue_date': 'xxxx-xx-xx', 'zip_key': '', 'status_code': '00',
    #            'status_description': 'Procesado Correctamente.',
    #            'status_message': 'La Factura electrónica XXXXxxxxxxxxx, ha sido autorizada.',
    #            'xml_file_name': 'xxxxxxxxxxxxxxxx', 'zip_name': 'xxxxxxxxxxxxxxxxxxx.zip',
    #            'url_acceptance': None, 'url_rejection': None, 'xml_bytes': 'true', 'errors_messages': [[]],
    #            'qr_data': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'application_response_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'attached_document_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'pdf_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'zip_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'dian_response_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'}

    # API Response with sync=false:
    #            {'is_valid': None, 'number': 'XXXXxxxxxxx',
    #            'uuid': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    #            'issue_date': 'xxxx-xx-xx', 'zip_key': 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx', 'status_code': None,
    #            'status_description': '', 'status_message': '', 'xml_file_name': '',
    #            'zip_name': 'xxxxxxxxxxxxx.zip', 'url_acceptance': None, 'url_rejection': None,
    #            'xml_bytes': '', 'errors_messages': ['true'],
    #            'qr_data': 'xxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'application_response_base64_bytes': '', 'attached_document_base64_bytes': None,
    #            'pdf_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'zip_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...',
    #            'dian_response_base64_bytes': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'}

    # Json sended:
    # {
    #     "number": "xxxxxxxxxxxxxx",
    #     "type_document_id": 1,
    #     "sync": true,
    #     "send": true,
    #     "customer": {
    #         "type_document_identification_id": 6,
    #         "identification_number": "xxxxxxxxx",
    #         "name": "Cliente de prueba",
    #         "email": "cliente@example.com",
    #         "merchant_registration": "No tiene"
    #     },
    #     "legal_monetary_totals": {
    #         "line_extension_amount": 500000.0,
    #         "tax_exclusive_amount": 500000.0,
    #         "tax_inclusive_amount": 500000.0,
    #         "allowance_total_amount": 0.0,
    #         "charge_total_amount": 0.0,
    #         "payable_amount": 500000.0
    #     },
    #     "invoice_lines": [
    #         {
    #             "unit_measure_id": 642,
    #             "invoiced_quantity": 1.0,
    #             "line_extension_amount": 500000.0,
    #             "free_of_charge_indicator": false,
    #             "allowance_charges": [
    #                 {
    #                     "charge_indicator": false,
    #                     "allowance_charge_reason": "Discount",
    #                     "amount": 0.0,
    #                     "base_amount": 0.0
    #                 }
    #             ],
    #             "tax_totals": [
    #                 {
    #                     "tax_id": 15,
    #                     "tax_amount": 0.0,
    #                     "taxable_amount": 500000.0,
    #                     "percent": 0.0
    #                 }
    #             ],
    #             "description": "Envio de Caja",
    #             "code": "1002004",
    #             "type_item_identification_id": 3,
    #             "price_amount": 500000.0,
    #             "base_quantity": 1.0
    #         }
    #     ]
    # }

    # TO DO:
    # Se puede hacer más eficiente haciendo que se llame a esta funcion una menor cantidad de veces,
    # cuando se procesa la factura electronica. Lo ideal es que sea una sola vez
    @api.multi
    def get_type_edi_document(self):
        type_edi_document = 'none'
        for rec in self:
            if rec.type == 'out_invoice':
                if rec.origin:
                    if rec.debit_invoice_id:
                        # Nota debito
                        type_edi_document = 'debit-note'
                    else:
                        # Factura de venta
                        type_edi_document = 'invoice'
                # Factura de venta
                else:
                    type_edi_document = 'invoice'
            elif rec.type == 'out_refund':
                # Nota credito
                type_edi_document = 'credit-note'
        return type_edi_document

    @api.multi
    def validate_dian_generic(self, is_test):
        # raise Warning(json.dumps(self.get_json_request(), indent=2, sort_keys=False))
        # _logger.debug("Request Validación DIAN: %s", json.dumps(self.get_json_request(), indent=2, sort_keys=False))

        for rec in self:
            try:
                type_edi_document = self.get_type_edi_document()
                if type_edi_document != 'none':
                    requests_data = self.get_json_request()

                    if self.env.user.company_id.api_key:
                        token = self.env.user.company_id.api_key
                    else:
                        raise Warning("Debe configurar un token para poder facturar electrónicamente")

                    if self.env.user.company_id.api_url:
                        api_url = self.env.user.company_id.api_url
                    else:
                        raise Warning("No ha configurado una URL API para la facturación electrónica")

                    header = {"accept": "application/json", "Content-Type": "application/json"}

                    api_url = api_url + "/api/ubl2.1/" + type_edi_document

                    if is_test or not rec.ei_is_not_test:
                        if self.env.user.company_id.test_set_id:
                            test_set_id = self.env.user.company_id.test_set_id
                            api_url = api_url + '/' + test_set_id
                        else:
                            raise Warning("No ha configurado un 'TestSetId'. "
                                          "Sin este no puede hacer pruebas para habilitación.")

                    _logger.debug('API URL: %s', api_url)

                    header.update({'Authorization': 'Bearer ' + token})
                    response = requests.post(api_url, json.dumps(requests_data), headers=header).json()
                    _logger.debug('API Response: %s', response)

                    if 'message' in response:
                        if response['message'] == 'Unauthenticated.' or response['message'] == '':
                            raise Warning("Error de autenticación con la API de facturación electrónica. "
                                          "Verifique que sus credenciales sean validas")
                        else:
                            if 'errors' in response:
                                raise Warning(response['message'] + '/ errors: ' + str(response['errors']))
                            else:
                                raise Warning(response['message'])
                    elif 'is_valid' in response:
                        self.write_response(response)
                        if response['is_valid']:
                            self.env.user.notify_success(message="La validación ante la DIAN ha sido exitosa.")
                        elif 'uuid' in response:
                            if response['uuid'] != "":
                                if not rec.ei_is_not_test:
                                    self.env.user.notify_success(message="Documento enviado a la DIAN en habilitación.")
                                else:
                                    temp_message = {self.ei_status_message, self.ei_errors_messages,
                                                    self.ei_status_description, self.ei_status_code}
                                    raise Warning(str(temp_message))
                            else:
                                raise Warning('No se ha obtenido un UUID valido. Intente nuevamente.')
                        else:
                            raise Warning('No se ha podido validar el documento ante la DIAN.')
                    else:
                        raise Warning("No se ha obtenido una respuesta logica por parte de la API")
                else:
                    raise Warning("Este tipo de documento no necesita ser enviado  la DIAN")
            except Exception as e:
                _logger.debug("Error al procesar la solicitud: %s", e)
                raise Warning("Error al procesar la solicitud: %s" % e)

    @api.multi
    def validate_dian(self):
        self.validate_dian_generic(False)
        self.write({'state': 'open'})

    @api.multi
    def validate_dian_test(self):
        self.validate_dian_generic(True)
        self.write({'state': 'open'})

    @api.multi
    def skip_validate_dian(self):
        for rec in self:
            rec.write({'state': 'open'})
            self.env.user.notify_warning(message="Se ha saltado el proceso de validación.")

    @api.multi
    def skip_validate_dian_production(self):
        self.skip_validate_dian()

    @api.multi
    def action_invoice_open(self):
        previous_invoice_state_is_draft = False
        if self.filtered(lambda inv: inv.state == 'draft'):
            previous_invoice_state_is_draft = True

        res = super(AccountInvoice, self).action_invoice_open()

        if previous_invoice_state_is_draft:
            to_open_invoices = self.filtered(lambda inv: inv.state == 'open')
            if to_open_invoices.filtered(lambda inv: inv.type in ('out_invoice', 'out_refund')):
                # Entorno
                to_open_invoices.filtered(
                    lambda inv: inv.write({'ei_is_not_test': inv.env.user.company_id.is_not_test}))

                # Entrar en estado intermedio de validación,
                # si la opción está habilitada en la configuración
                if to_open_invoices.filtered(lambda inv: inv.env.user.company_id.enable_validate_state):
                    return to_open_invoices.filtered(lambda inv: inv.write({'state': 'validate'}))

                if to_open_invoices.filtered(lambda inv: inv.ei_is_not_test):
                    to_open_invoices.validate_dian_generic(False)
                if to_open_invoices.filtered(lambda inv: not inv.ei_is_not_test):
                    to_open_invoices.validate_dian_generic(True)

                return to_open_invoices.filtered(lambda inv: inv.write({'state': 'open'}))

            to_paid_invoices = self.filtered(lambda inv: inv.state == 'paid')
            if to_paid_invoices:
                raise Warning('Revise su factura nuevamente. ¿Está facturando algo realmente?')

        return res

    @api.multi
    def compute_ei_attached_zip_base64_bytes(self):
        self.ensure_one()

        if self.ei_uuid:
            pdf_name = self.ei_uuid + '.pdf'
            pdf_path = Path(tempfile.gettempdir()) / pdf_name

            xml_name = self.ei_uuid + '.xml'
            xml_path = Path(tempfile.gettempdir()) / xml_name

            zip_name = self.ei_uuid + '.zip'
            zip_path = Path(tempfile.gettempdir()) / zip_name

            zip_archive = zipfile.ZipFile(zip_path, "w")

            if self.ei_pdf_base64_bytes:
                pdf_handle = open(pdf_path, "wb")
                pdf_handle.write(base64.decodebytes(self.ei_pdf_base64_bytes))
                pdf_handle.close()
                zip_archive.write(pdf_path, arcname=pdf_name)

            if self.ei_attached_document_base64_bytes:
                xml_handle = open(xml_path, "wb")
                xml_handle.write(base64.decodebytes(self.ei_attached_document_base64_bytes))
                xml_handle.close()
                zip_archive.write(xml_path, arcname=xml_name)

            zip_archive.close()

            if self.ei_pdf_base64_bytes or self.ei_attached_document_base64_bytes:
                with open(zip_path, "rb") as f:
                    attached_zip = f.read()
                    return base64.encodebytes(attached_zip)

        return False

    @api.multi
    def status_document(self):
        for rec in self:
            try:
                type_edi_document = self.get_type_edi_document()
                if type_edi_document != 'none':
                    if rec.ei_uuid:
                        requests_data = {"refresh_pdf": True}

                        if self.env.user.company_id.api_key:
                            token = self.env.user.company_id.api_key
                        else:
                            raise Warning("Debe configurar un token para poder facturar electrónicamente")

                        if self.env.user.company_id.api_url:
                            api_url = self.env.user.company_id.api_url
                        else:
                            raise Warning("No ha configurado una URL API para la facturación electrónica")

                        header = {"accept": "application/json", "Content-Type": "application/json"}

                        api_url = api_url + "/api/ubl2.1/status/document/" + rec.ei_uuid

                        _logger.debug('API URL: %s', api_url)

                        header.update({'Authorization': 'Bearer ' + token})
                        response = requests.post(api_url, json.dumps(requests_data), headers=header).json()
                        _logger.debug('API Response: %s', response)

                        if 'message' in response:
                            if response['message'] == 'Unauthenticated.' or response['message'] == '':
                                raise Warning("Error de autenticación con la API de facturación electrónica. "
                                              "Verifique que sus credenciales sean validas")
                            else:
                                if 'errors' in response:
                                    raise Warning(response['message'] + '/ errors: ' + str(response['errors']))
                                else:
                                    raise Warning(response['message'])
                        elif 'is_valid' in response:
                            self.write_response(response)
                            if response['is_valid']:
                                self.env.user.notify_info(message="La validación ante la DIAN ha sido exitosa.")
                            elif 'uuid' in response:
                                if response['uuid'] != "":
                                    if not rec.ei_is_not_test:
                                        self.env.user.notify_info(
                                            message="Documento enviado a la DIAN en habilitación.")
                                    else:
                                        temp_message = {self.ei_status_message, self.ei_errors_messages,
                                                        self.ei_status_description, self.ei_status_code}
                                        raise Warning(str(temp_message))
                                else:
                                    raise Warning('No se ha obtenido un UUID valido. Intente nuevamente.')
                            else:
                                raise Warning('No se ha podido validar el documento ante la DIAN.')
                        else:
                            raise Warning("No se ha obtenido una respuesta logica por parte de la API")
                    else:
                        raise Warning("Se necesita un UUID para verificar el estado del documento.")
                else:
                    raise Warning("Este tipo de documento no necesita ser enviado  la DIAN")
            except Exception as e:
                _logger.debug("Error al procesar la solicitud: %s", e)
                raise Warning("Error al procesar la solicitud: %s" % e)
