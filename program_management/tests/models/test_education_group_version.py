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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.utils.datetime_safe import datetime

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.models.group_year import GroupYear
from program_management.models.education_group_version import EducationGroupVersion
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory, \
    StandardEducationGroupVersionFactory, ParticularTransitionEducationGroupVersionFactory


class TestEducationGroupVersion(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.academic_year = AcademicYear(year=datetime.today().year)
        cls.offer = EducationGroupYear(academic_year=cls.academic_year, partial_acronym='PA', acronym='ACRO')
        cls.root_group = GroupYear()

    def test_str_education_group_version(self):
        version = EducationGroupVersion(version_name='version', offer=self.offer, root_group=self.root_group)
        self.assertEqual(str(version), '{} ({})'.format(version.offer, version.version_name))

    def test_str_standard_education_group_version(self):
        version = EducationGroupVersion(offer=self.offer, root_group=self.root_group)
        self.assertEqual(str(version), str(version.offer))


class TestStandardEducationGroupManager(TestCase):

    def setUp(self):
        self.not_standard_version = EducationGroupVersionFactory()
        self.standard_version = StandardEducationGroupVersionFactory()

    def test_standard_education_group_version_manager(self):
        result = EducationGroupVersion.standard.all()
        self.assertIn(self.standard_version, result)
        self.assertNotIn(self.not_standard_version, result)


class TestEducationGroupVersionModel(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.offer_1 = EducationGroupYearFactory(academic_year=self.academic_year)

    def test_unique(self):
        particular_version = ParticularTransitionEducationGroupVersionFactory(version_name='CEMSS', offer=self.offer_1)
        with self.assertRaises(IntegrityError):
            ParticularTransitionEducationGroupVersionFactory(version_name=particular_version.version_name,
                                                             offer=self.offer_1)
