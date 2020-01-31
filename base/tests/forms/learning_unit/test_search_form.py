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
import datetime

from django.http import QueryDict
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.forms.learning_unit.search.borrowed import BorrowedLearningUnitSearch, filter_is_borrowed_learning_unit_year
from base.forms.learning_unit.search.educational_information import LearningUnitDescriptionFicheFilter
from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.forms.learning_unit.search.simple import LearningUnitFilter, MOBILITY
from base.forms.search.search_form import get_research_criteria
from base.models.enums import entity_type, learning_container_year_types
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.offer_year_entity import OfferYearEntity
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from reference.tests.factories.country import CountryFactory

CINEY = "Ciney"
NAMUR = "Namur"
TITLE = "Title luy"


class TestSearchForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        current_year = datetime.date.today().year
        start_year = AcademicYearFactory(year=current_year - 2)
        end_year = AcademicYearFactory(year=current_year + 2)
        cls.academic_years = GenerateAcademicYear(start_year, end_year).academic_years
        ExternalLearningUnitYearFactory(
            learning_unit_year__academic_year=cls.academic_years[0],
            learning_unit_year__learning_container_year__container_type=learning_container_year_types.EXTERNAL,
            mobility=True,
            co_graduation=False,
        )

    def setUp(self):
        self.data = QueryDict(mutable=True)

    def test_get_research_criteria(self):
        self.data.update({
            "requirement_entity": "INFO",
            "tutor": "Jean Marcel",
            "academic_year": str(self.academic_years[0].id),
        })
        form = LearningUnitFilter(self.data).form
        self.assertTrue(form.is_valid())
        expected_research_criteria = [(_('Ac yr.'), self.academic_years[0]),
                                      (_('Req. Entity'), "INFO"),
                                      (_('Tutor'), "Jean Marcel")]
        actual_research_criteria = get_research_criteria(form)
        self.assertListEqual(expected_research_criteria, actual_research_criteria)

    def test_get_research_criteria_with_choice_field(self):
        self.data.update({
            "academic_year": str(self.academic_years[0].id),
            "container_type": learning_container_year_types.COURSE
        })
        form = LearningUnitFilter(self.data).form
        self.assertTrue(form.is_valid())
        expected_research_criteria = [(_('Ac yr.'), self.academic_years[0]),
                                      (_('Type'), _("Course"))]
        actual_research_criteria = get_research_criteria(form)
        self.assertListEqual(expected_research_criteria, actual_research_criteria)

    def test_search_on_external_mobility(self):
        self.data.update({
            "academic_year_id": str(self.academic_years[0].id),
            "container_type": MOBILITY
        })
        form = LearningUnitFilter(self.data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_queryset().count(), 1)

    def test_search_on_external_cograduation(self):
        self.data.update({
            "academic_year_id": str(self.academic_years[0].id),
            "container_type": learning_container_year_types.EXTERNAL
        })
        ExternalLearningUnitYearFactory(
            learning_unit_year__academic_year=self.academic_years[0],
            learning_unit_year__learning_container_year__container_type=learning_container_year_types.EXTERNAL,
            mobility=False,
            co_graduation=True,
        )
        learning_unit_filter = LearningUnitFilter(self.data)
        self.assertTrue(learning_unit_filter.is_valid())
        self.assertEqual(learning_unit_filter.qs.count(), 1)

    def test_search_on_external_title(self):
        ExternalLearningUnitYearFactory(
            learning_unit_year__academic_year=self.academic_years[0],
            learning_unit_year__learning_container_year__container_type=learning_container_year_types.EXTERNAL,
            learning_unit_year__learning_container_year__common_title=TITLE,
        )

        self.data.update({
            "academic_year_id": str(self.academic_years[0].id),
            "container_type": learning_container_year_types.EXTERNAL,
            "title": TITLE
        })

        learning_unit_filter = ExternalLearningUnitFilter(self.data)
        self.assertTrue(learning_unit_filter.is_valid())
        self.assertEqual(learning_unit_filter.qs.count(), 1)

    def test_dropdown_init(self):
        country = CountryFactory()

        organization_1 = OrganizationFactory(name="organization 1")
        organization_2 = OrganizationFactory(name="organization 2")
        organization_3 = OrganizationFactory(name="organization 3")

        OrganizationAddressFactory(organization=organization_1, country=country, city=NAMUR)
        OrganizationAddressFactory(organization=organization_2, country=country, city=NAMUR)

        OrganizationAddressFactory(organization=organization_3, country=country, city=CINEY)

        CampusFactory(organization=organization_1)
        campus_2 = CampusFactory(organization=organization_1)
        campus_3 = CampusFactory(organization=organization_2)

        form = ExternalLearningUnitFilter({'city': NAMUR, 'country': country, "campus": campus_2}).form
        campus_form_choices = list(form.fields["campus"].choices)
        self.assertEqual(campus_form_choices[0], ('', '---------'))
        self.assertEqual(campus_form_choices[1][1], 'organization 1')
        self.assertEqual(campus_form_choices[2], (campus_3.id, 'organization 2'))

        city_form_choices = list(form.fields['city'].choices)
        self.assertEqual(city_form_choices,
                         [('', '---------'), (CINEY, CINEY), (NAMUR, NAMUR)])

    def test_initial_value_learning_unit_filter_with_entity_subordinated(self):
        lu_filter = LearningUnitFilter()
        self.assertTrue(lu_filter.form.fields['with_entity_subordinated'].initial)

    def test_search_on_title(self):
        LearningUnitYearFactory(
            academic_year=self.academic_years[0],
            learning_container_year__common_title=TITLE,
        )

        self.data.update({
            "academic_year_id": str(self.academic_years[0].id),
            "title": TITLE
        })

        learning_unit_filter = LearningUnitFilter(self.data)
        self.assertTrue(learning_unit_filter.is_valid())
        self.assertEqual(learning_unit_filter.qs.count(), 1)


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
        self.assertCountEqual(result,   [obj.id for obj in self.luys_in_different_faculty_than_education_group])

    def test_with_faculty_borrowing_set(self):
        qs = LearningUnitYear.objects.filter(
            pk__in=[luy.pk for luy in self.luys_in_different_faculty_than_education_group]
        )

        group = GroupElementYear.objects.get(child_leaf=self.luys_in_different_faculty_than_education_group[0])
        entity = OfferYearEntity.objects.get(education_group_year=group.parent).entity
        result = list(filter_is_borrowed_learning_unit_year(qs, self.academic_year.start_date,
                                                            faculty_borrowing=entity.id))
        self.assertCountEqual(result, [obj.id for obj in self.luys_in_different_faculty_than_education_group[:1]])
        acronyms = [entity.most_recent_acronym, entity.most_recent_acronym.lower()]
        for acronym in acronyms:
            with self.subTest(msg=acronym):
                data = {
                    "academic_year": self.academic_year.id,
                    "faculty_borrowing_acronym": acronym
                }

                borrowed_filter = BorrowedLearningUnitSearch(data)

                borrowed_filter.is_valid()
                results = list(borrowed_filter.qs)

                self.assertEqual(results[0].id, self.luys_in_different_faculty_than_education_group[:1][0].id)

    def test_with_faculty_borrowing_set_and_no_entity_version(self):
        group = GroupElementYear.objects.get(child_leaf=self.luys_in_different_faculty_than_education_group[0])
        data = {
            "academic_year": self.academic_year.id,
            "faculty_borrowing_acronym": group.parent.acronym
        }

        borrowed_filter = BorrowedLearningUnitSearch(data)

        borrowed_filter.is_valid()
        result = list(borrowed_filter.qs)
        self.assertEqual(result, [])

    def assert_filter_borrowed_luys_returns_empty_qs(self, learning_unit_years):
        qs = LearningUnitYear.objects.filter(pk__in=[luy.pk for luy in learning_unit_years])
        result = list(filter_is_borrowed_learning_unit_year(qs, self.academic_year.start_date))
        self.assertFalse(result)


def generate_learning_unit_year_with_associated_education_group(academic_year, same_faculty=True, same_entity=True):
    luy = LearningUnitYearFactory(
        academic_year=academic_year,
        learning_container_year__academic_year=academic_year,
        learning_container_year__requirement_entity=EntityFactory()
    )

    entity_version = EntityVersionFactory(entity=luy.learning_container_year.requirement_entity,
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


class TestFilterDescriptiveficheLearningUnitYear(TestCase):
    def test_init_with_entity_subordinated_search_form(self):
        form = LearningUnitDescriptionFicheFilter(None).form
        self.assertTrue(form.fields['with_entity_subordinated'].initial)
