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
from django.core.exceptions import ValidationError
from django.test import TestCase

from base.models.education_group_publication_contact import ROLE_REQUIRED_FOR_TYPES
from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory


class EducationGroupPublicationContactCleanTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()

    def test_role_required_for_types(self):
        self.assertEqual(
            ROLE_REQUIRED_FOR_TYPES,
            (PublicationContactType.JURY_MEMBER.name, PublicationContactType.OTHER_CONTACT.name,)
        )

    def test_clean_case_role_not_specified_when_mandatory(self):
        publication_contact = EducationGroupPublicationContactFactory.build(
            type=PublicationContactType.JURY_MEMBER.name,
            role_fr='',
            role_en=''
        )
        with self.assertRaises(ValidationError):
            publication_contact.clean()

    def test_clean_case_role_specified_when_not_mandatory(self):
        publication_contact = EducationGroupPublicationContactFactory.build(
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
            role_fr='dummy role in french',
            role_en='dummy role in english'
        )

        publication_contact.clean()
        self.assertEqual(publication_contact.role_fr, '')
        self.assertEqual(publication_contact.role_en, '')
