##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django.utils import timezone
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from base.models import academic_year
from base.models import entity
from base.models.enums import entity_type
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory

from assistant.models.mandate_entity import find_by_mandate_and_entity
from assistant.models.tutoring_learning_unit_year import find_by_mandate
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.tutoring_learning_unit_year import TutoringLearningUnitYearFactory
from assistant.utils.import_xls_file_data import check_date_format
from assistant.utils.import_xls_file_data import check_file_format
from assistant.utils.import_xls_file_data import create_academic_assistant_if_not_exists
from assistant.utils.import_xls_file_data import create_assistant_mandate_if_not_exists
from assistant.utils.import_xls_file_data import link_mandate_to_entity
from assistant.utils.import_xls_file_data import read_xls_mandates
from assistant.utils.import_xls_file_data import retrieve_learning_units_year_from_previous_mandate
from assistant.utils.import_xls_file_data import search_entity_by_acronym_and_type
from assistant.utils import import_xls_file_data
from assistant.utils.import_xls_file_data import COLS_TITLES

HTTP_OK = 200


class ExportImportXlsFile(TestCase):
    def setUp(self):
        self.client = Client()
        self.request = self.client.post('/assistants/manager/mandates/upload/')
        self.request._messages = FakeMessages()
        self.manager = ManagerFactory()
        self.client.force_login(self.manager.person.user)
        self.request.user = self.manager.person.user
        now = timezone.now()
        AcademicYearFactory.produce_in_past()
        self.previous_academic_year = academic_year.find_academic_year_by_year(now.year - 2)
        self.person1 = PersonFactory(global_id='00201968')
        self.assistant1 = AcademicAssistantFactory(person=self.person1)
        self.record1 = {
            'SECTOR': 'SST', 'LOGISTICS_ENTITY': 'None', 'FACULTY': 'SC', 'SCHOOL': 'CHIM', 'INSTITUTE': 'IMCN',
            'POLE': 'MOST', 'SAP_ID': '1122199', 'GLOBAL_ID': '1122199', 'LAST_NAME': self.assistant1.person.last_name,
            'FIRST_NAME': self.assistant1.person.first_name, 'FULLTIME_EQUIVALENT': '1', 'ENTRY_DATE': '01/02/2015',
            'END_DATE': '03-10-2017', 'ASSISTANT_TYPE_CODE': 'ST', 'SCALE': '021', 'CONTRACT_DURATION': '4',
            'CONTRACT_DURATION_FTE': '4', 'RENEWAL_TYPE': 'NORMAL', 'ABSENCES': None, 'COMMENT': None,
            'OTHER_STATUS': None, 'EMAIL': None, 'FGS': '00201968'
        }
        self.person2 = PersonFactory(global_id='00201979')
        self.assistant2 = AcademicAssistantFactory()
        self.record2 = {
            'SECTOR': 'SST', 'LOGISTICS_ENTITY': 'None', 'FACULTY': 'SC', 'SCHOOL': 'CHIM', 'INSTITUTE': 'IMCN',
            'POLE': 'MOST', 'SAP_ID': '1122199', 'GLOBAL_ID': '1122199', 'LAST_NAME': self.person2.last_name,
            'FIRST_NAME': self.person2.first_name, 'FULLTIME_EQUIVALENT': '1', 'ENTRY_DATE': '01/02/2015',
            'END_DATE': '03-10-2017', 'ASSISTANT_TYPE_CODE': 'AS', 'SCALE': '021', 'CONTRACT_DURATION': '4',
            'CONTRACT_DURATION_FTE': '4', 'RENEWAL_TYPE': 'exceptional', 'ABSENCES': None, 'COMMENT': None,
            'OTHER_STATUS': None, 'EMAIL': None, 'FGS': '00201979'
        }
        self.assistant3 = AcademicAssistantFactory()
        self.record3 = {
            'SECTOR': 'SST', 'LOGISTICS_ENTITY': 'None', 'FACULTY': 'SC', 'SCHOOL': 'CHIM', 'INSTITUTE': 'IMCN',
            'POLE': 'MOST', 'SAP_ID': '1122599', 'GLOBAL_ID': '1322199', 'LAST_NAME': 'last_name',
            'FIRST_NAME': 'first_name', 'FULLTIME_EQUIVALENT': '1', 'ENTRY_DATE': '01/02/2015',
            'END_DATE': '03-10-2017', 'ASSISTANT_TYPE_CODE': 'AS', 'SCALE': '021', 'CONTRACT_DURATION': '4',
            'CONTRACT_DURATION_FTE': '4', 'RENEWAL_TYPE': 'SPECIAL', 'ABSENCES': None, 'COMMENT': None,
            'OTHER_STATUS': None, 'EMAIL': None, 'FGS': None
        }
        self.entity_version1 = EntityVersionFactory(entity_type=entity_type.SECTOR,
                                                    acronym='SST',
                                                    title='Secteur des Sciences et Technologies',
                                                    end_date=datetime.datetime(datetime.date.today().year + 1, 9, 14))
        self.entity_version2 = EntityVersionFactory(entity_type=entity_type.SECTOR,
                                                    acronym='SSH',
                                                    end_date=datetime.datetime(datetime.date.today().year + 1, 9, 14))
        self.assistant_mandate1 = AssistantMandateFactory(
            assistant=self.assistant1
        )

    def test_upload_mandates_file(self):
        file = File(open('assistant/tests/resources/assistants_ok.xlsx', 'rb'))
        response = self.client.post('/assistants/manager/mandates/upload/', {'file': file})
        self.assertEqual(response.status_code, HTTP_OK)
        file2 = File(open('assistant/tests/resources/bad_file_format.txt', 'rb'))
        response2 = self.client.post('/assistants/manager/mandates/upload/', {'file': file2})
        self.assertEqual(response2.status_code, HTTP_OK)

    def test_read_xls_mandates(self):
        file = File(open('assistant/tests/resources/assistants_bad_date.xlsx', 'rb'))
        uploaded_file = SimpleUploadedFile(
            'new_excel.xlsx', file.read(),
            content_type='vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertFalse(read_xls_mandates(self.request, uploaded_file))
        file2 = File(open('assistant/tests/resources/assistants_ok.xlsx', 'rb'))
        uploaded_file2 = SimpleUploadedFile(
            'new_excel.xlsx', file2.read(),
            content_type='vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue(read_xls_mandates(self.request, uploaded_file2))
        file3 = File(open('assistant/tests/resources/assistants_bad_column.xlsx', 'rb'))
        uploaded_file3 = SimpleUploadedFile(
            'new_excel.xlsx', file3.read(),
            content_type='vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertFalse(read_xls_mandates(self.request, uploaded_file3))

    def test_dates_format_(self):
        self.assertFalse(check_date_format('12/2015/92'))
        self.assertTrue(check_date_format('12/02/2015'))
        self.assertTrue(check_date_format('12-05-2013'))
        self.assertFalse(check_date_format('34-14-2013'))
        self.assertFalse(check_date_format('34_14_2013 '))

    def test_check_file_format(self):
        cols = COLS_TITLES.copy()
        self.assertTrue(check_file_format(self.request, cols))
        cols.append('NEW_COL')
        self.assertFalse(check_file_format(self.request, cols))
        cols.pop()
        cols[0] = 'BAD_TITLE'
        cols[1] = 'ANOTHER_BAD_TITLE'
        self.assertFalse(check_file_format(self.request, cols))

    def test_create_academic_assistant_if_not_exists(self):
        nbr_assistant_updated = import_xls_file_data.ASSISTANTS_UPDATED
        nbr_assistant_imported = import_xls_file_data.ASSISTANTS_IMPORTED
        nbr_persons_not_found = import_xls_file_data.PERSONS_NOT_FOUND
        create_academic_assistant_if_not_exists(self.record1)
        self.assertEqual(import_xls_file_data.ASSISTANTS_IMPORTED, nbr_assistant_imported)
        self.assertEqual(nbr_assistant_updated + 1, import_xls_file_data.ASSISTANTS_UPDATED)
        self.assertEqual(nbr_persons_not_found, import_xls_file_data.PERSONS_NOT_FOUND)
        create_academic_assistant_if_not_exists(self.record2)
        self.assertEqual(import_xls_file_data.ASSISTANTS_IMPORTED, nbr_assistant_imported + 1)
        self.assertEqual(nbr_assistant_updated + 1, import_xls_file_data.ASSISTANTS_UPDATED)
        self.assertEqual(nbr_persons_not_found, import_xls_file_data.PERSONS_NOT_FOUND)
        create_academic_assistant_if_not_exists(self.record3)
        self.assertEqual(import_xls_file_data.ASSISTANTS_IMPORTED, nbr_assistant_imported + 1)
        self.assertEqual(nbr_assistant_updated + 1, import_xls_file_data.ASSISTANTS_UPDATED)
        self.assertEqual(nbr_persons_not_found + 1, import_xls_file_data.PERSONS_NOT_FOUND)

    def test_create_assistant_mandate_if_not_exists(self):
        nbr_mandates_imported = import_xls_file_data.MANDATES_IMPORTED
        nbr_mandates_updated = import_xls_file_data.MANDATES_UPDATED
        create_assistant_mandate_if_not_exists(
            self.record1, self.assistant1, check_date_format(self.record1.get('END_DATE')),
            check_date_format(self.record1.get('END_DATE'))
        )
        self.assertEqual(import_xls_file_data.MANDATES_IMPORTED, nbr_mandates_imported + 1)
        self.assertEqual(import_xls_file_data.MANDATES_UPDATED, nbr_mandates_updated)
        create_assistant_mandate_if_not_exists(
            self.record1, self.assistant1, check_date_format(self.record1.get('END_DATE')),
            check_date_format(self.record1.get('END_DATE'))
        )
        self.assertEqual(import_xls_file_data.MANDATES_IMPORTED, nbr_mandates_imported + 1)
        self.assertEqual(import_xls_file_data.MANDATES_UPDATED, nbr_mandates_updated + 1)
        create_assistant_mandate_if_not_exists(
            self.record2, self.assistant2, check_date_format(self.record2.get('END_DATE')),
            check_date_format(self.record2.get('END_DATE'))
        )
        self.assertEqual(import_xls_file_data.MANDATES_IMPORTED, nbr_mandates_imported + 2)
        self.assertEqual(import_xls_file_data.MANDATES_UPDATED, nbr_mandates_updated + 1)
        create_assistant_mandate_if_not_exists(
            self.record3, self.assistant3, check_date_format(self.record3.get('END_DATE')),
            check_date_format(self.record3.get('END_DATE'))
        )
        self.assertEqual(import_xls_file_data.MANDATES_IMPORTED, nbr_mandates_imported + 3)
        self.assertEqual(import_xls_file_data.MANDATES_UPDATED, nbr_mandates_updated + 1)

    def test_retrieve_learning_units_year_from_previous_mandate(self):
        self.assistant_mandate3 = AssistantMandateFactory(assistant=self.assistant2)
        self.assistant_mandate2 = AssistantMandateFactory(
            assistant=self.assistant1,
            academic_year=self.previous_academic_year
        )
        self.tutoring_learning_unit_year1 = TutoringLearningUnitYearFactory(mandate=self.assistant_mandate2)
        self.tutoring_learning_unit_year2 = TutoringLearningUnitYearFactory(mandate=self.assistant_mandate2)
        self.assistant_mandate5 = AssistantMandateFactory(
            assistant=self.assistant2
        )
        retrieve_learning_units_year_from_previous_mandate(self.assistant1, self.assistant_mandate1)
        self.assertEqual(len(find_by_mandate(self.assistant_mandate1)), 2)

        retrieve_learning_units_year_from_previous_mandate(self.assistant2, self.assistant_mandate5)
        self.assertEqual(len(find_by_mandate(self.assistant_mandate5)), 0)

        retrieve_learning_units_year_from_previous_mandate(self.assistant2, self.assistant_mandate3)
        self.assertEqual(len(find_by_mandate(self.assistant_mandate3)), 0)

    def test_link_mandate_to_entity(self):
        self.assertEqual(
            link_mandate_to_entity(self.assistant_mandate1, self.entity_version1.entity),
            find_by_mandate_and_entity(self.assistant_mandate1, self.entity_version1.entity)[0]
        )
        self.assertEqual(link_mandate_to_entity(self.assistant_mandate1), None)
        self.assertEqual(
            link_mandate_to_entity(self.assistant_mandate1, self.entity_version2.entity),
            find_by_mandate_and_entity(self.assistant_mandate1, self.entity_version2.entity)[0]
        )

    def test_search_entity_by_acronym_and_type(self):
        self.assertIsInstance(search_entity_by_acronym_and_type('SST', entity_type.SECTOR), entity.Entity)
        self.assertEqual(search_entity_by_acronym_and_type(None, entity_type.SECTOR), None)
        self.assertEqual(search_entity_by_acronym_and_type(None, entity_type.SECTOR), None)
        self.assertEqual(search_entity_by_acronym_and_type('SST', None), None)


class FakeMessages:
    messages = []

    def add(self, level, message, extra_tags):
        self.messages.append(str(message))

    @property
    def pop(self):
        return self.messages.pop()
