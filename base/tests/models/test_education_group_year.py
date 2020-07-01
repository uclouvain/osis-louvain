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
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from base.models.education_group_year import search, find_with_enrollments_count
from base.models.enums import education_group_categories, duration_unit, offer_enrollment_state, education_group_types
from base.models.enums.constraint_type import CREDITS
from base.models.exceptions import MaximumOneParentAllowedException, ValidationWarning
from base.models.validation_rule import ValidationRule
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, GroupFactory, TrainingFactory, \
    string_generator
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from base.tests.factories.offer_year import OfferYearFactory
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.translated_text import TranslatedTextFactory


class EducationGroupYearTest(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.education_group_type_training = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING,
            name=education_group_types.TrainingType.BACHELOR.name
        )

        self.education_group_type_minitraining = EducationGroupTypeFactory(minitraining=True)
        self.education_group_type_group = EducationGroupTypeFactory(group=True)

        self.education_group_type_finality = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING,
            name=education_group_types.TrainingType.MASTER_MD_120.name
        )

        self.education_group_year_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_training
        )
        self.education_group_year_2 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_minitraining
        )
        self.education_group_year_3 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_training
        )
        self.education_group_year_4 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_group
        )
        self.education_group_year_5 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_group
        )
        self.education_group_year_6 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_training
        )
        self.education_group_year_MD = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_finality,
            title="Complete title",
            partial_title="Partial title",
            title_english="Complete title in English",
            partial_title_english="Partial title in English"
        )
        self.education_group_year_MD_no_partial_title = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=self.education_group_type_finality,
            partial_title="",
            partial_title_english="",
        )

        self.educ_group_year_domain = EducationGroupYearDomainFactory(education_group_year=self.education_group_year_2)

        self.entity_version_admin = EntityVersionFactory(
            entity=self.education_group_year_2.administration_entity,
            start_date=self.education_group_year_2.academic_year.start_date,
            parent=None
        )

        self.offer_year_3 = OfferYearFactory(academic_year=self.academic_year)

        self.entity_version_management = EntityVersionFactory(
            entity=self.education_group_year_3.management_entity,
            start_date=self.education_group_year_3.academic_year.start_date,
            parent=None
        )

        self.group_element_year_4 = GroupElementYearFactory(
            parent=self.education_group_year_3,
            child_branch=self.education_group_year_1
        )
        self.group_element_year_5 = GroupElementYearFactory(
            parent=self.education_group_year_6,
            child_branch=self.education_group_year_1
        )

    def test_verbose_type(self):
        type_of_egt = self.education_group_year_1.education_group_type.get_name_display()
        self.assertEqual(type_of_egt, self.education_group_year_1.verbose_type)

    def test_verbose_credit(self):
        verbose__waiting = "{} ({} {})".format(
            self.education_group_year_1.title, self.education_group_year_1.credits, _("credits")
        )
        self.assertEqual(self.education_group_year_1.verbose_credit, verbose__waiting)

    def test_search(self):
        result = search(id=[self.education_group_year_1.id, self.education_group_year_2.id])
        self.assertEqual(len(result), 2)

        result = search(education_group_type=self.education_group_year_2.education_group_type)
        self.assertEqual(result.first().education_group_type,
                         self.education_group_year_2.education_group_type)

        result = search(education_group_type=[self.education_group_type_training,
                                              self.education_group_type_minitraining])
        self.assertEqual(len(result), 4)

        OfferEnrollmentFactory(education_group_year=self.education_group_year_2,
                               enrollment_state=offer_enrollment_state.SUBSCRIBED)
        OfferEnrollmentFactory(education_group_year=self.education_group_year_2,
                               enrollment_state=offer_enrollment_state.PENDING)
        result = search(enrollment_states=[offer_enrollment_state.SUBSCRIBED])
        self.assertEqual(len(result), 1)

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

    def test_parent_by_training(self):
        parent_by_training = self.education_group_year_3.is_training()
        self.assertTrue(parent_by_training)

        parent_by_training = self.education_group_year_2.parent_by_training()
        self.assertIsNone(parent_by_training)

        with self.assertRaises(MaximumOneParentAllowedException):
            self.education_group_year_1.parent_by_training()

        group = GroupFactory(academic_year=self.academic_year)
        GroupElementYearFactory(child_branch=group, parent=self.education_group_year_2)
        self.assertIsNone(group.parent_by_training())

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
                self.education_group_year_6
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
                self.education_group_year_6,
            ]
        )

    def test_is_mini_training(self):
        self.assertFalse(self.education_group_year_1.is_mini_training())
        self.assertTrue(self.education_group_year_2.is_mini_training())
        self.assertFalse(self.education_group_year_3.is_mini_training())
        self.assertFalse(self.education_group_year_4.is_mini_training())
        self.assertFalse(self.education_group_year_5.is_mini_training())
        self.assertFalse(self.education_group_year_6.is_mini_training())

    @override_settings(LANGUAGES=[('fr-be', 'French'), ], LANGUAGE_CODE='fr-be')
    def test_verbose_title_fr(self):
        self.assertEqual(self.education_group_year_MD.verbose_title, self.education_group_year_MD.partial_title)
        self.assertEqual(self.education_group_year_1.verbose_title, self.education_group_year_1.title)

    @override_settings(LANGUAGES=[('en', 'English'), ], LANGUAGE_CODE='en')
    def test_verbose_title_en(self):
        self.assertEqual(self.education_group_year_MD.verbose_title, self.education_group_year_MD.partial_title_english)
        self.assertEqual(self.education_group_year_1.verbose_title,
                         self.education_group_year_1.title_english or self.education_group_year_1.title)

    @override_settings(LANGUAGES=[('fr-be', 'French'), ], LANGUAGE_CODE='fr-be')
    def test_verbose_title_fr_partial_title_empty(self):
        self.assertEqual(self.education_group_year_MD_no_partial_title.verbose_title, "")

    @override_settings(LANGUAGES=[('en', 'English'), ], LANGUAGE_CODE='en')
    def test_verbose_title_en_partial_title_empty(self):
        self.assertEqual(self.education_group_year_MD_no_partial_title.verbose_title, "")


class EducationGroupYearCleanTest(TestCase):
    def test_clean_constraint_both_value_set_case_no_errors(self):
        e = EducationGroupYearFactory(min_constraint=12, max_constraint=20, constraint_type=CREDITS)
        try:
            e.clean()
        except ValidationError:
            self.fail()

    def test_clean_constraint_only_one_value_set_case_no_errors(self):
        e = EducationGroupYearFactory(min_constraint=12, max_constraint=None, constraint_type=CREDITS)
        try:
            e.clean()
        except ValidationError:
            self.fail()

        e.min_constraint = None
        e.max_constraint = 12
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

    @override_settings(YEAR_LIMIT_EDG_MODIFICATION=2016)
    def test_clean_case_academic_year_before_settings(self):
        e = EducationGroupYearFactory(academic_year__year=2015)

        with self.assertRaises(ValidationError) as context_error:
            e.clean()

        self.assertListEqual(
            context_error.exception.messages,
            [_("You cannot create/update an education group before %(limit_year)s") % {
                "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION
            }]
        )


class TestCleanPartialAcronym(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.previous_acy, cls.current_acy, cls.next_acy = AcademicYearFactory.produce(number_past=1, number_future=1)
        cls.partial_acronym = 'CODE'
        ValidationRule(field_reference='base_educationgroupyear.partial_acronym.osis.education_group_type_2M180',
                       regex_rule='^([LWMBlwmb])([A-Za-z]{2,4})([0-9]{3})([Mm])$').save()
        ValidationRule(field_reference='base_educationgroupyear.partial_acronym.osis.education_group_type_2M1',
                       regex_rule='^([LWMBlwmb])([A-Za-z]{2,4})([0-9]{3})([Uu])$').save()
        ValidationRule(field_reference='base_educationgroupyear.partial_acronym.osis.education_group_type_3DP',
                       regex_rule='^([LWMBlwmb])([A-Za-z]{2,4})([0-9]{3})([Dd])$').save()

    def test_raise_validation_error_when_partial_acronym_exists_in_present_or_future(self):
        for acy in (self.current_acy, self.next_acy):
            with self.subTest(acy=acy):
                EducationGroupYearFactory(partial_acronym=self.partial_acronym, academic_year=acy)
                e = EducationGroupYearFactory.build(partial_acronym=self.partial_acronym,
                                                    academic_year=self.current_acy)
                with self.assertRaises(ValidationError):
                    e.clean_partial_acronym()

    def test_when_partial_acronym_existed_in_past(self):
        EducationGroupYearFactory(partial_acronym=self.partial_acronym, academic_year=self.previous_acy)
        e = EducationGroupYearFactory.build(partial_acronym=self.partial_acronym, academic_year=self.current_acy)
        e.clean_partial_acronym()

    def test_raise_validation_warning_when_partial_acronym_existed_in_past_and_raise_warnings_set_to_true(self):
        EducationGroupYearFactory(partial_acronym=self.partial_acronym, academic_year=self.previous_acy)
        e = EducationGroupYearFactory.build(partial_acronym=self.partial_acronym, academic_year=self.current_acy)
        with self.assertRaises(ValidationWarning):
            e.clean_partial_acronym(raise_warnings=True)

    def test_raise_validation_partial_acronym_invalid(self):
        random_partial_acronym = string_generator()
        external_ids = ['osis.education_group_type_2M180',
                        'osis.education_group_type_2M1',
                        'osis.education_group_type_3DP']
        for ext_id in external_ids:
            with self.subTest(type=ext_id):
                e = TrainingFactory(partial_acronym=random_partial_acronym,
                                    academic_year=self.current_acy,
                                    education_group_type__external_id=ext_id)
                with self.assertRaises(ValidationError):
                    e.clean_partial_acronym()

    def test_when_partial_acronym_not_exists(self):
        EducationGroupYearFactory(partial_acronym='CODE1')
        e = EducationGroupYearFactory.build(partial_acronym='CODE2')
        e.clean_partial_acronym()


class TestCleanAcronym(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.previous_acy, cls.current_acy, cls.next_acy = AcademicYearFactory.produce(number_past=1, number_future=1)
        cls.acronym = 'SIGLE'
        ValidationRule(field_reference='base_educationgroupyear.acronym.osis.education_group_type_2M180',
                       regex_rule='^([A-Za-z]{2,4})(2)([Mm])$').save()
        ValidationRule(field_reference='base_educationgroupyear.acronym.osis.education_group_type_2M1',
                       regex_rule='^([A-Za-z]{2,4})(2)([Mm])(1)$').save()
        ValidationRule(field_reference='base_educationgroupyear.acronym.osis.education_group_type_3DP',
                       regex_rule='^([A-Za-z]{2,4})(3)([Dd])([Pp])$').save()

    def test_raise_validation_error_when_acronym_exists_in_present_or_future(self):
        for acy in (self.current_acy, self.next_acy):
            with self.subTest(acy=acy):
                EducationGroupYearFactory(acronym=self.acronym, academic_year=acy)
                e = EducationGroupYearFactory.build(acronym=self.acronym, academic_year=self.current_acy)
                with self.assertRaises(ValidationError):
                    e.clean_acronym()

    def test_no_validation_error_when_group_reuse_acronym_of_another_group(self):
        for acy in (self.current_acy, self.next_acy):
            with self.subTest(acy=acy):
                GroupFactory(acronym=self.acronym, academic_year=acy)
                e = GroupFactory.build(acronym=self.acronym, academic_year=self.current_acy)
                e.clean_acronym()

    def test_when_acronym_existed_in_past(self):
        EducationGroupYearFactory(acronym=self.acronym, academic_year=self.previous_acy)
        e = EducationGroupYearFactory.build(acronym=self.acronym, academic_year=self.current_acy)
        e.clean_acronym()

    def test_raise_validation_warning_when_acronym_existed_in_past_and_raise_warning_set_to_true(self):
        EducationGroupYearFactory(acronym=self.acronym, academic_year=self.previous_acy)
        e = EducationGroupYearFactory.build(acronym=self.acronym, academic_year=self.current_acy)
        with self.assertRaises(ValidationWarning):
            e.clean_acronym(raise_warnings=True)

    def test_raise_validation_acronym_invalid(self):
        random_acronym = string_generator()
        external_ids = ['osis.education_group_type_2M180',
                        'osis.education_group_type_2M1',
                        'osis.education_group_type_3DP']
        for ext_id in external_ids:
            with self.subTest(type=ext_id):
                e = TrainingFactory(acronym=random_acronym,
                                    academic_year=self.current_acy,
                                    education_group_type__external_id=ext_id)
                with self.assertRaises(ValidationError):
                    e.clean_acronym()

    def test_when_acronym_not_exists(self):
        EducationGroupYearFactory(acronym='CODE1')
        e = EducationGroupYearFactory.build(acronym='CODE2')
        e.clean_acronym()


class TestFindWithEnrollmentsCount(TestCase):
    """Unit tests on find_with_enrollments_count()"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.learning_unit_year = LearningUnitYearFactory(academic_year=cls.current_academic_year)
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.current_academic_year)
        GroupElementYearFactory(parent=cls.education_group_year,
                                child_branch=None,
                                child_leaf=cls.learning_unit_year)

    def test_without_learning_unit_enrollment_but_with_offer_enrollments(self):
        OfferEnrollmentFactory(education_group_year=self.education_group_year)
        result = find_with_enrollments_count(self.learning_unit_year)
        self.assertEqual(list(result), [])

    def test_with_learning_unit_enrollment_and_with_offer_enrollments(self):
        enrol_not_in_education_group = LearningUnitEnrollmentFactory(
            learning_unit_year=LearningUnitYearFactory(),
            offer_enrollment=OfferEnrollmentFactory(enrollment_state=offer_enrollment_state.SUBSCRIBED)
        )
        result = find_with_enrollments_count(enrol_not_in_education_group.learning_unit_year)
        self.assertEqual(result[0].count_learning_unit_enrollments, 1)
        self.assertEqual(result[0].count_formation_enrollments, 1)

    def test_count_formation_enrollments_with_pending_enrollment(self):
        luy = LearningUnitYearFactory()
        edy = EducationGroupYearFactory()
        for k in dict(offer_enrollment_state.STATES):
            LearningUnitEnrollmentFactory(
                learning_unit_year=luy,
                offer_enrollment=OfferEnrollmentFactory(
                    enrollment_state=k,
                    education_group_year=edy),
            )
        result = find_with_enrollments_count(luy)
        self.assertEqual(result[0].count_learning_unit_enrollments, 5)
        self.assertEqual(result[0].count_formation_enrollments, 2)

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
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()

    def test_verbose_duration_case_no_empty_property(self):
        self.education_group_year.duration = 1
        self.education_group_year.duration_unit = duration_unit.QUADRIMESTER

        expected = '{} {}'.format(1, _(dict(duration_unit.DURATION_UNIT).get(duration_unit.QUADRIMESTER)))
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


class EducationGroupYearTypeTest(TestCase):
    def test_type_property(self):
        education_group_year = EducationGroupYearFactory()
        self.assertEqual(education_group_year.type, education_group_year.education_group_type.name)


class EducationGroupYearDeleteCms(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory()
        cls.translated_text = TranslatedTextFactory(entity=entity_name.OFFER_YEAR,
                                                    reference=cls.education_group_year.id)

        cls.education_group_year_no_cms = EducationGroupYearFactory()

    def test_delete_education_group_yr_and_cms(self):
        egy_id = self.education_group_year.id
        self.education_group_year.delete()
        self.assertCountEqual(list(TranslatedText.objects.filter(id=self.translated_text.id)), [])
        self.assertCountEqual(list(TranslatedText.objects.filter(reference=egy_id)), [])

    def test_delete_education_group_yr_without_cms(self):
        egy_id = self.education_group_year_no_cms.id
        self.education_group_year_no_cms.delete()
        self.assertCountEqual(list(TranslatedText.objects.filter(reference=egy_id)), [])
