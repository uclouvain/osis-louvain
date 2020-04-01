############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
import datetime

import reversion
from django.contrib.auth.models import Permission
from django.http import HttpResponseForbidden
from django.test import TestCase, Client
from django.urls import reverse

from base.models.enums import learning_unit_year_subtypes, learning_container_year_types
from base.models.enums.academic_calendar_type import LEARNING_UNIT_EDITION_FACULTY_MANAGERS
from base.models.enums.groups import UE_FACULTY_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.tests.business.test_perms import create_person_with_permission_and_group
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFullFactory
from base.tests.factories.person import PersonFactory, FacultyManagerFactory, UEFacultyManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory
from base.views.learning_units.detail import SEARCH_URL_PART


class TestLearningUnitDetailView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year, *cls.academic_years = AcademicYearFactory.produce_in_future(quantity=8)

        AcademicCalendarFactory(
            data_year=cls.current_academic_year,
            start_date=datetime.datetime(cls.current_academic_year.year - 2, 9, 15),
            end_date=datetime.datetime(cls.current_academic_year.year + 1, 9, 14),
            reference=LEARNING_UNIT_EDITION_FACULTY_MANAGERS
        )
        cls.a_superuser = SuperUserFactory()
        cls.person = PersonFactory(user=cls.a_superuser)

    def setUp(self):
        self.client.force_login(self.a_superuser)

    def test_learning_unit_read(self):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)

        header = {'HTTP_REFERER': SEARCH_URL_PART}
        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]), **header)

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(response.context['learning_unit_year'], learning_unit_year)
        self.assertEqual(self.client.session['search_url'], SEARCH_URL_PART)

    def test_learning_unit_read_versions(self):
        learning_unit_year = LearningUnitYearFullFactory(
            academic_year=self.current_academic_year,
        )
        LearningComponentYearFactory(learning_unit_year=learning_unit_year)

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 0)

        with reversion.create_revision():
            learning_unit_year.learning_container_year.save()

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 1)

        with reversion.create_revision():
            learning_unit_year.learningcomponentyear_set.first().save()

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))
        self.assertEqual(len(response.context['versions']), 2)

    def test_external_learning_unit_read(self):
        external_learning_unit_year = ExternalLearningUnitYearFactory(
            learning_unit_year__subtype=learning_unit_year_subtypes.FULL,
        )
        learning_unit_year = external_learning_unit_year.learning_unit_year

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(response.context['learning_unit_year'], learning_unit_year)

    def test_external_learning_unit_read_permission_denied(self):
        learning_container_year = LearningContainerYearFactory(academic_year=self.current_academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        external_learning_unit_year = ExternalLearningUnitYearFactory(learning_unit_year=learning_unit_year)
        learning_unit_year = external_learning_unit_year.learning_unit_year

        a_user_without_perms = PersonFactory().user
        client = Client()
        client.force_login(a_user_without_perms)

        response = client.get(reverse("learning_unit", args=[learning_unit_year.id]))
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

        a_user_without_perms.user_permissions.add(
            Permission.objects.get(codename='can_access_externallearningunityear'))

        response = client.get(reverse("learning_unit", args=[learning_unit_year.id]))
        self.assertEqual(response.status_code, 200)

    def test_learning_unit_with_faculty_manager_when_can_edit_end_date(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.OTHER_COLLECTIVE,
            requirement_entity=EntityFactory(),
        )
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        EntityVersionFactory(entity=learning_container_year.requirement_entity)

        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()
        ue_manager = UEFacultyManagerFactory(
            'can_edit_learningunit',
            'can_access_learningunit',
            'can_edit_learningunit_date'
        )
        managers = [
            FacultyManagerFactory('can_edit_learningunit', 'can_access_learningunit', 'can_edit_learningunit_date'),
            ue_manager
        ]

        for manager in managers:
            PersonEntityFactory(
                entity=learning_container_year.requirement_entity,
                person=manager
            )
            url = reverse("learning_unit", args=[learning_unit_year.id])
            self.client.force_login(manager.user)

            response = self.client.get(url)
            self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_of_type_partim_with_faculty_manager(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=EntityFactory(),
        )
        LearningUnitYearFactory(academic_year=self.current_academic_year,
                                learning_container_year=learning_container_year,
                                subtype=learning_unit_year_subtypes.FULL)
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.PARTIM)
        EntityVersionFactory(entity=learning_container_year.requirement_entity)
        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()
        ue_manager = create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP, 'can_edit_learningunit')
        ue_manager.user.user_permissions.add(Permission.objects.get(codename='can_access_learningunit'))
        managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP, 'can_edit_learningunit'),
            ue_manager
        ]
        for manager in managers:
            manager.user.user_permissions.add(Permission.objects.get(codename='can_edit_learningunit_date'))
            manager.user.user_permissions.add(Permission.objects.get(codename='can_access_learningunit'))
            PersonEntityFactory(entity=learning_container_year.requirement_entity, person=manager)
            url = reverse("learning_unit", args=[learning_unit_year.id])
            self.client.force_login(manager.user)

            response = self.client.get(url)
            self.assertEqual(response.context["can_edit_date"], True)

    def test_learning_unit_with_faculty_manager_when_cannot_edit_end_date(self):
        learning_container_year = LearningContainerYearFactory(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=EntityFactory(),
        )
        learning_unit_year = LearningUnitYearFactory(academic_year=self.current_academic_year,
                                                     learning_container_year=learning_container_year,
                                                     subtype=learning_unit_year_subtypes.FULL)
        EntityVersionFactory(entity=learning_container_year.requirement_entity)
        learning_unit_year.learning_unit.end_year = None
        learning_unit_year.learning_unit.save()
        managers = [
            FacultyManagerFactory('can_access_learningunit'),
        ]
        for manager in managers:
            PersonEntityFactory(entity=learning_container_year.requirement_entity, person=manager)
            url = reverse("learning_unit", args=[learning_unit_year.id])
            self.client.force_login(manager.user)

            response = self.client.get(url)
            self.assertEqual(response.context["can_edit_date"], False)

    def test_get_partims_identification_tabs(self):
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

        response = self.client.get(reverse('learning_unit', args=[learning_unit_year.pk]))

        self.assertTemplateUsed(response, 'learning_unit/identification.html')
        self.assertEqual(len(response.context['learning_container_year_partims']), 3)
