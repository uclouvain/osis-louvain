# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

import pypom
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from features.pages.common import CommonPageMixin
from features.fields.fields import InputField, SelectField, ButtonField


class SearchEntityPage(CommonPageMixin, pypom.Page):
    URL_TEMPLATE = '/entities/'

    acronym = InputField(By.ID, 'id_acronym')
    title = InputField(By.ID, 'id_title')
    entity_type = SelectField(By.ID, "id_entity_type")

    search = ButtonField(By.ID, "bt_submit_entity_search")

    def find_acronym_in_table(self, row: int = 1):
        return self.find_element(By.ID, 'td_entity_%d' % row).text


class SearchOrganizationPage(CommonPageMixin, pypom.Page):

    URL_TEMPLATE = '/organizations/'

    acronym = InputField(By.ID, 'id_acronym')
    name = InputField(By.ID, 'id_name')
    type = SelectField(By.ID, "id_type")

    search = ButtonField(By.ID, "bt_submit_organization_search")

    def find_acronym_in_table(self, row: int = 1):
        return self.find_element(By.ID, 'td_organization_%d' % row).text


class SearchStudentPage(CommonPageMixin, pypom.Page):

    URL_TEMPLATE = '/students/'

    registration_id = InputField(By.ID, 'id_registration_id')
    name = InputField(By.ID, 'id_name')

    search = ButtonField(By.ID, "bt_submit_student_search")

    def find_registration_id_in_table(self, row: int = 1):
        return self.find_element(By.ID, 'td_student_%d' % row).text

    def find_name_in_table(self):
        names = []
        row = 1
        last = False
        while not last:
            try:
                elt = self.find_element(By.ID, 'spn_student_name_%d' % row)
                names.append(elt.text)

                row += 1
            except NoSuchElementException as e:
                return names

        return names
