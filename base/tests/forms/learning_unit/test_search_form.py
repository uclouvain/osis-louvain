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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.http import QueryDict
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.search_form import filter_is_borrowed_learning_unit_year, LearningUnitSearchForm, LearningUnitYearForm
from base.models.enums import entity_container_year_link_type, entity_type, learning_container_year_types
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.offer_year_entity import OfferYearEntity
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.forms.search.search_form import get_research_criteria


class TestSearchForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_year = datetime.date.today().year
        cls.academic_years = GenerateAcademicYear(current_year - 2, current_year + 2).academic_years

    def test_get_research_criteria(self):
        data = QueryDict(mutable=True)
        data.update({
            "requirement_entity_acronym": "info",
            "tutor": "Jean Marcel",
            "academic_year_id": str(self.academic_years[0].id),
        })
        form = LearningUnitSearchForm(data)
        self.assertTrue(form.is_valid())
        expected_research_criteria = [(_('Ac yr.'), self.academic_years[0]),
                                      (_('Req. Entity'), "INFO"),
                                      (_('Tutor'), "Jean Marcel")]
        actual_research_criteria = get_research_criteria(form)
        self.assertListEqual(expected_research_criteria, actual_research_criteria)

    def test_get_research_criteria_with_choice_field(self):
        data = QueryDict(mutable=True)
        data.update({
            "academic_year_id": str(self.academic_years[0].id),
            "container_type": learning_container_year_types.COURSE
        })
        form = LearningUnitYearForm(data)
        self.assertTrue(form.is_valid())
        expected_research_criteria = [(_('Ac yr.'), self.academic_years[0]),
                                      (_('type'), _("Course"))]
        actual_research_criteria = get_research_criteria(form)
        self.assertListEqual(expected_research_criteria, actual_research_criteria)


class TestFilterIsBorrowedLearningUnitYear(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()

        cls.luys_not_in_education_group = [
            LearningUnitYearFactory(academic_year=cls.academic_year,
                                    learning_container_year__academic_year=cls.academic_year) for _ in range(3)
        ]

        cls.luys_with_same_entity_as_education_group = [
            generate_learning_unit_year_with_associated_education_group(cls.academic_year)
        ]

        cls.luys_in_same_faculty_as_education_group = [
            generate_learning_unit_year_with_associated_education_group(cls.academic_year, same_entity=False)
            for _ in range(3)
        ]

        cls.luys_in_different_faculty_than_education_group = [
            generate_learning_unit_year_with_associated_education_group(cls.academic_year, same_faculty=False)
            for _ in range(3)
        ]

    def test_empty_queryset(self):
        empty_qs = LearningUnitYear.objects.none()
        result = list(filter_is_borrowed_learning_unit_year(empty_qs, self.academic_year.start_date))
        self.assertFalse(result)

    def test_with_learning_unit_years_not_used_in_any_education_group(self):
        self.assert_filter_borrowed_luys_returns_empty_qs(self.luys_not_in_education_group)

    def test_with_learning_unit_years_when_requirement_entity_same_as_education_group(self):
        self.assert_filter_borrowed_luys_returns_empty_qs(self.luys_with_same_entity_as_education_group)

    def test_with_learning_unit_years_when_entity_for_luy_and_education_group_in_same_faculty(self):
        self.assert_filter_borrowed_luys_returns_empty_qs(self.luys_in_same_faculty_as_education_group)

    def test_with_learning_unit_when_entity_for_luy_and_education_group_in_different_faculty(self):
        qs = LearningUnitYear.objects.filter(
            pk__in=[luy.pk for luy in self.luys_in_different_faculty_than_education_group]
        )
        result = list(filter_is_borrowed_learning_unit_year(qs, self.academic_year.start_date))
        self.assertCountEqual(result, self.luys_in_different_faculty_than_education_group)

    def test_with_faculty_borrowing_set(self):
        qs = LearningUnitYear.objects.filter(
            pk__in=[luy.pk for luy in self.luys_in_different_faculty_than_education_group]
        )
        group = GroupElementYear.objects.get(child_leaf=self.luys_in_different_faculty_than_education_group[0])
        entity = OfferYearEntity.objects.get(education_group_year=group.parent).entity
        result = list(filter_is_borrowed_learning_unit_year(qs, self.academic_year.start_date,
                                                            faculty_borrowing=entity.id))
        self.assertCountEqual(result, self.luys_in_different_faculty_than_education_group[:1])

    def assert_filter_borrowed_luys_returns_empty_qs(self, learning_unit_years):
        qs = LearningUnitYear.objects.filter(pk__in=[luy.pk for luy in learning_unit_years])
        result = list(filter_is_borrowed_learning_unit_year(qs, self.academic_year.start_date))
        self.assertFalse(result)


def generate_learning_unit_year_with_associated_education_group(academic_year, same_faculty=True, same_entity=True):
    luy = LearningUnitYearFactory(academic_year=academic_year, learning_container_year__academic_year=academic_year)

    entity_container_year = EntityContainerYearFactory(learning_container_year=luy.learning_container_year,
                                                       type=entity_container_year_link_type.REQUIREMENT_ENTITY)

    entity_version = EntityVersionFactory(entity=entity_container_year.entity,
                                          entity_type=entity_type.SCHOOL)
    parent_entity = EntityVersionFactory(entity=entity_version.parent, parent=None, entity_type=entity_type.FACULTY)

    if not same_entity:
        entity_version = parent_entity
    if not same_faculty:
        entity_version = EntityVersionFactory(entity_type=entity_type.FACULTY)

    offer_year_entity = OfferYearEntityFactory(entity=entity_version.entity,
                                               education_group_year__academic_year=academic_year)

    GroupElementYearFactory(child_branch=offer_year_entity.education_group_year, parent=None)
    GroupElementYearFactory(child_branch=None, child_leaf=luy,
                            parent=offer_year_entity.education_group_year)

    return luy
