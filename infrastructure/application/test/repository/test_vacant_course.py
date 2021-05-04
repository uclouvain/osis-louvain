##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from base.models.enums import learning_container_year_types, vacant_declaration_type
from base.tests.factories.learning_component_year import LecturingLearningComponentYearFactory, \
    PracticalLearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from ddd.logic.application.domain.model.vacant_course import VacantCourseIdentity, VacantCourse
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYearIdentity
from infrastructure.application.repository.vacant_course import VacantCourseRepository


class VacantCourseRepositoryGet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year_db = LearningUnitYearFactory(
            acronym='LDROI1200',
            academic_year__year=2020,
            learning_container_year__acronym='LDROI1200',
            learning_container_year__academic_year__year=2020,
            learning_container_year__container_type=learning_container_year_types.COURSE,
            learning_container_year__type_declaration_vacant=vacant_declaration_type.RESEVED_FOR_INTERNS,
            learning_container_year__team=True
        )
        LecturingLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_db,
            volume_declared_vacant=Decimal(15)
        )
        PracticalLearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_db,
            volume_declared_vacant=Decimal(10)
        )
        cls.repository = VacantCourseRepository()

    def test_get_assert_return_not_found(self):
        vacant_course_id_unknown = VacantCourseIdentity(
            academic_year=AcademicYearIdentity(year=2018),
            code='LDROI1200'
        )
        with self.assertRaises(ObjectDoesNotExist):
            self.repository.get(vacant_course_id_unknown)

    def test_get_assert_return_instance(self):
        vacant_course_id = VacantCourseIdentity(
            academic_year=AcademicYearIdentity(year=2020),
            code='LDROI1200'
        )
        vacant_course = self.repository.get(vacant_course_id)

        self.assertIsInstance(vacant_course, VacantCourse)

        self.assertEqual(vacant_course.entity_id, vacant_course_id)
        self.assertTrue(vacant_course.is_in_team)
        self.assertEqual(vacant_course.vacant_declaration_type, vacant_declaration_type.RESEVED_FOR_INTERNS)
        expected_title = "{} - {}".format(
            self.learning_unit_year_db.learning_container_year.common_title,
            self.learning_unit_year_db.specific_title
        )
        self.assertEqual(vacant_course.title, expected_title)
        self.assertEqual(vacant_course.lecturing_volume_available, Decimal(15))
        self.assertEqual(vacant_course.practical_volume_available, Decimal(10))
