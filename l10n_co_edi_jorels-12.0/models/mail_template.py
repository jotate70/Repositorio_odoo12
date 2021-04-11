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

from odoo import api, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        res = super(MailTemplate, self).generate_email(res_ids, fields)

        if self.env.context.get('attach_ei_zip_file'):
            for res_id, template in self.get_email_template(res_ids).items():
                invoice = self.env['account.invoice'].browse(res_id)
                zip_filename = invoice.ei_uuid
                zip_string = invoice.ei_attached_zip_base64_bytes
                zip_attachments = invoice._generate_email_attachment(zip_filename, zip_string)
                if len(zip_attachments) == 1 and zip_filename:
                    ext = '.zip'
                    if not zip_filename.endswith(ext):
                        zip_filename += ext
                    attachments = [(zip_filename, zip_attachments.datas)]
                else:
                    attachments = [(a.name, a.datas) for a in zip_attachments]
                res[res_id]['attachments'] += attachments

        return res
