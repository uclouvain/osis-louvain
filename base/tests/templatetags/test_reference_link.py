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
from django.test import TestCase

from base.models.enums.link_type import LinkTypes
from base.templatetags.reference_link import get_parent_of_reference_link
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory


class ReferenceLinkTagTests(TestCase):

    def setUp(self):
        academic_yr = AcademicYearFactory()
        self.grandfather = EducationGroupYearFactory(
            academic_year=academic_yr,
        )
        self.parent = EducationGroupYearFactory(
            academic_year=academic_yr,
        )
        self.child = EducationGroupYearFactory(
            academic_year=academic_yr,
        )

    def test_no_reference_link(self):
        self.assertIsNone(get_parent_of_reference_link(self.parent))
        GroupElementYearFactory(
            parent=self.parent,
            child_branch=self.child,
        )
        self.assertIsNone(get_parent_of_reference_link(self.parent))

    def test_reference_link(self):
        group_element_yr_reference = GroupElementYearFactory(
            parent=self.grandfather,
            child_branch=self.child,
            link_type=LinkTypes.REFERENCE.name,
        )
        self.assertEqual(get_parent_of_reference_link(group_element_yr_reference.child_branch),
                         group_element_yr_reference)
