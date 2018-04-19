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
import random
from unittest import mock

import factory.fuzzy
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

import base.business.learning_unit
from base.business import learning_unit as learning_unit_business
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm
from base.forms.learning_unit.search_form import LearningUnitYearForm, SearchForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm, SummaryModelForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models import learning_unit_component
from base.models import learning_unit_component_class
from base.models.academic_year import AcademicYear
from base.models.bibliography import Bibliography
from base.models.enums import entity_container_year_link_type, active_status
from base.models.enums import internship_subtypes
from base.models.enums import learning_container_year_types, organization_type, entity_type
from base.models.enums import learning_unit_periodicity
from base.models.enums import learning_unit_year_session
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_container_year_types import LEARNING_CONTAINER_YEAR_TYPES_MUST_HAVE_SAME_ENTITIES
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.person import FACULTY_MANAGER_GROUP
from base.models.person_entity import PersonEntity
from base.models.learning_achievements import LearningAchievements

from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_achievements import LearningAchievementsFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_component_class import LearningUnitComponentClassFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from base.views.learning_unit import learning_unit_components, learning_class_year_edit, learning_unit_specifications
from base.views.learning_unit import learning_unit_identification
from base.views.learning_units.search import learning_units
from base.views.learning_units.search import learning_units_service_course
from base.views.learning_units.update import learning_unit_pedagogy
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from osis_common.document import xls_build
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory
from base.views.learning_achievement import delete
from django.core.exceptions import PermissionDenied


class TestLearningAchievementView(TestCase):
    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        self.language_fr = LanguageFactory(code="FR")
        self.user = UserFactory()
        PersonFactory(user=self.user)
        self.client.force_login(self.user)
        self.achievement_fr = LearningAchievementsFactory(language=self.language_fr,
                                                          learning_unit_year=self.learning_unit_year,
                                                          order=0)

    def test_delete_method_not_allowed(self):
        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete, args=[self.achievement_fr.id]))
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            delete(request, self.achievement_fr.id)

    def test_delete_redirection(self):
        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete, args=[self.achievement_fr.id]))
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        request.user = self.user

        response = delete(request, self.achievement_fr.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         "/learning_units/{}/specifications/".format(self.achievement_fr.learning_unit_year.id))


class TestLearningAchievementActions(TestCase):

    def setUp(self):
        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL
        )

        self.language_fr = LanguageFactory(code="FR")
        self.language_en = LanguageFactory(code="EN")
        self.user = UserFactory()
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))

        PersonFactory(user=self.user)
        self.client.force_login(self.user)

    def test_delete(self):
        achievement_fr_0 = LearningAchievementsFactory(language=self.language_fr,
                                                       learning_unit_year=self.learning_unit_year,
                                                       order=0)
        achievement_en_0 = LearningAchievementsFactory(language=self.language_en,
                                                       learning_unit_year=self.learning_unit_year,
                                                       order=0)
        achievement_fr_1 = LearningAchievementsFactory(language=self.language_fr,
                                                       learning_unit_year=self.learning_unit_year,
                                                       order=1)
        LearningAchievementsFactory(language=self.language_en,
                                    learning_unit_year=self.learning_unit_year,
                                    order=1)
        request_factory = RequestFactory()
        request = request_factory.get(reverse(delete, args=[achievement_fr_1.id]))
        request.user = self.user
        delete(request, achievement_fr_1.id)
        self.assertCountEqual(LearningAchievements.objects.all(), [achievement_fr_0,
                                                                   achievement_en_0])
