##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.apps import apps
from django.core.management import BaseCommand
from openpyxl import load_workbook

NATURAL_KEY_IDENTIFIER = '**'

# Need to use aliases because worksheet title is limited to max 31 chars
APP_NAME_ALIASES = {
    'part': 'partnership',
}


class Command(BaseCommand):
    help = """
    Command to load data in DB from a structured xls file where :
    - The worksheet title is the <app>.<model> name (e.g. base.Student)
    - The first row of the worksheet is the header
    - Each value in the header is a column of the model (e.g. registration_id, person__user__username)
    - Each row (after the header) is a record of the Model
    - Each value in a row is the value for the model field specified in the header

    Use '**' at the end of the header cell value to force a natural key for the model of your worksheet.

    """

    def handle(self, *args, **options):
        apps.clear_cache()
        workbook = load_workbook("fixtures_to_load.xlsx", read_only=True, data_only=True)
        for ws in workbook.worksheets:
            model_class = self._get_model_class_from_worksheet_title(ws)
            if model_class:
                xls_rows = list(ws.rows)
                print('Number of records : {}'.format(len(xls_rows)))
                headers = [(idx, cell.value) for idx, cell in enumerate(xls_rows[0])]
                for line_index, row in enumerate(xls_rows[1:]):
                    try:
                        self._save_in_database(row, model_class, headers)
                    except Exception as e:
                        print('    ERROR at line {} :: {}'.format(line_index+1, e))

    @staticmethod
    def _get_model_class_from_worksheet_title(xls_worksheet):
        ws_title = xls_worksheet.title
        app_name, model_name = ws_title.split('.')
        app_name = APP_NAME_ALIASES.get(app_name, app_name)
        print()
        print('Working on {}...'.format(ws_title))
        try:
            return apps.get_model(app_name, model_name)
        except LookupError as e:
            print('ERROR :: {}'.format(e))
            print('ERROR :: Ignoring data from worksheet named "{}"'.format(ws_title))
            return None

    def _save_in_database(self, row, model_class, headers):
        object_as_dict = {
            column_name: row[idx].value for idx, column_name in headers if column_name
        }
        object_dict_with_relations = {
            fk_field_name: self._convert_boolean_cell_value(value_as_obj)
            for fk_field_name, value_as_obj in [
                self._find_object_through_foreign_keys(model_class, col_name, value)
                for col_name, value in object_as_dict.items()
            ]
        }
        unique_values = {
            self._clean_header_from_special_chars(col_name): value
            for col_name, value in object_dict_with_relations.items()
            if NATURAL_KEY_IDENTIFIER in col_name
        }
        defaults = {
            col_name: value
            for col_name, value in object_dict_with_relations.items()
            if NATURAL_KEY_IDENTIFIER not in col_name
        }
        obj, created = model_class.objects.update_or_create(**unique_values, defaults=defaults)
        print('    SUCCESS : Object < {} > successfully {}'.format(obj, 'created' if created else 'updated'))
        return obj, created

    @staticmethod
    def _clean_header_from_special_chars(header):
        """Special chars are used to know if the field compose the unique constraint for update_or_create"""
        # FIXME :: should use the natural_key when Osis-portal will be removed (actually using UUID as natural key)
        return header.replace(NATURAL_KEY_IDENTIFIER, "")

    @staticmethod
    def _convert_boolean_cell_value(value):
        if value == 'True':
            return True
        elif value == 'False':
            return False
        return value

    def _find_object_through_foreign_keys(self, model_class, col_name, value, recur=0) -> object:
        is_natural_key_field = NATURAL_KEY_IDENTIFIER in col_name
        foreign_key_field = col_name
        if '__' in col_name:
            splitted_col_name = col_name.split('__')
            foreign_key_field = splitted_col_name[0]
            if foreign_key_field in [f.name for f in model_class._meta.fields]:
                field = model_class._meta.get_field(foreign_key_field)
                if field.is_relation:
                    _, related_obj = self._find_object_through_foreign_keys(
                        field.related_model,
                        '__'.join(splitted_col_name[1:]),
                        value,
                        recur=recur+1
                    )
                    value = related_obj
            else:
                foreign_key_field = col_name

        if is_natural_key_field:
            foreign_key_field += NATURAL_KEY_IDENTIFIER

        if recur == 0:
            return foreign_key_field, value

        kwargs = {self._clean_header_from_special_chars(foreign_key_field): value}

        return foreign_key_field, model_class.objects.get(**kwargs)
