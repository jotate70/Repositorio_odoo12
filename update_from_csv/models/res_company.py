# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import csv
from pathlib import Path

import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def init_csv_data(self, model):
        try:
            module_name = model.split('.')[0]
            model = model[len(module_name) + 1:]
            file_name = model + '.csv'
            _logger.debug("Import csv file: %s", file_name)
            file_path = Path(__file__).parents[2] / module_name / 'data' / file_name
            table_name = model.replace(".", "_")

            with open(file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        _logger.debug(f'Column names are {", ".join(row)}')
                        field_names = row
                    query = "insert into " + table_name + "("
                    for field_name in field_names:
                        query = query + field_name + ","
                    query = query + "create_uid,create_date,write_uid,write_date) values("
                    for field_name in field_names:
                        query = query + "$$" + row[field_name] + "$$,"
                    query = query + str(self.env.user.id) + ',NOW(),' + str(self.env.user.id) + \
                            ',NOW()) ON CONFLICT DO NOTHING'
                    self._cr.execute(query)
                    line_count += 1
                self._cr.execute("select max(id) from " + table_name)
                max_id = self._cr.dictfetchall()[0]['max']
                self._cr.execute(f"SELECT setval('{table_name}_id_seq',{str(max_id + 1)}, true)")
                _logger.debug(f'Processed {line_count} records on table {table_name}')
        except Exception as e:
            _logger.debug("init_csv_data %s", e)
