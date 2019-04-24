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
import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.utils.translation import ugettext_lazy as _
from waffle.testutils import override_flag

from attribution.tests.factories.attribution import AttributionFactory, AttributionNewFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.models.enums import entity_container_year_link_type
from base.models.enums import entity_type
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollmentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory
from base.views.learning_units.delete import delete_all_learning_units_year


@override_flag('learning_unit_delete', active=True)
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
        acronym = "LDROI1004"
        l1 = LearningUnitFactory(start_year=settings.YEAR_LIMIT_LUE_MODIFICATION)

        learning_unit_years = []
        for year in range(4):
            ac_year = AcademicYearFactory(year=settings.YEAR_LIMIT_LUE_MODIFICATION + year)
            l_containeryear = LearningContainerYearFactory(academic_year=ac_year)
            EntityContainerYearFactory(learning_container_year=l_containeryear, entity=self.entity_version.entity,
                                       type=entity_container_year_link_type.REQUIREMENT_ENTITY)
            learning_unit_year = LearningUnitYearFactory(acronym=acronym, learning_unit=l1, academic_year=ac_year,
                                                         learning_container_year=l_containeryear)
            learning_unit_years.append(learning_unit_year)

        learning_unit_years[1].subtype = learning_unit_year_subtypes.FULL
        learning_unit_years[1].save()
        lcomponent = LearningComponentYearFactory()
        LearningClassYearFactory(learning_component_year=lcomponent)
        LearningClassYearFactory(learning_component_year=lcomponent)
        return learning_unit_years

    def test_delete_all_learning_units_year_method_not_allowed(self):
        learning_unit_years = self.learning_unit_year_list

        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete_all_learning_units_year, args=[learning_unit_years[1].id]))
        request.user = self.user

        response = delete_all_learning_units_year(request, learning_unit_years[1].id)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_delete_all_learning_units_year_case_success(self):
        learning_unit_years = self.learning_unit_year_list

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

    def test_delete_all_learning_units_year_case_error_start_date(self):
        learning_unit_years = self.learning_unit_year_list
        request_factory = RequestFactory()
        learning_unit_years[1].learning_unit.start_year = 2014
        learning_unit_years[1].learning_unit.save()

        request = request_factory.post(reverse(delete_all_learning_units_year, args=[learning_unit_years[1].id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = delete_all_learning_units_year(request, learning_unit_years[1].id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]

        self.assertIn(messages.ERROR, msg_level, msg)

        for y in range(4):
            self.assertTrue(LearningUnitYear.objects.filter(pk=learning_unit_years[y].pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_units'))

    def test_delete_all_learning_units_year_case_error_have_enrollment(self):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        LearningUnitEnrollmentFactory(learning_unit_year=ly1)

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

    def test_delete_all_learning_units_year_case_error_have_attribution(self):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        attrib_1 = AttributionFactory(learning_unit_year=ly1)

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
        self.assertIn(_("%(subtype)s %(acronym)s is assigned to %(tutor)s for the year %(year)s")
                      % {'subtype': subtype,
                         'acronym': ly1.acronym,
                         'tutor': attrib_1.tutor,
                         'year': ly1.academic_year},
                      msg)

        # Check that record is not deleted
        self.assertTrue(LearningUnitYear.objects.filter(pk=ly1.pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_unit', kwargs={'learning_unit_year_id': ly1.pk}))

    def test_delete_all_learning_units_year_case_success_have_attribution_new_without_charge(self):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        AttributionNewFactory(learning_container_year=ly1.learning_container_year)
        request_factory = RequestFactory()

        request = request_factory.post(reverse(delete_all_learning_units_year, args=[ly1.id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = delete_all_learning_units_year(request, ly1.id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 5)
        self.assertIn(messages.SUCCESS, msg_level)

        for y in range(4):
            self.assertFalse(LearningUnitYear.objects.filter(pk=learning_unit_years[y].pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_units'))

    def test_delete_all_learning_units_year_case_error_have_attributionnew_with_charge(self):
        learning_unit_years = self.learning_unit_year_list
        ly1 = learning_unit_years[1]
        attrib_new_1 = AttributionNewFactory(learning_container_year=ly1.learning_container_year)
        learning_component_year_1 = LearningComponentYearFactory(learning_unit_year=ly1)
        AttributionChargeNewFactory(attribution=attrib_new_1, learning_component_year=learning_component_year_1)

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
        self.assertIn(_("%(subtype)s %(acronym)s is assigned to %(tutor)s for the year %(year)s")
                      % {'subtype': subtype,
                         'acronym': ly1.acronym,
                         'tutor': attrib_new_1.tutor,
                         'year': ly1.academic_year},
                      msg)

        # Check that record is not deleted
        self.assertTrue(LearningUnitYear.objects.filter(pk=ly1.pk).exists())

        # Check redirection to identification
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('learning_unit', kwargs={'learning_unit_year_id': ly1.pk}))


def add_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)
