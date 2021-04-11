# -*- coding: utf-8 -*-
#
# Jorels S.A.S. - Copyright (2019-2021)
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

import json
import logging
from pathlib import Path

import requests
from odoo import api, fields, models
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Api key
    api_key = fields.Char(related="company_id.api_key", string="Api key", readonly=False)
    api_url = fields.Char(related="company_id.api_url", string="Api url", readonly=False,
                          default='https://lion-consulting.apifacturacionelectronica.xyz')

    # Software
    software_id = fields.Char(related="company_id.software_id", string="Software Id", readonly=False)
    software_pin = fields.Char(related="company_id.software_pin", string="Pin", readonly=False)
    software_message = fields.Char(related="company_id.software_message", string="Estado software", readonly=False)

    # Company Signature
    certificate_certificate = fields.Binary(related="company_id.certificate_certificate", string="Firma Digital",
                                            readonly=False)
    certificate_password = fields.Char(related="company_id.certificate_password", string="Contraseña", readonly=False)
    certificate_message = fields.Char(related="company_id.certificate_message", string="Estado certificado",
                                      readonly=False)

    # Test
    is_not_test = fields.Boolean(related="company_id.is_not_test", string="Entorno de producción", default=False,
                                 readonly=False)
    test_set_id = fields.Char(related="company_id.test_set_id", string="TestSetId", readonly=False)
    enable_validate_state = fields.Boolean(related="company_id.enable_validate_state",
                                           string="Estado internedio Validación DIAN",
                                           default=True, readonly=False)
    enable_mass_send_print = fields.Boolean(related="company_id.enable_mass_send_print",
                                            string="Email automatico de la factura al validar(En producción)",
                                            default=False, readonly=False)

    # Report
    report_custom_text = fields.Html(related="company_id.report_custom_text", string="Custom text", readonly=False)

    # Consulta de software
    @api.multi
    def button_get_software(self):
        for rec in self:
            try:
                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/software"
                header.update({'Authorization': 'Bearer' + ' ' + token})
                response = requests.get(api_url, headers=header).json()
                _logger.debug('API Response: %s', response)

                if 'id' in response:
                    if rec.software_id == response['identifier'] and rec.software_pin == response['pin']:
                        rec.software_message = "¡Genial, la información coincide con la API!"
                    else:
                        rec.software_message = "Lo siento, la información no coincide con la API. " \
                                               "¡Intente nuevamente!"
                elif 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        rec.software_message = 'No es posible la autenticación con la API. ' \
                                               'Revise su Api key e intente nuevamente.'
                    else:
                        rec.software_message = response['message']
                else:
                    rec.software_message = 'Algo sucede. No es posible comunicarse con la API'
            except Exception as e:
                rec.software_message = "¡Error de conexión con la API!"
                _logger.debug("Error de conexión: %s", e)
        rec.env.user.notify_info(message=rec.software_message)
        # rec.env.user.notify_success(message=rec.software_message)
        # self.env.user.notify_danger(message='My danger message')
        # self.env.user.notify_info(message='My information message')
        # self.env.user.notify_default(message='My default message')

        # Example success response:
        # {
        #     'id': 3,
        #     'identifier': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        #     'pin': 'xxxxxxxx',
        #     'url': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
        #     'deleted_at': None,
        #     'created_at': '2020-02-28T23:58:47.000000Z',
        #     'updated_at': '2020-02-28T23:58:47.000000Z'
        # }

    # Actualización del software
    @api.multi
    def button_put_software(self):
        try:
            for rec in self:
                api_file_path = Path(__file__).parents[2] / 'static' / 'api.json'
                with open(api_file_path) as api_file:
                    requests_data = json.loads(api_file.read())
                requests_data['software']['id'] = rec.software_id
                requests_data['software']['pin'] = rec.software_pin

                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/software"
                header.update({'Authorization': 'Bearer' + ' ' + token})
                response = requests.put(api_url, json.dumps(requests_data['software']), headers=header).json()
                _logger.debug('API Response: %s', response)

                if 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        rec.software_message = 'No es posible la autenticación con la API. ' \
                                               'Revise su Api key e intente nuevamente.'
                    else:
                        rec.software_message = response['message']
                else:
                    rec.software_message = 'Algo sucede. No es posible comunicarse con la API'
        except Exception as e:
            rec.software_message = "¡Error de conexión con la API!"
            _logger.debug("Error de conexión: %s", e)
        rec.env.user.notify_info(message=rec.software_message)
        # Example success response
        # {
        #     'message': 'Software creado con éxito',
        #     'software': {'identifier': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        #                  'pin': xxxxxxxx,
        #                  'url': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
        #                  'updated_at': '2020-04-30T06:53:54.000000Z',
        #                  'created_at': '2020-04-30T06:53:54.000000Z',
        #                  'id': 6
        #                  }
        # }

    # Consulta de certificado
    @api.multi
    def button_get_certificate(self):
        try:
            for rec in self:
                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/certificate"
                header.update({'Authorization': 'Bearer' + ' ' + token})
                response = requests.get(api_url, headers=header).json()
                _logger.debug('API Response: %s', response)

                # No es posible comprobar la firma digital, ni el password
                if 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        rec.certificate_message = 'No es posible la autenticación con la API. ' \
                                                  'Revise su Api key e intente nuevamente.'
                    else:
                        rec.certificate_message = response['message']
                elif 'is_valid' in response:
                    if response['is_valid']:
                        if 'organization' in response:
                            rec.certificate_message = "Certificado valido para la empresa: " + response['organization']
                        else:
                            rec.certificate_message = "Certificado valido en servidor"
                    else:
                        rec.certificate_message = "No se ha encontrado un certificado. " \
                                                  "¡Suba uno o Intente nuevamente!"
                else:
                    rec.certificate_message = 'Algo sucede. No es posible comunicarse con la API'

        except Exception as e:
            rec.certificate_message = "¡Error de conexión con la API!"
            _logger.debug("Error de conexión: %s", e)
        rec.env.user.notify_info(message=rec.certificate_message)
        # Example success response:
        # {
        #     'id': 1,
        #     'name': 'xxxxxxxxxx.p12',
        #     'password': 'xxxxxxxx',
        #     'deleted_at': None,
        #     'created_at': '2020-03-01T03:45:08.000000Z',
        #     'updated_at': '2020-04-19T20:40:41.000000Z'
        # }

    # Actualización de certificado
    @api.multi
    def button_put_certificate(self):
        try:
            for rec in self:
                api_file_path = Path(__file__).parents[2] / 'static' / 'api.json'
                with open(api_file_path) as api_file:
                    requests_data = json.loads(api_file.read())
                _logger.error('Certificado: %s', str(rec.certificate_certificate)[2:][:-1])

                requests_data['firma']['certificate'] = str(rec.certificate_certificate)[2:][:-1]
                requests_data['firma']['password'] = rec.certificate_password

                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/certificate"
                header.update({'Authorization': 'Bearer' + ' ' + token})
                response = requests.put(api_url, json.dumps(requests_data['firma']), headers=header).json()
                _logger.debug('API Response: %s', response)

                if 'message' in response:
                    if response['message'] == 'Unauthenticated.' or response['message'] == '':
                        rec.certificate_message = 'No es posible la autenticación con la API. ' \
                                                  'Revise su Api key e intente nuevamente.'
                    else:
                        rec.certificate_message = response['message']
                else:
                    rec.certificate_message = 'Algo sucede. No es posible comunicarse con la API'
        except Exception as e:
            rec.certificate_message = "¡Error de conexión con la API!"
            _logger.debug("Error de conexión: %s", e)
        rec.env.user.notify_info(message=rec.certificate_message)
        # Example success response
        # {
        #     'message': 'Certificado creado con éxito', 
        #     'certificado': {
        #         'name': 'xxxxxxxxxx.p12',
        #         'password': 'xxxxxxxx',
        #         'updated_at': '2020-05-01T22:56:14.000000Z',
        #         'created_at': '2020-05-01T22:56:14.000000Z',
        #         'id': 2
        #     }
        # }

    # Consulta de resoluciones
    @api.multi
    def button_get_resolutions(self):
        try:
            for rec in self:
                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/resolutions"
                header.update({'Authorization': 'Bearer' + ' ' + token})
                response = requests.get(api_url, headers=header).json()
                _logger.debug('API Response: %s', response)
        except Exception as e:
            _logger.debug("Error de conexión: %s", e)
        # Example success response
        # [
        #     {
        #         'id': 1,
        #         'type_document_id': 1,
        #         'prefix': 'XXXX',
        #         'resolution': 'xxxxxxxx',
        #         'resolution_date': 'xxxx-xx-xx',
        #         'technical_key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        #         'from': xxxxxxxxx,
        #         'to': xxxxxxxxx,
        #         'date_from': 'xxxx-xx-xx',
        #         'date_to': 'xxxx-xx-xx',
        #         'deleted_at': None,
        #         'created_at': '2020-03-03T23:45:08.000000Z',
        #         'updated_at': '2020-03-03T23:45:08.000000Z',
        #         'number': xxxxxxxxx,
        #         'next_consecutive': 'XXXXxxxxxxxx'
        #     },
        #     {
        #         'id': 2,
        #         'type_document_id': 1,
        #         'prefix': 'XXXX',
        #         'resolution': 'xxxxxxxxx',
        #         'resolution_date': 'xxxx-xx-xx',
        #         'technical_key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        #         'from': xxxxxxxxx,
        #         'to': xxxxxxxxx,
        #         'date_from': 'xxxx-xx-xx',
        #         'date_to': 'xxxx-xx-xx',
        #         'deleted_at': None,
        #         'created_at': '2020-05-02T02:28:08.000000Z',
        #         'updated_at': '2020-05-02T02:28:08.000000Z',
        #         'number': xxxxxxxxxxx,
        #         'next_consecutive': 'XXXXxxxxxxx'
        #     }
        # ]

    # Update resolutions on Odoo database
    @api.model
    def action_update_resolutions(self):
        try:
            token = str(self.env.user.company_id.api_key)
            api_url = str(self.env.user.company_id.api_url)

            header = {"accept": "application/json", "Content-Type": "application/json"}
            api_url = api_url + "/api/ubl2.1/config/resolutions"
            header.update({'Authorization': 'Bearer' + ' ' + token})
            response = requests.get(api_url, headers=header).json()
            _logger.debug('API Response: %s', response)

            if 'message' in response:
                if response['message'] == 'Unauthenticated.' or response['message'] == '':
                    raise Warning('No es posible la autenticación con la API. ' \
                                  'Revise su Api key e intente nuevamente.')
                else:
                    raise Warning(response['message'])
            else:
                # First delete resolutions on database
                # self._cr.execute("""DELETE FROM l10n_co_edi_jorels_resolution""")

                # Now create new resolutions
                for resolution in response:
                    if resolution['resolution_date']:
                        if int(resolution['resolution_date'].split('-')[0]) < 2000:
                            resolution['resolution_date'] = "'2000-01-01'"
                        else:
                            resolution['resolution_date'] = "'" + resolution['resolution_date'] + "'"
                    else:
                        resolution['resolution_date'] = 'NULL'

                    if resolution['date_from']:
                        if int(resolution['date_from'].split('-')[0]) < 2000:
                            resolution['date_from'] = "'2000-01-01'"
                        else:
                            resolution['date_from'] = "'" + resolution['date_from'] + "'"
                    else:
                        resolution['date_from'] = 'NULL'

                    if resolution['date_to']:
                        if int(resolution['date_to'].split('-')[0]) < 2000:
                            resolution['date_to'] = "'2000-01-01'"
                        else:
                            resolution['date_to'] = "'" + resolution['date_to'] + "'"
                    else:
                        resolution['date_to'] = 'NULL'

                    # Sincronizando Odoo con la API
                    resolution_search = self.env['l10n_co_edi_jorels.resolution'].search(
                        [('resolution_id', '=', resolution['id'])])

                    # TO DO: Actualizar con UPDATE si ya existe
                    # Si no está ya en la base de datos, entonces la agrega
                    if not resolution_search:
                        self._cr.execute(
                            "INSERT INTO l10n_co_edi_jorels_resolution (" \
                            "resolution_api_sync," \
                            "resolution_type_document_id," \
                            "resolution_prefix," \
                            "resolution_resolution," \
                            "resolution_resolution_date," \
                            "resolution_technical_key," \
                            "resolution_from," \
                            "resolution_to," \
                            "resolution_date_from," \
                            "resolution_date_to," \
                            "resolution_id," \
                            "resolution_number," \
                            "resolution_next_consecutive," \
                            "create_uid," \
                            "create_date," \
                            "write_uid," \
                            "write_date" \
                            ") VALUES (TRUE, %d, '%s', NULLIF('%s','None'), %s, NULLIF('%s','None'), %d, %d, %s, %s, %d, %d, '%s', %d, %s, %d, %s)" %
                            (
                                resolution['type_document_id'],
                                resolution['prefix'],
                                resolution['resolution'],
                                resolution['resolution_date'],
                                resolution['technical_key'],
                                resolution['from'],
                                resolution['to'],
                                resolution['date_from'],
                                resolution['date_to'],
                                resolution['id'],
                                resolution['number'],
                                resolution['next_consecutive'],
                                self.env.user.id,
                                'NOW()',
                                self.env.user.id,
                                'NOW()'
                            )
                        )
        except Exception as e:
            raise Warning(e)

        # To update or redirect to the resolutions views
        return {
            "name": "Resoluciones",
            "type": "ir.actions.act_window",
            "res_model": "l10n_co_edi_jorels.resolution",
            "views": [[False, "tree"], [False, "form"]],
        }

    # Actualización de entorno
    @api.multi
    def button_put_environment(self):
        try:
            for rec in self:
                if rec.is_not_test:
                    environment = 1
                else:
                    environment = 2

                api_file_path = Path(__file__).parents[2] / 'static' / 'api.json'
                with open(api_file_path) as api_file:
                    requests_data = json.loads(api_file.read())
                requests_data['environment']['type_environment_id'] = environment
                _logger.debug("Request environment DIAN: %s",
                              json.dumps(requests_data['environment'], indent=2, sort_keys=False))

                token = rec.api_key
                api_url = rec.api_url

                header = {"accept": "application/json", "Content-Type": "application/json"}
                api_url = api_url + "/api/ubl2.1/config/environment"
                header.update({'Authorization': 'Bearer ' + token})
                response = requests.put(api_url, json.dumps(requests_data['environment']), headers=header).json()
                _logger.debug('API Response PUT environment: %s', response)

                if 'message' in response:
                    rec.env.user.notify_info(message=response['message'])
                else:
                    rec.env.user.notify_info(message="Ahora, sincronice las resoluciones")
        except Exception as e:
            _logger.debug("Error de comunicación: %s", e)
