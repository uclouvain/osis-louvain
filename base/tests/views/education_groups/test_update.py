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
import json
from http import HTTPStatus
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.http import HttpResponseForbidden
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.translation import ugettext as _
from waffle.testutils import override_flag

from base.business.group_element_years import management
from base.forms.education_group.group import GroupYearModelForm
from base.models.enums import education_group_categories, internship_presence
from base.models.enums.active_status import ACTIVE
from base.models.enums.schedule_type import DAILY
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.education_group_year import GroupFactory, TrainingFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory
from base.utils.cache import cache
from base.views.education_groups.update import update_education_group, _get_success_redirect_url
from reference.tests.factories.domain import DomainFactory
from reference.tests.factories.language import LanguageFactory


@override_flag('education_group_update', active=True)
class TestUpdate(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.start_date_ay_1 = self.current_academic_year.start_date.replace(year=self.current_academic_year.year + 1)
        self.end_date_ay_1 = self.current_academic_year.end_date.replace(year=self.current_academic_year.year + 2)
        academic_year_1 = AcademicYearFactory.build(start_date=self.start_date_ay_1,
                                                    end_date=self.end_date_ay_1,
                                                    year=self.current_academic_year.year + 1)
        academic_year_1.save()
        self.start_date_ay_2 = self.current_academic_year.start_date.replace(year=self.current_academic_year.year + 2)
        self.end_date_ay_2 = self.current_academic_year.end_date.replace(year=self.current_academic_year.year + 3)
        academic_year_2 = AcademicYearFactory.build(start_date=self.start_date_ay_2,
                                                    end_date=self.end_date_ay_2,
                                                    year=self.current_academic_year.year + 2)
        academic_year_2.save()

        self.education_group_year = GroupFactory()

        EntityVersionFactory(entity=self.education_group_year.management_entity,
                             start_date=self.education_group_year.academic_year.start_date)

        EntityVersionFactory(entity=self.education_group_year.administration_entity,
                             start_date=self.education_group_year.academic_year.start_date)

        AuthorizedRelationshipFactory(
            parent_type=self.education_group_year.education_group_type,
            child_type=self.education_group_year.education_group_type
        )

        self.url = reverse(update_education_group, args=[self.education_group_year.pk, self.education_group_year.pk])
        self.person = PersonFactory()

        self.client.force_login(self.person.user)
        permission = Permission.objects.get(codename='change_educationgroup')
        self.person.user.user_permissions.add(permission)
        self.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group",
                                       return_value=True)
        self.mocked_perm = self.perm_patcher.start()

        self.an_training_education_group_type = EducationGroupTypeFactory(category=education_group_categories.TRAINING)

        self.training_education_group_year = TrainingFactory(
            academic_year=self.current_academic_year,
            education_group_type=self.an_training_education_group_type
        )

        self.training_education_group_year_1 = TrainingFactory(
            academic_year=academic_year_1,
            education_group_type=self.an_training_education_group_type,
            education_group=self.training_education_group_year.education_group
        )

        self.training_education_group_year_2 = TrainingFactory(
            academic_year=academic_year_2,
            education_group_type=self.an_training_education_group_type,
            education_group=self.training_education_group_year.education_group
        )

        AuthorizedRelationshipFactory(
            parent_type=self.an_training_education_group_type,
            child_type=self.an_training_education_group_type,
        )

        EntityVersionFactory(
            entity=self.training_education_group_year.management_entity,
            start_date=self.education_group_year.academic_year.start_date
        )

        EntityVersionFactory(
            entity=self.training_education_group_year.administration_entity,
            start_date=self.education_group_year.academic_year.start_date
        )

        self.training_url = reverse(
            update_education_group,
            args=[self.training_education_group_year.pk, self.training_education_group_year.pk]
        )

        self.domains = [DomainFactory() for x in range(10)]

    def tearDown(self):
        self.perm_patcher.stop()

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_permission_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.mocked_perm.assert_called_once_with(self.person, self.education_group_year, raise_exception=True)

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/update_groups.html")

    def test_response_context(self):
        response = self.client.get(self.url)

        form_education_group_year = response.context["form_education_group_year"]

        self.assertIsInstance(form_education_group_year, GroupYearModelForm)

    def test_post(self):
        new_entity_version = MainEntityVersionFactory()
        PersonEntityFactory(person=self.person, entity=new_entity_version.entity)

        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.education_group_year.education_group_type.id,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.education_group_year.academic_year.pk,
            "constraint_type": "",
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.title, 'Cours au choix')
        self.assertEqual(self.education_group_year.title_english, 'deaze')
        self.assertEqual(self.education_group_year.credits, 42)
        self.assertEqual(self.education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.education_group_year.management_entity, new_entity_version.entity)

    def test_template_used_for_training(self):
        response = self.client.get(self.training_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/update_trainings.html")

    def test_post_training(self):
        old_domain = DomainFactory()
        EducationGroupYearDomainFactory(
            education_group_year=self.training_education_group_year,
            domain=old_domain
        )

        new_entity_version = MainEntityVersionFactory()
        PersonEntityFactory(person=self.person, entity=new_entity_version.entity)
        list_domains = [domain.pk for domain in self.domains]
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.an_training_education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'secondary_domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "constraint_type": "",
        }
        response = self.client.post(self.training_url, data=data)
        self.assertEqual(response.status_code, 302)

        self.training_education_group_year.refresh_from_db()
        self.assertEqual(self.training_education_group_year.title, 'Cours au choix')
        self.assertEqual(self.training_education_group_year.title_english, 'deaze')
        self.assertEqual(self.training_education_group_year.credits, 42)
        self.assertEqual(self.training_education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.training_education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.training_education_group_year.management_entity, new_entity_version.entity)
        self.assertEqual(self.training_education_group_year.administration_entity, new_entity_version.entity)
        self.assertListEqual(
            list(self.training_education_group_year.secondary_domains.values_list('id', flat=True)),
            list_domains
        )
        self.assertNotIn(old_domain, self.education_group_year.secondary_domains.all())

    def test_post_training_with_end_year(self):
        new_entity_version = MainEntityVersionFactory()
        PersonEntityFactory(person=self.person, entity=new_entity_version.entity)
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.an_training_education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'management_entity': new_entity_version.pk,
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'secondary_domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'active': ACTIVE,
            'schedule_type': DAILY,
            "internship": internship_presence.NO,
            "primary_language": LanguageFactory().pk,
            "start_year": 2010,
            "end_year": 2018,
            "constraint_type": "",
        }
        response = self.client.post(self.training_url, data=data)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(
            messages[1], _("Education group year %(acronym)s (%(academic_year)s) successfuly deleted.") % {
                "acronym": self.training_education_group_year_1.acronym,
                "academic_year": self.training_education_group_year_1.academic_year,
            }
        )
        self.assertEqual(
            messages[2], _("Education group year %(acronym)s (%(academic_year)s) successfuly deleted.") % {
                "acronym": self.training_education_group_year_2.acronym,
                "academic_year": self.training_education_group_year_2.academic_year,
            }
        )


class TestGetSuccessRedirectUrl(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.education_group_year = EducationGroupYearFactory(
            academic_year=self.current_academic_year
        )

        self.ac_year_in_future = GenerateAcademicYear(
            start_year=self.current_academic_year.year + 1,
            end_year=self.current_academic_year.year + 5,
        )

        self.education_group_year_in_future = []
        for ac_in_future in self.ac_year_in_future.academic_years:
            self.education_group_year_in_future.append(EducationGroupYearFactory(
                education_group=self.education_group_year.education_group,
                academic_year=ac_in_future
            ))

    def test_get_redirect_success_url_when_exist(self):
        expected_url = reverse("education_group_read", args=[self.education_group_year.pk,
                                                             self.education_group_year.id])
        result = _get_success_redirect_url(self.education_group_year, self.education_group_year)
        self.assertEqual(result, expected_url)

    def test_get_redirect_success_url_when_current_viewed_has_been_deleted(self):
        current_viewed = self.education_group_year_in_future[-1]
        current_viewed.delete()
        # Expected URL is the latest existing [-2]
        expected_url = reverse("education_group_read", args=[self.education_group_year_in_future[-2].pk,
                                                             self.education_group_year_in_future[-2].pk])
        result = _get_success_redirect_url(current_viewed, current_viewed)
        self.assertEqual(result, expected_url)


@override_flag('education_group_attach', active=True)
@override_flag('education_group_select', active=True)
@override_flag('education_group_update', active=True)
class TestSelectAttach(TestCase):
    def setUp(self):
        self.locmem_cache = cache
        self.locmem_cache.clear()
        self.patch = patch.object(management, 'cache', self.locmem_cache)
        self.patch.start()

        self.person = PersonFactory()
        self.client = Client()
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch(
            "base.business.group_element_years.perms.is_eligible_to_create_group_element_year",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()

        self.academic_year = create_current_academic_year()
        self.child_education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        self.learning_unit_year = LearningUnitYearFactory(academic_year=self.academic_year)
        self.initial_parent_education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        self.new_parent_education_group_year = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__learning_unit_child_allowed=True
        )

        self.initial_group_element_year = GroupElementYearFactory(
            parent=self.initial_parent_education_group_year,
            child_branch=self.child_education_group_year
        )

        self.child_group_element_year = GroupElementYearFactory(
            parent=self.initial_parent_education_group_year,
            child_branch=None,
            child_leaf=self.learning_unit_year
        )

        self.url_select_education_group = reverse(
            "education_group_select",
            args=[
                self.initial_parent_education_group_year.id,
                self.child_education_group_year.id,
            ]
        )
        self.url_select_learning_unit = reverse(
            "learning_unit_select",
            args=[self.learning_unit_year.id]
        )
        group_above_new_parent = GroupElementYearFactory(child_branch=self.new_parent_education_group_year)

        self.url_management = reverse("education_groups_management")
        self.select_data = {
            "root_id": group_above_new_parent.parent.id,
            "element_id": self.child_education_group_year.id,
            "group_element_year_id": self.initial_group_element_year.id,
            "action": "select",
        }
        self.root = group_above_new_parent.parent
        self.attach_data = {
            "root_id": group_above_new_parent.parent.id,
            "element_id": self.new_parent_education_group_year.id,
            "group_element_year_id": group_above_new_parent.id,
            "action": "attach",
        }

        cache.set('child_to_cache_id', None, timeout=None)

    def tearDown(self):
        cache.set('child_to_cache_id', None, timeout=None)
        self.patch.stop()
        self.client.logout()
        self.perm_patcher.stop()

    def test_select_case_education_group(self):
        response = self.client.post(
            self.url_management,
            data=self.select_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data_cached = cache.get(management.SELECT_CACHE_KEY)

        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(data_cached, dict)
        self.assertEqual(int(data_cached['id']), self.child_education_group_year.id)
        self.assertEqual(data_cached['modelname'], management.EDUCATION_GROUP_YEAR)

    def test_select_ajax_case_learning_unit_year(self):
        response = self.client.post(
            self.url_select_learning_unit,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data_cached = cache.get(management.SELECT_CACHE_KEY)

        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(data_cached, dict)
        self.assertEqual(int(data_cached['id']), self.learning_unit_year.id)
        self.assertEqual(data_cached['modelname'], management.LEARNING_UNIT_YEAR)

    def test_select_case_learning_unit_year(self):
        """In this test, we ensure that redirect is made if the request is not in AJAX """
        response = self.client.post(self.url_select_learning_unit)

        # Verify cache
        data_cached = cache.get(management.SELECT_CACHE_KEY)
        self.assertIsInstance(data_cached, dict)
        self.assertEqual(int(data_cached['id']), self.learning_unit_year.id)
        self.assertEqual(data_cached['modelname'], management.LEARNING_UNIT_YEAR)

        # Verify redirection
        redirected_url = reverse('learning_unit', args=[self.learning_unit_year.id])
        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)

    def test_attach_case_child_education_group_year(self):
        AuthorizedRelationshipFactory(
            parent_type=self.new_parent_education_group_year.education_group_type,
            child_type=self.child_education_group_year.education_group_type,
        )

        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        self._assert_link_with_inital_parent_present()

        # Select :
        self.client.post(
            self.url_management,
            data=self.select_data
        )

        # Attach :
        self.client.post(
            reverse("education_group_attach",
                    args=[self.attach_data["root_id"],
                          self.attach_data["element_id"]]),
        )

        expected_group_element_year_count = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).count()
        self.assertEqual(expected_group_element_year_count, 1)

        self._assert_link_with_inital_parent_present()

    def test_attach_case_child_education_group_year_without_authorized_relationship_fails(self):
        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        self._assert_link_with_inital_parent_present()

        # Select :
        self.client.post(
            self.url_management,
            data=self.select_data
        )

        response = self.client.get(
            reverse("education_group_attach", args=[self.root.pk, self.new_parent_education_group_year.pk])
        )
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            _("You cannot attach \"%(child)s\" (type \"%(child_type)s\") "
              "to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                'child': self.child_education_group_year,
                'child_type': self.child_education_group_year.education_group_type,
                'parent': self.new_parent_education_group_year,
                'parent_type': self.new_parent_education_group_year.education_group_type,
            }
        )

        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        self._assert_link_with_inital_parent_present()

    def test_attach_child_education_group_year_to_one_of_its_descendants_creating_loop(self):
        # We attempt to create a loop : child --> initial_parent --> new_parent --> child
        GroupElementYearFactory(
            parent=self.new_parent_education_group_year,
            child_branch=self.initial_parent_education_group_year
        )
        AuthorizedRelationshipFactory(
            parent_type=self.child_education_group_year.education_group_type,
            child_type=self.new_parent_education_group_year.education_group_type,
        )

        # Select :
        self.client.post(
            self.url_select_education_group,
            data={'element_id': self.new_parent_education_group_year.id}
        )

        # Attach :
        response = self.client.post(
            reverse("education_group_attach", args=[
                self.new_parent_education_group_year.id, self.child_education_group_year.id
            ]),
            data={}
        )
        self.assertFormError(
            response, 'form', '__all__',
            _("It is forbidden to attach an element to one of its included elements.")
        )

        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.child_education_group_year,
            child_branch=self.new_parent_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

    def test_attach_case_child_education_group_year_without_person_entity_link_fails(self):
        self.mocked_perm.return_value = False
        AuthorizedRelationshipFactory(
            parent_type=self.new_parent_education_group_year.education_group_type,
            child_type=self.child_education_group_year.education_group_type,
        )
        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        self._assert_link_with_inital_parent_present()

        # Select :
        self.client.post(
            self.url_management,
            data=self.select_data
        )

        # Attach :
        response = self.client.get(
            reverse("education_group_attach", args=[self.root.pk, self.new_parent_education_group_year.pk])
        )

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        self._assert_link_with_inital_parent_present()

    def test_attach_case_child_learning_unit_year(self):
        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_leaf=self.learning_unit_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        cache.set(
            management.SELECT_CACHE_KEY,
            {'id': self.learning_unit_year.pk, 'modelname': management.LEARNING_UNIT_YEAR},
            timeout=None,
        )

        response = self.client.post(
            reverse("education_group_attach", args=[self.root.pk, self.new_parent_education_group_year.pk]),
            data={}
        )
        self.assertEqual(response.status_code, 302)

        expected_group_element_year_count = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_leaf=self.learning_unit_year
        ).count()
        self.assertEquals(expected_group_element_year_count, 1)

    def test_attach_without_selecting_gives_warning(self):
        cache.set(management.SELECT_CACHE_KEY, None, timeout=None, )

        expected_absent_group_element_year = GroupElementYear.objects.filter(
            parent=self.new_parent_education_group_year,
            child_branch=self.child_education_group_year
        ).exists()
        self.assertFalse(expected_absent_group_element_year)

        response = self.client.get(
            reverse("education_group_attach",
                    args=[self.root.pk,
                          self.new_parent_education_group_year.pk]),
        )
        self.assertEqual(response.status_code, 200)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), _("Please Select or Move an item before Attach it"))

    def _assert_link_with_inital_parent_present(self):
        expected_initial_group_element_year = GroupElementYear.objects.get(
            parent=self.initial_parent_education_group_year,
            child_branch=self.child_education_group_year
        )
        self.assertEqual(expected_initial_group_element_year, self.initial_group_element_year)


class TestCertificateAimAutocomplete(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory()
        self.url = reverse("certificate_aim_autocomplete")
        self.certificate_aim = CertificateAimFactory(
            code=1234,
            section=5,
            description="description",
        )

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url, data={'q': '1234'})
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(results, [])

    def test_when_param_is_digit_assert_searching_on_code(self):
        # When searching on "code"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': '1234'})
        self._assert_result_is_correct(response)

    def test_assert_searching_on_description(self):
        # When searching on "description"
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'q': 'descr'})
        self._assert_result_is_correct(response)

    def test_with_filter_by_section(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(self.url, data={'forward': '{"section": "5"}'})
        self._assert_result_is_correct(response)

    def _assert_result_is_correct(self, response):
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        results = json.loads(json_response)['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.certificate_aim.id))
