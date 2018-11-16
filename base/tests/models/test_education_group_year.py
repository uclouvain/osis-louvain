##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.models.education_group_year import find_by_id, search, find_with_enrollments_count
from base.models.enums import education_group_categories, duration_unit
from base.models.enums.constraint_type import CREDITS
from base.models.exceptions import MaximumOneParentAllowedException
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory


class EducationGroupYearTest(TestCase):

    def setUp(self):
        academic_year = AcademicYearFactory()
        self.education_group_type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)

        self.education_group_type_minitraining = EducationGroupTypeFactory(
            category=education_group_categories.MINI_TRAINING
        )

        self.education_group_type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

        self.education_group_year_1 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_training)
        self.education_group_year_2 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_minitraining)

        self.education_group_year_3 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_training)
        self.education_group_year_4 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_group)
        self.education_group_year_5 = EducationGroupYearFactory(academic_year=academic_year,
                                                                education_group_type=self.education_group_type_group)

        self.educ_group_year_domain = EducationGroupYearDomainFactory(education_group_year=self.education_group_year_2)

        self.entity_version_admin = EntityVersionFactory(
            entity=self.education_group_year_2.administration_entity,
            start_date=self.education_group_year_2.academic_year.start_date,
            parent=None
        )

        self.offer_year_3 = OfferYearFactory(academic_year=academic_year)

        self.entity_version_management = EntityVersionFactory(
            entity=self.education_group_year_3.management_entity,
            start_date=self.education_group_year_3.academic_year.start_date,
            parent=None
        )

        self.group_element_year_4 = GroupElementYearFactory(parent=self.education_group_year_3,
                                                            child_branch=self.education_group_year_1)
        self.group_element_year_5 = GroupElementYearFactory(parent=self.education_group_year_3,
                                                            child_branch=self.education_group_year_1)

    def test_verbose_credit(self):
        verbose__waiting = "{} ({} {})".format(
            self.education_group_year_1.title, self.education_group_year_1.credits, _("credits")
        )
        self.assertEqual(self.education_group_year_1.verbose_credit, verbose__waiting)

    def test_find_by_id(self):
        education_group_year = find_by_id(self.education_group_year_1.id)
        self.assertEqual(education_group_year, self.education_group_year_1)

        education_group_year = find_by_id(-1)
        self.assertIsNone(education_group_year)

    def test_search(self):
        result = search(id=[self.education_group_year_1.id, self.education_group_year_2.id])
        self.assertEqual(len(result), 2)

        result = search(education_group_type=self.education_group_year_2.education_group_type)
        self.assertEqual(result.first().education_group_type,
                         self.education_group_year_2.education_group_type)

        result = search(education_group_type=[self.education_group_type_training,
                                              self.education_group_type_minitraining])
        self.assertEqual(len(result), 3)

    def test_domains_property(self):
        domains = self.education_group_year_1.str_domains
        self.assertEqual(domains, '')

        domains = self.education_group_year_2.str_domains
        offer_year_domain = "{}-{}\n".format(self.educ_group_year_domain.domain.decree,
                                             self.educ_group_year_domain.domain.name)
        self.assertEqual(domains, offer_year_domain)

    def test_administration_entity_version_property(self):
        self.assertEqual(self.education_group_year_2.administration_entity_version, self.entity_version_admin)

    def test_management_entity_version_property(self):
        self.assertEqual(self.education_group_year_3.management_entity_version, self.entity_version_management)

    def test_parent_by_training_property(self):
        parent_by_training = self.education_group_year_3.is_training()
        self.assertTrue(parent_by_training)

        parent_by_training = self.education_group_year_2.parent_by_training
        self.assertIsNone(parent_by_training)

        with self.assertRaises(MaximumOneParentAllowedException):
            parent_by_training = self.education_group_year_1.parent_by_training

    def test_children_group_element_years_property(self):
        children_group_element_years = self.education_group_year_1.children_group_element_years
        self.assertListEqual(list(children_group_element_years), [])

    def test_direct_parents_of_branch(self):
        GroupElementYearFactory(
            parent=self.education_group_year_2,
            child_branch=self.education_group_year_1
        )
        GroupElementYearFactory(
            parent=self.education_group_year_4,
            child_branch=self.education_group_year_1
        )
        GroupElementYearFactory(
            parent=self.education_group_year_5,
            child_branch=self.education_group_year_4
        )

        self.assertCountEqual(
            self.education_group_year_1.direct_parents_of_branch,
            [
                self.education_group_year_2,
                self.education_group_year_3,
                self.education_group_year_4,
            ]
        )

    def test_ascendants_of_branch(self):
        GroupElementYearFactory(
            parent=self.education_group_year_2,
            child_branch=self.education_group_year_1
        )
        GroupElementYearFactory(
            parent=self.education_group_year_4,
            child_branch=self.education_group_year_1
        )
        GroupElementYearFactory(
            parent=self.education_group_year_5,
            child_branch=self.education_group_year_4
        )
        GroupElementYearFactory(
            parent=self.education_group_year_5,
            child_branch=self.education_group_year_1
        )

        self.assertCountEqual(
            self.education_group_year_1.ascendants_of_branch,
            [
                self.education_group_year_2,
                self.education_group_year_3,
                self.education_group_year_4,
                self.education_group_year_5,
            ]
        )


class EducationGroupYearCleanTest(TestCase):
    def test_clean_constraint(self):

        e = EducationGroupYearFactory(min_constraint=12, max_constraint=20, constraint_type=CREDITS)
        try:
            e.clean()
        except ValidationError:
            self.fail()

    def test_clean_no_constraint_type(self):
        e = EducationGroupYearFactory(min_constraint=12, max_constraint=20, constraint_type=None)

        with self.assertRaises(ValidationError):
            e.clean()

    def test_clean_no_min_max(self):
        e = EducationGroupYearFactory(min_constraint=None, max_constraint=None, constraint_type=CREDITS)

        with self.assertRaises(ValidationError):
            e.clean()

    def test_clean_min_gt_max(self):
        e = EducationGroupYearFactory(min_constraint=20, max_constraint=10, constraint_type=CREDITS)

        with self.assertRaises(ValidationError):
            e.clean()

    def test_clean_case_no_duration_with_duration_unit(self):
        e = EducationGroupYearFactory(duration=None, duration_unit=duration_unit.QUADRIMESTER)

        with self.assertRaises(ValidationError):
            e.clean()

    def test_clean_case_no_duration_unit_with_duration(self):
        e = EducationGroupYearFactory(duration=1, duration_unit=None)

        with self.assertRaises(ValidationError):
            e.clean()


class TestFindWithEnrollmentsCount(TestCase):
    """Unit tests on find_with_enrollments_count()"""

    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.education_group_year = EducationGroupYearFactory(academic_year=self.current_academic_year)
        GroupElementYearFactory(parent=self.education_group_year,
                                child_branch=None,
                                child_leaf=self.learning_unit_year)

    def test_without_learning_unit_enrollment_but_with_offer_enrollments(self):
        OfferEnrollmentFactory(education_group_year=self.education_group_year)
        result = find_with_enrollments_count(self.learning_unit_year)
        self.assertEqual(list(result), [])

    def test_with_learning_unit_enrollment_and_with_offer_enrollments(self):
        enrol_not_in_education_group = LearningUnitEnrollmentFactory(learning_unit_year=LearningUnitYearFactory())
        result = find_with_enrollments_count(enrol_not_in_education_group.learning_unit_year)
        self.assertEqual(result[0].count_learning_unit_enrollments, 1)
        self.assertEqual(result[0].count_formation_enrollments, 1)

    def test_count_learning_unit_enrollments(self):
        LearningUnitEnrollmentFactory(
            offer_enrollment=OfferEnrollmentFactory(education_group_year=self.education_group_year),
            learning_unit_year=self.learning_unit_year
        )
        result = find_with_enrollments_count(self.learning_unit_year)
        self.assertEqual(result[0].count_learning_unit_enrollments, 1)

    def test_ordered_by_acronym(self):
        group_1 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='XDRT1234'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        group_2 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='BMED1000'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        group_3 = GroupElementYearFactory(parent=EducationGroupYearFactory(acronym='LDROI1001'),
                                          child_branch=None,
                                          child_leaf=self.learning_unit_year)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year,
                                      offer_enrollment__education_group_year=group_1.parent)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year,
                                      offer_enrollment__education_group_year=group_2.parent)
        LearningUnitEnrollmentFactory(learning_unit_year=self.learning_unit_year,
                                      offer_enrollment__education_group_year=group_3.parent)

        result = find_with_enrollments_count(self.learning_unit_year)
        expected_list_order = [group_2.parent, group_3.parent, group_1.parent]
        self.assertEqual(list(result), expected_list_order)


class EducationGroupYearVerboseTest(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()

    def test_verbose_duration_case_no_empty_property(self):
        self.education_group_year.duration = 1
        self.education_group_year.duration_unit = duration_unit.QUADRIMESTER

        expected = '{} {}'.format(1, _(duration_unit.QUADRIMESTER))
        self.assertEqual(self.education_group_year.verbose_duration, expected)

    def test_verbose_duration_case_no_duration(self):
        self.education_group_year.duration = None
        self.education_group_year.duration_unit = duration_unit.QUADRIMESTER

        expected = ''
        self.assertEqual(self.education_group_year.verbose_duration, expected)

    def test_verbose_duration_case_no_duration_unit(self):
        self.education_group_year.duration = 1
        self.education_group_year.duration_unit = None

        expected = ''
        self.assertEqual(self.education_group_year.verbose_duration, expected)
