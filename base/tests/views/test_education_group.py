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

from django.contrib.auth.models import Permission, Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.test import TestCase, RequestFactory

from base.forms.education_groups import EducationGroupFilter
from base.models.academic_calendar import AcademicCalendar
from base.models.enums import education_group_categories, offer_year_entity_type
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.offer import OfferFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_entity import OfferYearEntityFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.structure import StructureFactory
from reference.tests.factories.country import CountryFactory

from base.views.education_group import education_groups


def save(self, *args, **kwargs):
    return super(AcademicCalendar, self).save()


class EducationGroupViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_year = AcademicYearFactory(start_date=today,
                                                 end_date=today.replace(year=today.year + 1),
                                                 year=today.year)

        self.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        self.type_minitraining = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        self.type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        request_factory = RequestFactory()

        EducationGroupYearFactory(acronym='EDPH2', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='ARKE2A', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='HIST2A', academic_year=self.academic_year)

        request = request_factory.get(reverse(education_groups), data={
            'acronym': 'EDPH2',
            'academic_year': self.academic_year.id,
        })
        request.user = mock.Mock()
        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 1)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_by_code_scs(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        request_factory = RequestFactory()

        EducationGroupYearFactory(acronym='EDPH2', partial_acronym='EDPH2_SCS', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='ARKE2A', partial_acronym='ARKE2A_SCS', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='HIST2A', partial_acronym='HIST2A_SCS', academic_year=self.academic_year)

        request = request_factory.get(reverse(education_groups), data={
            'partial_acronym': 'EDPH2_SCS',
            'academic_year': self.academic_year.id,
        })
        request.user = mock.Mock()
        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 1)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_by_requirement_entity(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda  x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        request_factory = RequestFactory()

        self._prepare_context_education_groups_search()

        request = request_factory.get(reverse('education_groups'), data={
                'academic_year': self.academic_year.id,
                'requirement_entity_acronym': 'AGRO'
            })
        request.user = mock.Mock()
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 1)


    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_by_requirement_entity_and_subord(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda  x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        request_factory = RequestFactory()

        self._prepare_context_education_groups_search()

        request = request_factory.get(reverse(education_groups), data={
                'academic_year': self.academic_year.id,
                'requirement_entity_acronym': 'AGRO',
                'with_entity_subordinated': True
            })
        request.user = mock.Mock()
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 3)


    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_by_type(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()

        EducationGroupYearFactory(acronym='EDPH2', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='ARKE2A', academic_year=self.academic_year)
        result = EducationGroupYearFactory(acronym='HIST2A', academic_year=self.academic_year,
                                  education_group_type=self.type_minitraining)

        request = request_factory.get(reverse(education_groups), data={
            'academic_year': self.academic_year.id,
            'education_group_type': self.type_minitraining.id
        })
        request.user = mock.Mock()

        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 1)
        self.assertIn(result, context['object_list'])

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_by_category(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()

        EducationGroupYearFactory(acronym='EDPH2', academic_year=self.academic_year)
        EducationGroupYearFactory(acronym='ARKE2A', academic_year=self.academic_year)
        result = EducationGroupYearFactory(acronym='HIST2A', academic_year=self.academic_year,
                                           education_group_type=self.type_minitraining)

        request = request_factory.get(reverse(education_groups), data={
            'academic_year': self.academic_year.id,
            'category': MINI_TRAINING
        })
        request.user = mock.Mock()

        education_groups(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'education_groups.html')
        self.assertEqual(len(context['object_list']), 1)
        self.assertIn(result, context['object_list'])

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_post(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()

        request = request_factory.post(reverse(education_groups), data={})
        request.user = mock.Mock()

        education_groups(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'education_groups.html')
        self.assertIsInstance(context.get('form'), EducationGroupFilter)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_groups_search_empty_result(self, mock_render, mock_decorators):
        from django.contrib.messages.storage.fallback import FallbackStorage

        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        request_factory = RequestFactory()
        from base.views.education_group import education_groups
        request = request_factory.get(reverse(education_groups), data={
            'academic_year': self.academic_year.id,
            'type': ''  # Simulate all type
        })
        request.user = mock.Mock()
        # Need session in order to store messages
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))

        education_groups(request)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_groups.html')
        self.assertFalse(context['object_list'])
        # It should have one message ['no_result']
        self.assertEqual(len(request._messages), 1)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager', return_value=True)
    @mock.patch('base.models.education_group_year.find_by_id')
    def test_education_group_read(self,
                                  mock_find_by_id,
                                  mock_program_manager,
                                  mock_render,
                                  mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        organization = EducationGroupOrganizationFactory(education_group_year=education_group_year)
        request = mock.Mock(method='GET')

        from base.views.education_group import education_group_read

        mock_find_by_id.return_value = education_group_year
        education_group_read(request, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_identification.html')
        self.assertEqual(context['education_group_year'].coorganizations.first(), organization)
        self.assertEqual(context['education_group_year'].coorganizations.first().address, organization.address)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager', return_value=True)
    @mock.patch('base.models.education_group_year.find_by_id')
    def test_education_group_parent_read(self,
                                         mock_find_by_id,
                                         mock_program_manager,
                                         mock_render,
                                         mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        education_group_type = EducationGroupTypeFactory(category=TRAINING)

        education_group_year_child = EducationGroupYearFactory(academic_year=self.academic_year,
                                                                education_group_type=education_group_type)
        education_group_year_parent = EducationGroupYearFactory(academic_year=self.academic_year,
                                                                education_group_type=education_group_type)

        GroupElementYearFactory(parent=education_group_year_parent, child_branch=education_group_year_child)
        request = mock.Mock(method='GET')

        from base.views.education_group import education_group_parent_read

        mock_find_by_id.return_value = education_group_year_child
        education_group_parent_read(request, education_group_year_child.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_identification.html')
        self.assertEqual(context['education_group_year'].parent_by_training, education_group_year_parent)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.person.get_user_interface_language', return_value=True)
    @mock.patch('base.models.education_group_year.find_by_id')
    def test_education_group_general_informations(self,
                                                  mock_find_by_id,
                                                  mock_get_user_interface_language,
                                                  mock_render,
                                                  mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        request = mock.Mock(method='GET')

        from base.views.education_group import education_group_general_informations

        mock_find_by_id.return_value = education_group_year
        education_group_general_informations(request, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_general_informations.html')

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.education_group_year.find_by_id')
    def test_education_administrative_data(self,
                                           mock_find_by_id,
                                           mock_render,
                                           mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        request = mock.Mock(method='GET')

        from base.views.education_group import education_group_administrative_data

        mock_find_by_id.return_value = education_group_year
        education_group_administrative_data(request, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_administrative_data.html')
        self.assertEqual(context['education_group_year'], education_group_year)

    def test_get_sessions_dates(self):
        from base.views.education_group import get_sessions_dates
        from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
        from base.tests.factories.academic_calendar import AcademicCalendarFactory
        from base.tests.factories.education_group_year import EducationGroupYearFactory
        from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory

        sessions_quantity = 3
        an_academic_year = AcademicYearFactory()
        academic_calendar = AcademicCalendarFactory.build(academic_year=an_academic_year)
        academic_calendar.save(functions=[])
        education_group_year = EducationGroupYearFactory(academic_year=an_academic_year)
        session_exam_calendars = [SessionExamCalendarFactory(number_session=session,
                                                             academic_calendar=academic_calendar)
                                  for session in range(1, sessions_quantity + 1)]
        offer_year_calendar = OfferYearCalendarFactory(
            academic_calendar=academic_calendar,
            education_group_year=education_group_year
        )
        self.assertEquals(
            get_sessions_dates(academic_calendar.reference, education_group_year),
            {
                'session{}'.format(s): offer_year_calendar for s in range(1, sessions_quantity + 1)
            }
        )

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_education_edit_administrative_data(self,
                                                mock_render,
                                                mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        from base.views.education_group import education_group_edit_administrative_data

        request_factory = RequestFactory()
        request = request_factory.get(reverse(education_group_edit_administrative_data, kwargs={
            'education_group_year_id': education_group_year.id
        }))
        request.user = mock.Mock()

        education_group_edit_administrative_data(request, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_edit_administrative_data.html')
        self.assertEqual(context['education_group_year'], education_group_year)
        self.assertEqual(context['f1'], False)
        self.assertEqual(context['f2'], False)


    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.education_group_year.find_by_id')
    def test_education_content(self,
                               mock_find_by_id,
                               mock_render,
                               mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        request = mock.Mock(method='GET')

        from base.views.education_group import education_group_content

        mock_find_by_id.return_value = education_group_year
        education_group_content(request, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_content.html')
        self.assertEqual(context['education_group_year'], education_group_year)

    def _prepare_context_education_groups_search(self):
        # Create a structure [Entity / Entity version]
        country = CountryFactory()
        structure = StructureFactory()
        ssh_entity = EntityFactory(country=country)
        ssh_entity_v = EntityVersionFactory(acronym="SSH", end_date=None, entity=ssh_entity)

        agro_entity = EntityFactory(country=country)
        envi_entity = EntityFactory(country=country)
        ages_entity = EntityFactory(country=country)
        agro_entity_v = EntityVersionFactory(entity=agro_entity, parent=ssh_entity_v.entity, acronym="AGRO",
                                             end_date=None)
        envi_entity_v = EntityVersionFactory(entity=envi_entity, parent=agro_entity_v.entity, acronym="ENVI",
                                             end_date=None)
        ages_entity_v = EntityVersionFactory(entity=ages_entity, parent=agro_entity_v.entity, acronym="AGES",
                                             end_date=None)

        # Create EG and put entity charge [AGRO]
        agro_education_group = EducationGroupFactory()
        agro_education_group_type = EducationGroupTypeFactory(category=TRAINING)

        agro_education_group_year = EducationGroupYearFactory(acronym='EDPH2',
                                                              academic_year=self.academic_year,
                                                              education_group=agro_education_group,
                                                              education_group_type=agro_education_group_type)

        agro_offer = OfferFactory()
        agro_offer_year=OfferYearFactory(offer=agro_offer,
                                    entity_management=structure,
                                    entity_administration_fac=structure)

        OfferYearEntityFactory(offer_year=agro_offer_year,
                               entity=agro_entity,
                               education_group_year=agro_education_group_year,
                               type=offer_year_entity_type.ENTITY_MANAGEMENT)

        # Create EG and put entity charge [ENVI]
        envi_education_group = EducationGroupFactory()
        envi_education_group_type = EducationGroupTypeFactory(category=TRAINING)

        envi_education_group_year = EducationGroupYearFactory(academic_year=self.academic_year,
                                                         education_group=envi_education_group,
                                                         education_group_type=envi_education_group_type)

        envi_offer = OfferFactory()
        envi_offer_year=OfferYearFactory(offer=envi_offer,
                                         entity_management=structure,
                                         entity_administration_fac=structure)

        OfferYearEntityFactory(offer_year=envi_offer_year,
                               entity=envi_entity,
                               education_group_year=envi_education_group_year,
                               type=offer_year_entity_type.ENTITY_MANAGEMENT)

        # Create EG and put entity charge [AGES]
        ages_education_group = EducationGroupFactory()
        ages_education_group_type = EducationGroupTypeFactory(category=TRAINING)

        ages_education_group_year = EducationGroupYearFactory(academic_year=self.academic_year,
                                                         education_group=ages_education_group,
                                                         education_group_type=ages_education_group_type)

        ages_offer = OfferFactory()
        ages_offer_year=OfferYearFactory(offer=ages_offer,
                                    entity_management=structure,
                                    entity_administration_fac=structure)

        OfferYearEntityFactory(offer_year=ages_offer_year,
                               entity=ages_entity,
                               education_group_year=ages_education_group_year,
                               type=offer_year_entity_type.ENTITY_MANAGEMENT)


class EducationGroupEditAdministrativeData(TestCase):
    def setUp(self):
        self.person = PersonFactory()

        self.permission = Permission.objects.get(codename='can_edit_offer_year_calendar')
        self.person.user.user_permissions.add(self.permission)

        self.education_group_year = EducationGroupYearFactory()
        self.program_manager = ProgramManagerFactory(person=self.person,
                                                     education_group=self.education_group_year.education_group)
        self.url = reverse('education_group_edit_administrative', args=[self.education_group_year.id])
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        Group.objects.get(name="program_managers").permissions.remove(self.permission)
        self.person.user.user_permissions.remove(self.permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_user_is_not_program_manager_of_education_group(self):
        self.program_manager.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_education_group_non_existent(self):
        self.education_group_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")
