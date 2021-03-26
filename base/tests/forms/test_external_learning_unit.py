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
from django.test.utils import override_settings

from base.forms.learning_unit.external_learning_unit import ExternalLearningUnitBaseForm, \
    LearningContainerYearExternalModelForm, CograduationExternalLearningUnitModelForm, \
    LearningUnitYearForExternalModelForm, ExternalPartimForm
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningUnitModelForm
from base.forms.learning_unit.search.external import ExternalLearningUnitFilter
from base.models.entity_version import EntityVersion
from base.models.enums import learning_unit_year_subtypes
from base.models.enums import organization_type
from base.models.enums.learning_container_year_types import EXTERNAL
from base.models.enums.learning_unit_external_sites import LearningUnitExternalSite
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_calendar import generate_learning_unit_edition_calendars
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.entities import create_entities_hierarchy
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.entity_version_address import MainRootEntityVersionAddressFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFullFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from learning_unit.tests.factories.central_manager import CentralManagerFactory
from reference.tests.factories.language import FrenchLanguageFactory

YEAR_LIMIT_LUE_MODIFICATION = 2018
NAMUR = 'Namur'


def get_valid_external_learning_unit_form_data(academic_year, learning_unit_year=None, entity=None):
    create_entities_hierarchy(root_entity=entity)
    requirement_entity_version = EntityVersion.objects.filter(entity=entity.id).first()
    organization = OrganizationFactory(type=organization_type.MAIN)
    campus = CampusFactory(organization=organization)
    language = FrenchLanguageFactory()

    if not learning_unit_year:
        container_year = LearningContainerYearFactory(
            academic_year=academic_year,
            requirement_entity=None,
            allocation_entity=None
        )
        learning_unit_year = LearningUnitYearFactory.build(
            acronym='EOSIS1111',
            academic_year=academic_year,
            learning_container_year=container_year,
            subtype=learning_unit_year_subtypes.FULL,
            campus=campus,
            language=language
        )
    return {
        # Learning unit year data model form
        'acronym_0': learning_unit_year.acronym[0],
        'acronym_1': learning_unit_year.acronym[1:],
        'acronym_2': "A",
        'academic_year': learning_unit_year.academic_year.id,
        'specific_title': learning_unit_year.specific_title,
        'specific_title_english': learning_unit_year.specific_title_english,
        'credits': learning_unit_year.credits,
        'status': learning_unit_year.status,
        'campus': learning_unit_year.campus.id,
        'language': learning_unit_year.language.pk,
        'periodicity': learning_unit_year.periodicity,
        'faculty_remark': learning_unit_year.faculty_remark,

        # Learning container year data model form
        'common_title': learning_unit_year.learning_container_year.common_title,
        'common_title_english': learning_unit_year.learning_container_year.common_title_english,
        'is_vacant': learning_unit_year.learning_container_year.is_vacant,

        # External learning unit model form
        'requirement_entity': requirement_entity_version.id,
        'allocation_entity': requirement_entity_version.id,
        'external_acronym': 'Gorzyne',
        'external_credits': '5',

        # Learning component year data model form
        'component-TOTAL_FORMS': '2',
        'component-INITIAL_FORMS': '0',
        'component-MAX_NUM_FORMS': '2',
        'component-0-hourly_volume_total_annual': 20,
        'component-0-hourly_volume_partial_q1': 10,
        'component-0-hourly_volume_partial_q2': 10,
        'component-0-planned_classes': 1,
        'component-1-hourly_volume_total_annual': 20,
        'component-1-hourly_volume_partial_q1': 10,
        'component-1-hourly_volume_partial_q2': 10,
        'component-1-planned_classes': 1,
    }


class TestExternalLearningUnitForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        starting_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION)
        end_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION + 6)
        cls.academic_years = GenerateAcademicYear(starting_year, end_year).academic_years
        cls.academic_year = cls.academic_years[1]
        cls.language = FrenchLanguageFactory()
        cls.entity = MainEntityVersionFactory().entity
        cls.manager = CentralManagerFactory(entity=cls.entity, with_child=True)
        cls.person = cls.manager.person
        generate_learning_unit_edition_calendars(cls.academic_years)

    def setUp(self):
        pass

    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=YEAR_LIMIT_LUE_MODIFICATION)
    def test_external_learning_unit_form_init(self):
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year)

        context = form.get_context()
        self.assertEqual(context['subtype'], FULL)
        self.assertIsInstance(context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(context['learning_unit_year_form'], LearningUnitYearModelForm)
        self.assertIsInstance(context['learning_container_year_form'], LearningContainerYearExternalModelForm)
        self.assertIsInstance(context['learning_unit_external_form'], CograduationExternalLearningUnitModelForm)

    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=YEAR_LIMIT_LUE_MODIFICATION)
    def test_external_learning_unit_form_is_valid(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, entity=self.entity)
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year, data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_external_learning_unit_form_save(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, entity=self.entity)
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year, data=data,
                                            start_year=self.academic_year)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save()

        self.assertIsInstance(luy, LearningUnitYear)
        self.assertEqual(luy.learning_container_year.container_type, EXTERNAL)
        self.assertEqual(luy.acronym[0], 'E')
        self.assertEqual(luy.externallearningunityear.author, self.person)
        self.assertEqual(luy.learning_unit.start_year, self.academic_year)

    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=YEAR_LIMIT_LUE_MODIFICATION)
    def test_creation(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, entity=self.entity)
        form = LearningUnitYearForExternalModelForm(
            person=self.person, data=data, subtype=learning_unit_year_subtypes.FULL, initial={}
        )
        self.assertCountEqual(list(form.fields['academic_year'].queryset), self.academic_years[1:])


class TestExternalPartimForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = CentralManagerFactory(entity=EntityWithVersionFactory(), with_child=True)
        cls.person = cls.manager.person

        starting_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION)
        end_year = AcademicYearFactory(year=YEAR_LIMIT_LUE_MODIFICATION + 6)
        academic_years = GenerateAcademicYear(starting_year, end_year).academic_years
        cls.academic_year = academic_years[1]
        cls.language = FrenchLanguageFactory()
        organization = OrganizationFactory(type=organization_type.MAIN)
        cls.campus = CampusFactory(organization=organization)
        cls.language = FrenchLanguageFactory()
        cls.container_year = LearningContainerYearFactory(
            academic_year=cls.academic_year,
            container_type=EXTERNAL,
            requirement_entity=None,
            allocation_entity=None
        )
        cls.learning_unit = LearningUnitFactory(start_year=cls.academic_year)
        generate_learning_unit_edition_calendars(academic_years)

    def setUp(self):
        self.learning_unit_year = LearningUnitYearFactory(
            acronym='EOSIS1111',
            academic_year=self.academic_year,
            learning_unit=self.learning_unit,
            learning_container_year=self.container_year,
            subtype=learning_unit_year_subtypes.FULL,
            campus=self.campus,
            language=self.language,
            internship_subtype=None
        )

    def test_external_learning_unit_form_init(self):
        form = ExternalPartimForm(person=self.person, academic_year=self.academic_year,
                                  learning_unit_full_instance=self.learning_unit_year.learning_unit)

        context = form.get_context()
        self.assertEqual(context['subtype'], PARTIM)
        self.assertIsInstance(context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(context['learning_unit_year_form'], LearningUnitYearModelForm)
        self.assertIsInstance(context['learning_container_year_form'], LearningContainerYearExternalModelForm)
        self.assertIsInstance(context['learning_unit_external_form'], CograduationExternalLearningUnitModelForm)

    def test_external_learning_unit_form_is_valid(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, entity=self.manager.entity)
        form = ExternalPartimForm(person=self.person, academic_year=self.academic_year, data=data,
                                  learning_unit_full_instance=self.learning_unit_year.learning_unit)
        self.assertTrue(form.is_valid(), form.errors)

    def test_external_learning_unit_form_save(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, entity=self.manager.entity)
        form = ExternalPartimForm(person=self.person, academic_year=self.academic_year, data=data,
                                  start_year=self.academic_year.year,
                                  learning_unit_full_instance=self.learning_unit_year.learning_unit)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save()

        self.assertIsInstance(luy, LearningUnitYear)
        self.assertEqual(luy.learning_container_year.container_type, EXTERNAL)
        self.assertEqual(luy.acronym[0], 'E')
        self.assertEqual(luy.externallearningunityear.author, self.person)
        self.assertEqual(luy.learning_unit.start_year, self.academic_year)


class TestLearningUnitYearForExternalModelForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.academic_year = create_current_academic_year()
        cls.language = FrenchLanguageFactory()

    def test_init(self):
        campus = CampusFactory()
        address = MainRootEntityVersionAddressFactory(entity_version__entity__organization=campus.organization)

        luy = LearningUnitYearFullFactory(campus=campus)

        form = LearningUnitYearForExternalModelForm(
            person=self.person, data=None,
            subtype=FULL, instance=luy, initial={})
        self.assertEqual(form.fields["country_external_institution"].initial, address.country.pk)

    def test_fill_acronym_initial_letter_instance(self):
        luy = LearningUnitYearFullFactory(campus=CampusFactory())
        form = LearningUnitYearForExternalModelForm(
            person=self.person, data=None,
            subtype=FULL, instance=luy, initial={}
        )
        self.assertEqual(form.data['acronym_0'], luy.acronym[0])

    def test_fill_external_initial_letter_no_instance(self):
        form = LearningUnitYearForExternalModelForm(
            person=self.person, data=None,
            subtype=FULL, instance=None, initial={}
        )
        self.assertEqual(form.data['acronym_0'], LearningUnitExternalSite.E.value)


class TestExternalLearningUnitSearchForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()

        cls.organization_1 = OrganizationFactory()
        cls.be_organization_adr_city1 = MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=cls.organization_1,
            country__iso_code="BE",
            city=NAMUR
        )
        cls.external_lu_1 = ExternalLearningUnitYearFactory(
            co_graduation=True,
            learning_unit_year__academic_year=cls.academic_year,
            learning_unit_year__acronym='EDROI1001',
            learning_unit_year__campus__organization=cls.organization_1,
        )

        cls.organization_2 = OrganizationFactory()
        cls.be_organization_adr_city2 = MainRootEntityVersionAddressFactory(
            entity_version__entity__organization=cls.organization_2,
            country__iso_code="BE",
            city='Bruxelles'
        )
        cls.external_lu_2 = ExternalLearningUnitYearFactory(
            co_graduation=True,
            learning_unit_year__academic_year=cls.academic_year,
            learning_unit_year__acronym='EDROI1002',
            learning_unit_year__campus__organization=cls.organization_2,
        )

    def test_search_learning_units_on_acronym(self):
        form_data = {
            "acronym": self.external_lu_1.learning_unit_year.acronym,
        }

        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid())
        self.assertCountEqual(external_filter.qs, [self.external_lu_1.learning_unit_year])

    def test_search_learning_units_on_partial_acronym(self):
        form_data = {
            "acronym": self.external_lu_1.learning_unit_year.acronym[:5],
        }

        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid())
        self.assertCountEqual(external_filter.qs, [
            self.external_lu_1.learning_unit_year,
            self.external_lu_2.learning_unit_year
        ])

    def test_search_learning_units_by_country(self):
        form_data = {
            "country": self.external_lu_1.learning_unit_year.campus.organization.country.id,
        }

        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid(), external_filter.errors)
        self.assertCountEqual(external_filter.qs, [
            self.external_lu_1.learning_unit_year, self.external_lu_2.learning_unit_year])

    def test_search_learning_units_by_city(self):
        form_data = {
            "country": self.external_lu_1.learning_unit_year.campus.organization.country.id,
            "city": NAMUR,
        }

        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid())
        self.assertCountEqual(external_filter.qs, [self.external_lu_1.learning_unit_year])

    def test_search_learning_units_by_campus(self):
        form_data = {
            "country": self.external_lu_1.learning_unit_year.campus.organization.country.id,
            "city": NAMUR,
            "campus": self.external_lu_1.learning_unit_year.campus.id,
        }

        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid(), external_filter.errors)
        self.assertCountEqual(external_filter.qs, [self.external_lu_1.learning_unit_year])

    def test_assert_ignore_external_learning_units_of_type_mobility(self):
        original_count = LearningUnitYear.objects.filter(externallearningunityear__co_graduation=True,
                                                         externallearningunityear__mobility=False).count()
        ExternalLearningUnitYearFactory(
            learning_unit_year__academic_year=self.academic_year,
            mobility=True,
            co_graduation=False,
            learning_unit_year__acronym="XTEST1234",
        )
        form_data = {
            "academic_year": self.academic_year.id,
        }
        external_filter = ExternalLearningUnitFilter(form_data)
        self.assertTrue(external_filter.is_valid())
        self.assertEqual(external_filter.qs.count(), original_count)
