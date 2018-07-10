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
from unittest import mock

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.forms.education_group.group import GroupModelForm
from base.models.enums import education_group_categories
from base.models.enums.active_status import ACTIVE
from base.models.enums.schedule_type import DAILY
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import GroupFactory, TrainingFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity_version import EntityVersionFactory, MainEntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.views.education_groups.update import update_education_group
from reference.tests.factories.domain import DomainFactory


@override_flag('education_group_update', active=True)
class TestUpdate(TestCase):
    def setUp(self):
        self.education_group_year = GroupFactory()

        EntityVersionFactory(entity=self.education_group_year.management_entity,
                             start_date=self.education_group_year.academic_year.start_date)

        EntityVersionFactory(entity=self.education_group_year.administration_entity,
                             start_date=self.education_group_year.academic_year.start_date)

        self.url = reverse(update_education_group, kwargs={'education_group_year_id': self.education_group_year.pk})
        self.person = PersonFactory()

        self.client.force_login(self.person.user)
        permission = Permission.objects.get(codename='change_educationgroup')
        self.person.user.user_permissions.add(permission)
        self.perm_patcher = mock.patch("base.business.education_groups.perms.is_eligible_to_change_education_group",
                                       return_value=True)
        self.mocked_perm = self.perm_patcher.start()

        self.training_url = self._get_training_url()

        self.domains = [DomainFactory() for x in range(10)]

    def _get_training_url(self):
        self.an_training_education_group_type = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        self.training_education_group_year = TrainingFactory(
            education_group_type=self.an_training_education_group_type)
        EntityVersionFactory(entity=self.training_education_group_year.administration_entity,
                             start_date=self.education_group_year.academic_year.start_date)
        EntityVersionFactory(entity=self.training_education_group_year.management_entity,
                             start_date=self.education_group_year.academic_year.start_date)
        return reverse(update_education_group,
                       kwargs={'education_group_year_id': self.training_education_group_year.pk})

    def tearDown(self):
        self.perm_patcher.stop()

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_permission_required(self):
        response = self.client.get(self.url)

        self.mocked_perm.assert_called_once_with(self.person)

    def test_template_used(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education_group/update_groups.html")

    def test_response_context(self):
        response = self.client.get(self.url)

        form_education_group_year = response.context["form_education_group_year"]

        self.assertIsInstance(form_education_group_year, GroupModelForm)

    def test_post(self):
        new_entity_version = MainEntityVersionFactory()
        new_education_group_type = EducationGroupTypeFactory(category=education_group_categories.GROUP)

        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': new_education_group_type.id,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.education_group_year.academic_year.pk
        }
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.education_group_year.refresh_from_db()
        self.assertEqual(self.education_group_year.title, 'Cours au choix')
        self.assertEqual(self.education_group_year.title_english, 'deaze')
        self.assertEqual(self.education_group_year.credits, 42)
        self.assertEqual(self.education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.education_group_year.administration_entity, new_entity_version.entity)

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
        list_domains = [domain.pk for domain in self.domains]
        data = {
            'title': 'Cours au choix',
            'title_english': 'deaze',
            'education_group_type': self.an_training_education_group_type.pk,
            'credits': 42,
            'acronym': 'CRSCHOIXDVLD',
            'partial_acronym': 'LDVLD101R',
            'administration_entity': new_entity_version.pk,
            'main_teaching_campus': "",
            'academic_year': self.training_education_group_year.academic_year.pk,
            'domains': ['|' + ('|'.join([str(domain.pk) for domain in self.domains])) + '|'],
            'active': ACTIVE,
            'schedule_type': DAILY,
        }
        response = self.client.post(self.training_url, data=data)
        self.assertEqual(response.status_code, 302)

        self.training_education_group_year.refresh_from_db()
        self.assertEqual(self.training_education_group_year.title, 'Cours au choix')
        self.assertEqual(self.training_education_group_year.title_english, 'deaze')
        self.assertEqual(self.training_education_group_year.credits, 42)
        self.assertEqual(self.training_education_group_year.acronym, 'CRSCHOIXDVLD')
        self.assertEqual(self.training_education_group_year.partial_acronym, 'LDVLD101R')
        self.assertEqual(self.training_education_group_year.administration_entity, new_entity_version.entity)
        self.assertListEqual(
            list(self.training_education_group_year.domains.values_list('id', flat=True)),
            list_domains
        )
        self.assertNotIn(old_domain, self.education_group_year.domains.all())
