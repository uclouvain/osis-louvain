# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from unittest import mock

from django.test.testcases import TestCase

from base.utils.load_sql_scripts import ExecuteSQLTriggers, LoadSQLFilesToExecute


class TestLoadSQLFilesToExecute(TestCase):
    def setUp(self):
        self.subfolder = 'test/'
        self.load_sql = LoadSQLFilesToExecute(subfolder=self.subfolder)

    def test_scripts_path_as_backoffice_and_subfolder(self):
        self.assertEqual(self.load_sql.scripts_path, 'backoffice/test/')

    @mock.patch('base.utils.load_sql_scripts.LoadSQLFilesToExecute._get_scripts_files')
    def test_load_scripts_should_return_error_if_not_sql_file(self, mock_get_files):
        filename = 'test.sol'
        mock_get_files.return_value = [filename]
        with self.assertRaises(SystemExit):
            self.load_sql.load_scripts()

    @mock.patch('base.utils.load_sql_scripts.LoadSQLFilesToExecute._get_scripts_files')
    @mock.patch('base.utils.load_sql_scripts.LoadSQLFilesToExecute._get_sql_string_statement_from_file')
    def test_load_scripts_should_return_dict_with_filename_and_script_string(self, mock_get_sql, mock_get_files):
        filename = 'test.sql'
        mock_get_files.return_value = [filename]
        script = """
            SELECT * FROM a WHERE b = c;
            UPDATE test set b = 'c';
            DELETE FROM test WHERE b = 'c';
        """
        mock_get_sql.return_value = script
        result = self.load_sql.load_scripts()
        expected_result = {filename: script}
        self.assertDictEqual(result, expected_result)


class TestExecuteSQLTriggers(TestCase):
    def setUp(self):
        self.executeSQL_triggers = ExecuteSQLTriggers()
        self.table_name = 'public.education_group_groupyear'
        self.script = """
            TEST
            CREATE TRIGGER TEST
                TEST
                
                ON {tablename}
                TEST
                WHEN TEST
            TEST;
        """.format(tablename=self.table_name)
        self.filename = 'test.sql'

    def test_load_trigger_should_raise_error_if_unable_to_get_tablename(self):
        script_without_trigger = """
            CREATE TEST
                ON public.education_group_groupyear
                TEST;
        """
        script_tablename_bad_format = """
            CREATE TRIGGER
                ON poblic.education_group_groupyear
                TEST;
        """
        for script in [script_tablename_bad_format, script_without_trigger]:
            with self.assertRaises(SystemExit):
                self.executeSQL_triggers.load_trigger(script=script, filename=self.filename)

    @mock.patch('base.utils.load_sql_scripts.ExecuteSQL.execute')
    def test_load_trigger_should_call_execute_with_locked_script(self, mock_execute):
        self.executeSQL_triggers.load_trigger(script=self.script, filename=self.filename)
        expected_locked_script = """
            BEGIN WORK;
            LOCK TABLE public.education_group_groupyear IN SHARE ROW EXCLUSIVE MODE;
            
            TEST
            CREATE TRIGGER TEST
                TEST
                ON public.education_group_groupyear
                TEST
                WHEN TEST
            TEST;
            
            COMMIT WORK;
        """.replace(' ', '')
        self.assertEqual(mock_execute.call_args[0][0].replace(' ', ''), expected_locked_script)
