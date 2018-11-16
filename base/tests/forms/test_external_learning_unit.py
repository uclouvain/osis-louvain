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
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.external_learning_unit import ExternalLearningUnitBaseForm, \
    LearningContainerYearExternalModelForm, ExternalLearningUnitModelForm, LearningUnitYearForExternalModelForm
from base.forms.learning_unit.learning_unit_create import LearningUnitYearModelForm, \
    LearningUnitModelForm
from base.forms.learning_unit.search_form import ExternalLearningUnitYearForm
from base.models.enums import learning_unit_year_subtypes
from base.models.enums import organization_type
from base.models.enums.learning_container_year_types import EXTERNAL
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.business.entities import create_entities_hierarchy
from base.tests.factories.campus import CampusFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFullFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.organization_address import OrganizationAddressFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory

NAMEN = 'Namur'


def get_valid_external_learning_unit_form_data(academic_year, person, learning_unit_year=None):
    entities = create_entities_hierarchy()
    PersonEntityFactory(person=person, entity=entities['root_entity'], with_child=True)
    requesting_entity = entities['child_one_entity_version']
    organization = OrganizationFactory(type=organization_type.MAIN)
    campus = CampusFactory(organization=organization)
    language = LanguageFactory(code='FR')

    if not learning_unit_year:
        container_year = LearningContainerYearFactory(academic_year=academic_year)
        learning_unit_year = LearningUnitYearFactory.build(
            acronym='XOSIS1111',
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
        'academic_year': learning_unit_year.academic_year.id,
        'specific_title': learning_unit_year.specific_title,
        'specific_title_english': learning_unit_year.specific_title_english,
        'credits': learning_unit_year.credits,
        'status': learning_unit_year.status,
        'campus': learning_unit_year.campus.id,
        'language': learning_unit_year.language.pk,
        'periodicity': learning_unit_year.periodicity,

        # Learning unit data model form
        'faculty_remark': learning_unit_year.learning_unit.faculty_remark,

        # Learning container year data model form
        'common_title': learning_unit_year.learning_container_year.common_title,
        'common_title_english': learning_unit_year.learning_container_year.common_title_english,
        'is_vacant': learning_unit_year.learning_container_year.is_vacant,

        # External learning unit model form
        'requesting_entity': requesting_entity.id,
        'external_acronym': 'Gorzyne',
        'external_credits': '5',

        # Learning component year data model form
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '0',
        'form-MAX_NUM_FORMS': '2',
        'form-0-hourly_volume_total_annual': 20,
        'form-0-hourly_volume_partial_q1': 10,
        'form-0-hourly_volume_partial_q2': 10,
        'form-1-hourly_volume_total_annual': 20,
        'form-1-hourly_volume_partial_q1': 10,
        'form-1-hourly_volume_partial_q2': 10,
    }


class TestExternalLearningUnitForm(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.academic_year = create_current_academic_year()
        self.language = LanguageFactory(code='FR')

    def test_external_learning_unit_form_init(self):
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year)

        context = form.get_context()
        self.assertEqual(context['subtype'], FULL)
        self.assertIsInstance(context['learning_unit_form'], LearningUnitModelForm)
        self.assertIsInstance(context['learning_unit_year_form'], LearningUnitYearModelForm)
        self.assertIsInstance(context['learning_container_year_form'], LearningContainerYearExternalModelForm)
        self.assertIsInstance(context['learning_unit_external_form'], ExternalLearningUnitModelForm)

    def test_external_learning_unit_form_is_valid(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, self.person)
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year, data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_external_learning_unit_form_save(self):
        data = get_valid_external_learning_unit_form_data(self.academic_year, self.person)
        form = ExternalLearningUnitBaseForm(person=self.person, academic_year=self.academic_year, data=data,
                                            start_year=self.academic_year.year)
        self.assertTrue(form.is_valid(), form.errors)
        luy = form.save()

        self.assertIsInstance(luy, LearningUnitYear)
        self.assertEqual(luy.learning_container_year.container_type, EXTERNAL)
        self.assertEqual(luy.acronym[0], 'X')
        self.assertEqual(luy.externallearningunityear.author, self.person)
        self.assertEqual(luy.learning_unit.start_year, self.academic_year.year)


class TestLearningUnitYearForExternalModelForm(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.academic_year = create_current_academic_year()
        self.language = LanguageFactory(code='FR')

    def test_init(self):
        campus = CampusFactory()
        address = OrganizationAddressFactory(is_main=True, organization=campus.organization)

        luy = LearningUnitYearFullFactory(campus=campus)

        form = LearningUnitYearForExternalModelForm(
            person=self.person, data=None,
            subtype=FULL, instance=luy, initial={})
        self.assertEqual(form.initial["country"], address.country.pk)


class TestExternalLearningUnitSearchForm(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()

        self.learning_unit_year_1 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                            acronym='XLDR1001')
        self.external_lu_1 = ExternalLearningUnitYearFactory(external_acronym='XLDR1001',
                                                             learning_unit_year=self.learning_unit_year_1)
        self.learning_unit_year_2 = LearningUnitYearFactory(academic_year=self.academic_year,
                                                            acronym='XLDR1002')
        self.external_lu_2 = ExternalLearningUnitYearFactory(external_acronym='XLDR1002',
                                                             learning_unit_year=self.learning_unit_year_2)

        self.a_be_country = CountryFactory(iso_code='BE')
        self.be_organization_adr_city1 = OrganizationAddressFactory(country=self.a_be_country, city=NAMEN)
        self.be_campus_1 = CampusFactory(organization=self.be_organization_adr_city1.organization)
        self.learning_container_year = LearningContainerYearFactory(academic_year=self.academic_year)
        self.learning_unit_year_3 = LearningUnitYearFactory(learning_container_year=self.learning_container_year,
                                                            academic_year=self.academic_year,
                                                            campus=self.be_campus_1)
        self.external_lu_BE_1 = ExternalLearningUnitYearFactory(learning_unit_year=self.learning_unit_year_3)

        self.be_organization_adr_city2 = OrganizationAddressFactory(country=self.a_be_country, city='Bruxelles')
        self.be_campus_2 = CampusFactory(organization=self.be_organization_adr_city2.organization)
        self.learning_container_year_4 = LearningContainerYearFactory(academic_year=self.academic_year)
        self.external_lu_BE_2 = ExternalLearningUnitYearFactory(
            learning_unit_year=LearningUnitYearFactory(learning_container_year=self.learning_container_year_4,
                                                       academic_year=self.academic_year,
                                                       campus=self.be_campus_2))

    def test_search_learning_units_on_acronym(self):
        form_data = {
            "acronym": self.external_lu_1.learning_unit_year.acronym,
        }

        form = ExternalLearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertCountEqual(form.get_activity_learning_units(), [self.external_lu_1])

    def test_search_learning_units_on_partial_acronym(self):
        form_data = {
            "acronym": self.external_lu_1.learning_unit_year.acronym[:5],
        }

        form = ExternalLearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertCountEqual(form.get_activity_learning_units(), [self.external_lu_1, self.external_lu_2])

    def test_search_learning_units_by_country(self):
        form_data = {
            "country": self.a_be_country.id,
        }

        form = ExternalLearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertCountEqual(form.get_activity_learning_units(), [self.external_lu_BE_1, self.external_lu_BE_2])

    def test_search_learning_units_by_city(self):
        form_data = {
            "city": NAMEN,
        }

        form = ExternalLearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertCountEqual(form.get_activity_learning_units(), [self.external_lu_BE_1])

    def test_search_learning_units_by_campus(self):
        form_data = {

            "campus": self.be_campus_1.id,
        }

        form = ExternalLearningUnitYearForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertCountEqual(form.get_activity_learning_units(), [self.external_lu_BE_1])

    def test_has_no_criteria(self):
        form = ExternalLearningUnitYearForm({})
        self.assertFalse(form.is_valid())
        self.assertIn(_("Please choose at least one criteria!"), form.errors['__all__'])
