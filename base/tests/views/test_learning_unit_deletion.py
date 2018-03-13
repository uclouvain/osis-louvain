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
import datetime
from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.utils.translation import ugettext_lazy as _

from base.models import person
from base.models.enums import entity_container_year_link_type
from base.models.enums import entity_type
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.models.person_entity import PersonEntity
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory


class LearningUnitDelete(TestCase):
    def setUp(self):
        self.user = UserFactory(username="jeandp")
        content_type = ContentType.objects.get_for_model(LearningUnit)
        permission = Permission.objects.get(codename="can_delete_learningunit",
                                            content_type=content_type)
        self.user.user_permissions.add(permission)
        person = PersonFactory(user=self.user)
        self.entity_version = EntityVersionFactory(entity_type=entity_type.FACULTY, acronym="SST",
                                                   start_date=datetime.date(year=1990, month=1, day=1),
                                                   end_date=None)
        PersonEntityFactory(person=person, entity=self.entity_version.entity, with_child=True)

        self.learning_unit_year_list = self.create_learning_unit_years_and_dependencies()

    def create_learning_unit_years_and_dependencies(self):
        l1 = LearningUnitFactory(start_year=1900)

        learning_unit_years = []
        for year in range(4):
            ac_year = AcademicYearFactory(year=2000 + year)
            l_containeryear = LearningContainerYearFactory(academic_year=ac_year)
            EntityContainerYearFactory(learning_container_year=l_containeryear, entity=self.entity_version.entity,
                                       type=entity_container_year_link_type.REQUIREMENT_ENTITY)
            learning_unit_year = LearningUnitYearFactory(learning_unit=l1, academic_year=ac_year,
                                                         learning_container_year=l_containeryear)
            learning_unit_years.append(learning_unit_year)

        learning_unit_years[1].subtype = learning_unit_year_subtypes.FULL
        learning_unit_years[1].save()
        lcomponent = LearningComponentYearFactory()
        LearningClassYearFactory(learning_component_year=lcomponent)
        LearningClassYearFactory(learning_component_year=lcomponent)
        LearningUnitComponentFactory(learning_unit_year=learning_unit_years[1],
                                     learning_component_year=lcomponent)
        return learning_unit_years

    @mock.patch('base.views.layout.render')
    def test_delete_from_given_learning_unit_year_case_success(self, mock_render):
        learning_unit_years = self.learning_unit_year_list

        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        request_factory = RequestFactory()

        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[learning_unit_years[1].id]))
        request.user = self.user

        delete_from_given_learning_unit_year(request, learning_unit_years[1].id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        self.assertEqual(_('msg_warning_delete_learning_unit') % learning_unit_years[1], context['title'])

        # click on accept button
        request = request_factory.post(reverse(delete_from_given_learning_unit_year, args=[learning_unit_years[1].id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        delete_from_given_learning_unit_year(request, learning_unit_years[1].id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 4)
        self.assertIn(messages.SUCCESS, msg_level)

        with self.assertRaises(ObjectDoesNotExist):
            LearningUnitYear.objects.get(id=learning_unit_years[1].id)

        with self.assertRaises(ObjectDoesNotExist):
            LearningUnitYear.objects.get(id=learning_unit_years[2].id)

        with self.assertRaises(ObjectDoesNotExist):
            LearningUnitYear.objects.get(id=learning_unit_years[3].id)

        self.assertIsNotNone(LearningUnitYear.objects.get(id=learning_unit_years[0].id))

    def test_delete_all_learning_units_year_method_not_allowed(self):
        learning_unit_years = self.learning_unit_year_list

        from base.views.learning_unit_deletion import delete_all_learning_units_year

        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete_all_learning_units_year, args=[learning_unit_years[1].id]))
        request.user = self.user

        response = delete_all_learning_units_year(request, learning_unit_years[1].id)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_delete_all_learning_units_year_case_success(self):
        learning_unit_years = self.learning_unit_year_list

        from base.views.learning_unit_deletion import delete_all_learning_units_year

        request_factory = RequestFactory()

        request = request_factory.post(reverse(delete_all_learning_units_year, args=[learning_unit_years[1].id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = delete_all_learning_units_year(request, learning_unit_years[1].id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 5)
        self.assertIn(messages.SUCCESS, msg_level)

        for y in range(4):
            self.assertFalse(LearningUnitYear.objects.filter(pk=learning_unit_years[y].pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_units'))

    @mock.patch('base.views.layout.render')
    def test_delete_from_given_learning_unit_year_case_error(self, mock_render):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        LearningUnitEnrollmentFactory(learning_unit_year=ly1)

        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        request_factory = RequestFactory()

        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[ly1.id]))
        request.user = self.user

        setattr(request, 'session', 'session')

        delete_from_given_learning_unit_year(request, ly1.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        msg = context.get('messages_deletion', [])
        self.assertEqual(_('cannot_delete_learning_unit_year')
                         % {'learning_unit': ly1.acronym,
                            'year': ly1.academic_year},
                         context['title'])

        subtype = _('The partim') if ly1.is_partim() else _('The learning unit')
        self.assertIn(_("There is %(count)d enrollments in %(subtype)s %(acronym)s for the year %(year)s")
                      % {'subtype': subtype,
                         'acronym': ly1.acronym,
                         'year': ly1.academic_year,
                         'count': 1},
                      msg)

        self.assertIsNotNone(LearningUnitYear.objects.get(id=ly1.id))

    def test_delete_all_learning_units_year_case_error_have_enrollment(self):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        LearningUnitEnrollmentFactory(learning_unit_year=ly1)

        from base.views.learning_unit_deletion import delete_all_learning_units_year

        request_factory = RequestFactory()

        request = request_factory.post(reverse(delete_all_learning_units_year, args=[ly1.id]))
        request.user = self.user

        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = delete_all_learning_units_year(request, ly1.id)

        # Get message from context
        msg = [m.message for m in get_messages(request)]
        msg_level = [m.level for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.ERROR, msg_level)

        # Check error message
        subtype = _('The partim') if ly1.is_partim() else _('The learning unit')
        self.assertIn(_("There is %(count)d enrollments in %(subtype)s %(acronym)s for the year %(year)s")
                      % {'subtype': subtype,
                         'acronym': ly1.acronym,
                         'year': ly1.academic_year,
                         'count': 1},
                      msg)

        # Check that record is not deleted
        self.assertTrue(LearningUnitYear.objects.filter(pk=ly1.pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_unit', kwargs={'learning_unit_year_id': ly1.pk}))

    @mock.patch('base.views.layout.render')
    def test_delete_from_given_learning_unit_year_case_error_have_enrollment(self, mock_render):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        LearningUnitEnrollmentFactory(learning_unit_year=ly1)

        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        request_factory = RequestFactory()

        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[ly1.id]))
        request.user = self.user

        setattr(request, 'session', 'session')

        delete_from_given_learning_unit_year(request, ly1.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]

        msg = context.get('messages_deletion', [])
        self.assertEqual(_('cannot_delete_learning_unit_year')
                         % {'learning_unit': ly1.acronym,
                            'year': ly1.academic_year},
                         context['title'])

        subtype = _('The partim') if ly1.is_partim() else _('The learning unit')
        self.assertIn(_("There is %(count)d enrollments in %(subtype)s %(acronym)s for the year %(year)s")
                      % {'subtype': subtype,
                         'acronym': ly1.acronym,
                         'year': ly1.academic_year,
                         'count': 1},
                      msg)

        self.assertIsNotNone(LearningUnitYear.objects.get(id=ly1.id))

    def test_delete_from_given_learning_unit_year_case_error_not_attached_to_entity(self):
        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        l_unit_year_to_delete = self.learning_unit_year_list[0]
        PersonEntity.objects.all().delete()  # Remove all link person entity

        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[l_unit_year_to_delete.id]))
        request.user = self.user

        response = delete_from_given_learning_unit_year(request, l_unit_year_to_delete.id)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_delete_from_given_learning_unit_year_faculty_manager_role(self):
        """A Faculty manager can only remove container_type other than COURSE/INTERNSHIP/DISSERTATION"""
        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        add_to_group(self.user, person.FACULTY_MANAGER_GROUP)
        l_unit_year_to_delete = self.learning_unit_year_list[0]
        l_unit_year_to_delete.subtype = learning_unit_year_subtypes.PARTIM
        l_unit_year_to_delete.save()
        l_container_year = l_unit_year_to_delete.learning_container_year
        l_container_year.container_type = learning_container_year_types.COURSE
        l_container_year.save()

        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[l_unit_year_to_delete.id]))
        request.user = self.user
        setattr(request, 'session', 'session')

        response = delete_from_given_learning_unit_year(request, l_unit_year_to_delete.id)

        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_delete_from_given_learning_unit_year_case_error_faculty_manager(self):
        """A Faculty manager can only remove container_type other than COURSE/INTERNSHIP/DISSERTATION"""
        from base.views.learning_unit_deletion import delete_from_given_learning_unit_year

        add_to_group(self.user, person.FACULTY_MANAGER_GROUP)
        l_unit_year_to_delete = self.learning_unit_year_list[0]
        l_container_year = l_unit_year_to_delete.learning_container_year
        request_factory = RequestFactory()

        # Full Course
        l_container_year.container_type = learning_container_year_types.COURSE
        l_container_year.save()
        l_unit_year_to_delete.subtype = learning_unit_year_subtypes.FULL
        l_unit_year_to_delete.save()
        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[l_unit_year_to_delete.id]))
        request.user = self.user
        response = delete_from_given_learning_unit_year(request, l_unit_year_to_delete.id)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Internship
        l_container_year.container_type = learning_container_year_types.INTERNSHIP
        l_container_year.save()
        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[l_unit_year_to_delete.id]))
        request.user = self.user
        response = delete_from_given_learning_unit_year(request, l_unit_year_to_delete.id)
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Dissertation
        l_container_year.container_type = learning_container_year_types.DISSERTATION
        l_container_year.save()
        request = request_factory.get(reverse(delete_from_given_learning_unit_year, args=[l_unit_year_to_delete.id]))
        request.user = self.user
        response = delete_from_given_learning_unit_year(request, l_unit_year_to_delete.id)
        self.assertEqual(response.status_code, 403)  # Forbidden


def add_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)
