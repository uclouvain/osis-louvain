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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from unittest import mock

from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase, RequestFactory


from base.forms import learning_units
from base.forms.learning_unit_create import CreateLearningUnitYearForm
from base.models import learning_unit_component
from base.models import learning_unit_component_class
from base.models.academic_year import AcademicYear
from base.models.enums import learning_container_year_types, organization_type, entity_type
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.internship_subtypes import TEACHING_INTERNSHIP
from base.models.enums.learning_container_year_types import COURSE
from base.models.enums.learning_unit_periodicity import ANNUAL
from base.models.enums.learning_unit_year_session import SESSION_P23
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_component_class import LearningUnitComponentClassFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.models.enums import entity_container_year_link_type
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory
from base.business import learning_unit as learning_unit_business
from django.utils.translation import ugettext_lazy as _
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


class LearningUnitViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_year_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                         end_date=today.replace(year=today.year + 2),
                                                         year=today.year + 1)
        self.academic_year_2 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 2),
                                                         end_date=today.replace(year=today.year + 3),
                                                         year=today.year + 2)
        self.academic_year_3 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 3),
                                                         end_date=today.replace(year=today.year + 4),
                                                         year=today.year + 3)
        self.academic_year_4 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 4),
                                                         end_date=today.replace(year=today.year + 5),
                                                         year=today.year + 4)
        self.academic_year_5 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 5),
                                                         end_date=today.replace(year=today.year + 6),
                                                         year=today.year + 5)
        self.academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                         end_date=today.replace(year=today.year + 7),
                                                         year=today.year + 6)
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        super(AcademicYear, self.academic_year_1).save()
        super(AcademicYear, self.academic_year_2).save()
        super(AcademicYear, self.academic_year_3).save()
        super(AcademicYear, self.academic_year_4).save()
        super(AcademicYear, self.academic_year_5).save()
        super(AcademicYear, self.academic_year_6).save()
        self.learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year)
        self.learning_component_yr = LearningComponentYearFactory(learning_container_year=self.learning_container_yr)
        self.organization = OrganizationFactory(type=organization_type.MAIN)
        self.country = CountryFactory()
        self.entity = EntityFactory(country=self.country, organization=self.organization)
        self.entity_2 = EntityFactory(country=self.country, organization=self.organization)
        self.entity_3 = EntityFactory(country=self.country, organization=self.organization)
        self.entity_container_yr = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                              type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                              entity=self.entity)
        self.entity_container_yr_2 = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                                type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                                entity=self.entity_2)
        self.entity_container_yr_3 = EntityContainerYearFactory(learning_container_year=self.learning_container_yr,
                                                                type=entity_container_year_link_type.REQUIREMENT_ENTITY,
                                                                entity=self.entity_3)
        self.entity_version = EntityVersionFactory(entity=self.entity, entity_type=entity_type.SCHOOL, start_date=today,
                                                   end_date=today.replace(year=today.year + 1))

        self.campus = CampusFactory(organization=self.organization, is_administration=True, code="L")
        self.language = LanguageFactory(code='FR')
        self.a_superuser = SuperUserFactory()
        self.person = PersonFactory(user=self.a_superuser)
        PersonEntityFactory(person=self.person, entity=self.entity)
        PersonEntityFactory(person=self.person, entity=self.entity_2)
        PersonEntityFactory(person=self.person, entity=self.entity_3)
        self.client.force_login(self.a_superuser)

    @mock.patch('base.views.layout.render')
    def test_learning_units(self, mock_render):
        request_factory = RequestFactory()

        request = request_factory.get(reverse('learning_units'))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['academic_years']), 7)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search(self, mock_render):
        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_units'))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units

        learning_units(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['academic_years'].count(), 7)
        self.assertEqual(context['current_academic_year'], self.current_academic_year)
        self.assertEqual(len(context['types']),
                         len(learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES))
        self.assertEqual(len(context['container_types']),
                         len(learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES))
        self.assertTrue(context['experimental_phase'])
        self.assertIsNone(context['learning_units'])

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_acronym_filtering(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': True,
            'acronym': 'LBIR'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 3)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_by_acronym_with_valid_regex(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': True,
            'acronym': '^DRT.+A'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 1)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_by_acronym_with_invalid_regex(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'status': True,
            'acronym': '^LB(+)2+'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(context['form'].errors['acronym'], [_('LU_ERRORS_INVALID_REGEX_SYNTAX')])

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'ENVI'
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 1)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_requirement_entity_and_subord(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        request = request_factory.get(reverse('learning_units'), data=filter_data)
        request.user = self.a_superuser

        from base.views.learning_unit import learning_units
        learning_units(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 6)

    @mock.patch('base.views.layout.render')
    def test_learning_units_search_with_service_course(self, mock_render):
        self._prepare_context_learning_units_search()
        request_factory = RequestFactory()
        filter_data = {
            'academic_year_id': self.current_academic_year.id,
            'requirement_entity_acronym': 'AGRO',
            'with_entity_subordinated': True
        }
        from base.views.learning_unit import learning_units_service_course

        request = request_factory.get(reverse(learning_units_service_course), data=filter_data)
        request.user = self.a_superuser

        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))
        learning_units_service_course(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_units.html')
        self.assertEqual(len(context['learning_units']), 0)

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_read(self, mock_program_manager, mock_render):
        mock_program_manager.return_value = True

        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year)

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit', args=[learning_unit_year.id]))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(context['learning_unit_year'], learning_unit_year)

    def test_get_components_no_learning_container_yr(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.assertEqual(len(learning_unit_business.get_same_container_year_components(learning_unit_year, False)), 0)

    def test_get_components_with_classes(self):
        l_container = LearningContainerFactory()
        l_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                        title="LC-98998", learning_container=l_container)
        l_component_year = LearningComponentYearFactory(learning_container_year=l_container_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        LearningClassYearFactory(learning_component_year=l_component_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=l_container_year)

        components = learning_unit_business.get_same_container_year_components(learning_unit_year, True)
        self.assertEqual(len(components), 1)
        self.assertEqual(len(components[0]['learning_component_year'].classes), 2)

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_get_partims_identification_tabs(self, mock_program_manager, mock_render):
        mock_program_manager.return_value = True

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210A",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210B",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )
        LearningUnitYearFactory(
            acronym="LCHIM1210F",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            academic_year=self.current_academic_year
        )

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit', args=[learning_unit_year.id]))
        request.user = self.a_superuser

        from base.views.learning_unit import learning_unit_identification

        learning_unit_identification(request, learning_unit_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'learning_unit/identification.html')
        self.assertEqual(len(context['learning_container_year_partims']), 3)

    def test_learning_unit_usage_two_usages(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLA',
                                                     quadrimester='Q1',
                                                     learning_container_year=learning_container_yr)
        learning_unit_yr_2 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOLB',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_2,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_business._learning_unit_usage(learning_component_yr), 'LBIOLA (Q1), LBIOLB (?)')

    def test_learning_unit_usage_with_complete_LU(self):
        learning_container_yr = LearningContainerYearFactory(academic_year=self.current_academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     acronym='LBIOL', quadrimester='Q1&2',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                     learning_component_year=learning_component_yr)

        self.assertEqual(learning_unit_business._learning_unit_usage(learning_component_yr), 'LBIOL (Q1&2)')

    def test_learning_unit_usage_by_class_with_complete_LU(self):
        academic_year = AcademicYearFactory(year=2016)
        learning_container_yr = LearningContainerYearFactory(academic_year=academic_year,
                                                             acronym='LBIOL')

        learning_unit_yr_1 = LearningUnitYearFactory(academic_year=academic_year,
                                                     acronym='LBIOL',
                                                     learning_container_year=learning_container_yr)

        learning_component_yr = LearningComponentYearFactory(learning_container_year=learning_container_yr)

        learning_unit_component = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr_1,
                                                               learning_component_year=learning_component_yr)
        learning_class_year = LearningClassYearFactory(learning_component_year=learning_component_yr)
        LearningUnitComponentClassFactory(learning_unit_component=learning_unit_component,
                                          learning_class_year=learning_class_year)
        self.assertEqual(learning_unit_business._learning_unit_usage_by_class(learning_class_year), 'LBIOL')

    def test_component_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)

    def test_component_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1"})
        self.assertRaises(ObjectDoesNotExist, learning_unit_component.LearningUnitComponent.objects.filter(
            pk=learning_unit_compnt.id).first())

    def test_component_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        url = reverse('learning_unit_component_edit', args=[learning_unit_yr.id])
        qs = 'learning_component_year_id={}'.format(self.learning_component_yr.id)

        response = self.client.post('{}?{}'.format(url, qs), data={"planned_classes": "1", "used_by": "on"})

        self.assertTrue(learning_unit_component.find_by_learning_component_year(self.learning_component_yr).exists())

    def _prepare_context_learning_units_search(self):
        # Create a structure [Entity / Entity version]
        ssh_entity = EntityFactory(country=self.country)
        ssh_entity_v = EntityVersionFactory(acronym="SSH", end_date=None, entity=ssh_entity)

        agro_entity = EntityFactory(country=self.country)
        envi_entity = EntityFactory(country=self.country)
        ages_entity = EntityFactory(country=self.country)
        agro_entity_v = EntityVersionFactory(entity=agro_entity, parent=ssh_entity_v.entity, acronym="AGRO",
                                             end_date=None)
        envi_entity_v = EntityVersionFactory(entity=envi_entity, parent=agro_entity_v.entity, acronym="ENVI",
                                             end_date=None)
        ages_entity_v = EntityVersionFactory(entity=ages_entity, parent=agro_entity_v.entity, acronym="AGES",
                                             end_date=None)

        espo_entity = EntityFactory(country=self.country)
        drt_entity = EntityFactory(country=self.country)
        espo_entity_v = EntityVersionFactory(entity=espo_entity, parent=ssh_entity_v.entity, acronym="ESPO",
                                             end_date=None)
        drt_entity_v = EntityVersionFactory(entity=drt_entity, parent=ssh_entity_v.entity, acronym="DRT",
                                            end_date=None)

        # Create UE and put entity charge [AGRO]
        l_container_yr = LearningContainerYearFactory(acronym="LBIR1100", academic_year=self.current_academic_year,
                                                      container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr, entity=agro_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="LBIR1100", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="LBIR1100A", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100B", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(acronym="LBIR1100C", learning_container_year=l_container_yr,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM,
                                status=False)

        # Create another UE and put entity charge [ENV]
        l_container_yr_2 = LearningContainerYearFactory(acronym="CHIM1200", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_2, entity=envi_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="CHIM1200", learning_container_year=l_container_yr_2,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [DRT]
        l_container_yr_3 = LearningContainerYearFactory(acronym="DRT1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.COURSE)
        EntityContainerYearFactory(learning_container_year=l_container_yr_3, entity=drt_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="DRT1500", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(acronym="DRT1500A", learning_container_year=l_container_yr_3,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.PARTIM)

        # Create another UE and put entity charge [ESPO]
        l_container_yr_4 = LearningContainerYearFactory(acronym="ESPO1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.DISSERTATION)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=espo_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="ESPO1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=learning_unit_year_subtypes.FULL)

        # Create another UE and put entity charge [AGES]
        l_container_yr_4 = LearningContainerYearFactory(acronym="AGES1500", academic_year=self.current_academic_year,
                                                        container_type=learning_container_year_types.MASTER_THESIS)
        EntityContainerYearFactory(learning_container_year=l_container_yr_4, entity=ages_entity_v.entity,
                                   type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        LearningUnitYearFactory(acronym="AGES1500", learning_container_year=l_container_yr_4,
                                academic_year=self.current_academic_year, subtype=None)

    def test_class_save(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})
        self.learning_component_yr.refresh_from_db()
        self.assertEqual(response.status_code, 302)

    def test_class_save_create_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={"used_by": "on"})

        self.assertTrue(learning_unit_component_class.search(learning_unit_compnt, learning_class_yr).exists())

    def test_class_save_delete_link(self):
        learning_unit_yr = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                   learning_container_year=self.learning_container_yr)
        learning_unit_compnt = LearningUnitComponentFactory(learning_unit_year=learning_unit_yr,
                                                            learning_component_year=self.learning_component_yr)
        learning_class_yr = LearningClassYearFactory(learning_component_year=self.learning_component_yr)
        a_link = LearningUnitComponentClassFactory(learning_unit_component=learning_unit_compnt,
                                                   learning_class_year=learning_class_yr)

        response = self.client.post('{}?{}&{}'.format(reverse('learning_class_year_edit', args=[learning_unit_yr.id]),
                                                      'learning_component_year_id={}'.format(
                                                          self.learning_component_yr.id),
                                                      'learning_class_year_id={}'.format(learning_class_yr.id)),
                                    data={})

        self.assertRaises(ObjectDoesNotExist,
                          learning_unit_component_class.LearningUnitComponentClass.objects.filter(pk=a_link.id).first())

    def get_base_form_data(self):
        return {"first_letter": "L",
                "acronym": "TAU2000",
                "container_type": COURSE,
                "academic_year": self.current_academic_year.id,
                "status": True,
                "periodicity": ANNUAL,
                "credits": "5",
                "campus": self.campus.id,
                "internship_subtype": TEACHING_INTERNSHIP,
                "title": "LAW",
                "title_english": "LAW",
                "requirement_entity": self.entity_version.id,
                "allocation_entity": self.entity_version.id,
                "additional_entity_1": self.entity_version.id,
                "additional_entity_2": self.entity_version.id,
                "subtype": learning_unit_year_subtypes.FULL,
                "language": self.language.id,
                "session": SESSION_P23,
                "faculty_remark": "faculty remark",
                "other_remark": "other remark"}

    def get_valid_data(self):
        return self.get_base_form_data()

    def get_faulty_acronym(self):
        faultydict = dict(self.get_valid_data())
        faultydict["acronym"] = "TA200"
        return faultydict

    def get_empty_acronym(self):
        faultyDict = dict(self.get_valid_data())
        faultyDict["acronym"] = ""
        return faultyDict

    def get_faulty_requirement_entity(self):
        """We will create an entity + entity version that user cannot create on it"""
        entity = EntityFactory(country=self.country, organization=self.organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, end_date=None,
                                              start_date=datetime.date.today())
        faultydict = dict(self.get_valid_data())
        faultydict['requirement_entity'] = entity_version.id
        return faultydict

    def test_learning_unit_year_form(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        url = reverse('learning_unit_year_add')
        response = self.client.post(url, data=self.get_base_form_data())
        self.assertEqual(response.status_code, 302)
        count_learning_unit_year = LearningUnitYear.objects.all().count()
        self.assertEqual(count_learning_unit_year, 6)

    def test_create_learning_unit_year_requirement_entity_not_allowed(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_faulty_requirement_entity())
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertTrue('requirement_entity' in form.errors)

    def test_learning_unit_acronym_form(self):
        form = CreateLearningUnitYearForm(person=self.person, data=self.get_valid_data())
        self.assertTrue(form.is_valid(), form.errors)

        form = CreateLearningUnitYearForm(person=self.person, data=self.get_empty_acronym())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['acronym'], [_('This field is required.')])

        form = CreateLearningUnitYearForm(person=self.person, data=self.get_faulty_acronym())
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors['acronym'], [_('invalid_acronym')])

    def test_learning_unit_check_acronym(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        url = reverse('check_acronym')
        get_data = {'acronym': 'goodacronym', 'year_id': self.academic_year_1.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': False,
             'existed_acronym': False,
             'last_using': ""}
        )

        learning_unit_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year
        )
        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1210",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1210', 'year_id': self.current_academic_year.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': False,
             'existing_acronym': True,
             'existed_acronym': False,
             'last_using': ""}
        )

        learning_unit_year = LearningUnitYearFactory(
            acronym="LCHIM1211",
            learning_container_year=learning_unit_container_year,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=self.current_academic_year
        )
        learning_unit_year.save()

        get_data = {'acronym': 'LCHIM1211', 'year_id': self.academic_year_6.id}
        response = self.client.get(url, get_data, **kwargs)

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'valid': True,
             'existing_acronym': False,
             'existed_acronym': True,
             'last_using': str(self.current_academic_year)}
        )

    def _get_volumes_data(self, learning_units_year):
        if not isinstance(learning_units_year, list):
            learning_units_year = [learning_units_year]
        data = {}
        for learning_unit_year in learning_units_year:
            data['VOLUME_TOTAL_REQUIREMENT_ENTITIES_{}_{}'.format(learning_unit_year.id,
                                                                  self.learning_component_yr.id)] = [60]
            data['VOLUME_Q1_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [10]
            data['VOLUME_Q2_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [20]
            data['VOLUME_TOTAL_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [30]
            data['PLANNED_CLASSES_{}_{}'.format(learning_unit_year.id, self.learning_component_yr.id)] = [2]
        return data

    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager')
    def test_get_learning_unit_volumes_management(self, mock_program_manager, mock_render):
        mock_program_manager.return_value = True

        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr)
        learning_unit_year.save()

        request_factory = RequestFactory()
        url = reverse("learning_unit_volumes_management", args=[learning_unit_year.id])
        # GET request
        request = request_factory.get(url)
        request.user = self.a_superuser
        from base.views.learning_unit import learning_unit_volumes_management
        learning_unit_volumes_management(request, learning_unit_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'learning_unit/volumes_management.html')
        self.assertEqual(context['tab_active'], 'components')

        # POST request
        request = request_factory.post(url, self._get_volumes_data([learning_unit_year]))
        request.user = mock.Mock()
        learning_unit_volumes_management(request, learning_unit_year.id)
        self.assertTrue(mock_render.called)

    def test_volumes_validation(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=self.learning_container_yr)
        learning_unit_year.save()

        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        url = reverse("volumes_validation", args=[learning_unit_year.id])

        data = self._get_volumes_data(learning_unit_year)
        # TODO inject wrong data
        response = self.client.get(url, data, **kwargs)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'errors': [],
             }
        )

    @mock.patch("base.models.learning_unit_year.count_search_results")
    def test_error_message_case_too_many_results_to_show(self, mock_count):
        mock_count.return_value = learning_units.MAX_RECORDS + 1
        response = self.client.get(reverse('learning_units'), {'academic_year_id': self.academic_year_1.id})
        messages = list(response.context['messages'])
        self.assertEqual(messages[0].message, _('too_many_results'))


class LearningUnitCreate(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.url = reverse('learning_unit_create', args=[2015])
        self.language = LanguageFactory(code='FR')

        self.client.force_login(self.person.user)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        from django.utils.encoding import uri_to_iri
        self.assertEqual(uri_to_iri(uri_to_iri(response.url)), '/login/?next={}'.format(self.url))
        self.assertEqual(response.status_code, 302)

    def test_when_user_has_not_permission(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_when_user_has_permission(self):
        content_type = ContentType.objects.get_for_model(LearningUnit)
        permission = Permission.objects.get(codename="can_create_learningunit",
                                            content_type=content_type)
        self.person.user.user_permissions.add(permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/learning_unit_form.html')

        self.assertIsInstance(response.context['form'], CreateLearningUnitYearForm)


class LearningUnitYearAdd(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        content_type = ContentType.objects.get_for_model(LearningUnit)
        permission = Permission.objects.get(codename="can_create_learningunit",
                                            content_type=content_type)
        self.person.user.user_permissions.add(permission)
        self.url = reverse('learning_unit_year_add')

        self.client.force_login(self.person.user)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_when_user_has_not_permission(self):
        a_person = PersonFactory()
        self.client.force_login(a_person.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_when_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTemplateUsed(response, 'method_not_allowed.html')

    def test_when_empty_form_data(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/learning_unit_form.html')

        self.assertIsInstance(response.context['form'], CreateLearningUnitYearForm)

    def test_when_valid_form_data(self):
        today = datetime.date.today()
        academic_year_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                    end_date=today.replace(year=today.year + 2),
                                                    year=today.year + 1)
        academic_year_2 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 2),
                                                    end_date=today.replace(year=today.year + 3),
                                                    year=today.year + 2)
        academic_year_3 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 3),
                                                    end_date=today.replace(year=today.year + 4),
                                                    year=today.year + 3)
        academic_year_4 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 4),
                                                    end_date=today.replace(year=today.year + 5),
                                                    year=today.year + 4)
        academic_year_5 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 5),
                                                    end_date=today.replace(year=today.year + 6),
                                                    year=today.year + 5)
        academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                    end_date=today.replace(year=today.year + 7),
                                                    year=today.year + 6)
        current_academic_year = AcademicYearFactory(start_date=today,
                                                    end_date=today.replace(year=today.year + 1),
                                                    year=today.year)
        super(AcademicYear, academic_year_1).save()
        super(AcademicYear, academic_year_2).save()
        super(AcademicYear, academic_year_3).save()
        super(AcademicYear, academic_year_4).save()
        super(AcademicYear, academic_year_5).save()
        super(AcademicYear, academic_year_6).save()

        organization = OrganizationFactory(type=organization_type.MAIN)
        campus = CampusFactory(organization=organization)
        entity = EntityFactory(organization=organization)
        entity_version = EntityVersionFactory(entity=entity, entity_type=entity_type.SCHOOL, start_date=today,
                                              end_date=today.replace(year=today.year + 1))
        language = LanguageFactory()

        form_data = {
            "first_letter": "L",
            "acronym": "TAU2000",
            "container_type": COURSE,
            "academic_year": current_academic_year.id,
            "status": True,
            "periodicity": ANNUAL,
            "credits": "5",
            "campus": campus.id,
            "internship_subtype": TEACHING_INTERNSHIP,
            "title": "LAW",
            "title_english": "LAW",
            "requirement_entity": entity_version.id,
            "subtype": learning_unit_year_subtypes.FULL,
            "language": language.id,
            "session": SESSION_P23,
            "faculty_remark": "faculty remark",
            "other_remark": "other remark"
        }

        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)
