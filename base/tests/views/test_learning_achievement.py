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
from unittest import mock

from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from waffle.models import Flag
from waffle.testutils import override_flag

from base.business.learning_units.achievement import DELETE, DOWN, UP
from base.forms.learning_achievement import LearningAchievementEditForm
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_achievement import LearningAchievement
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory, get_current_year
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import SuperUserFactory
from base.tests.factories.user import UserFactory
from base.views.learning_achievement import operation, management, create, create_first
from cms.tests.factories.text_label import TextLabelFactory
from reference.models.language import FR_CODE_LANGUAGE
from reference.tests.factories.language import LanguageFactory


@override_flag('learning_achievement_update', active=True)
class TestLearningAchievementView(TestCase):
    def setUp(self):
        self.language_fr = LanguageFactory(code="FR")
        self.language_en = LanguageFactory(code="EN")
        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.person_entity = PersonEntityFactory(person=self.person)

        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year__requirement_entity=self.person_entity.entity,
        )
        self.client.force_login(self.user)
        self.achievement_fr = LearningAchievementFactory(
            language=self.language_fr,
            learning_unit_year=self.learning_unit_year,
            order=0
        )
        self.achievement_en = LearningAchievementFactory(
            language=self.language_en,
            learning_unit_year=self.learning_unit_year,
            order=0,
            code_name=self.achievement_fr.code_name
        )
        self.reverse_learning_unit_yr = reverse('learning_unit', args=[self.learning_unit_year.id])
        flag, created = Flag.objects.get_or_create(name='learning_achievement_update')
        flag.users.add(self.user)

    def test_operation_method_not_allowed(self):
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse('achievement_management', args=[self.achievement_fr.learning_unit_year.id]),
            data={'achievement_id': self.achievement_fr.id, 'action': DELETE}
        )
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        with self.assertRaises(PermissionDenied):
            management(request, self.achievement_fr.learning_unit_year.id)

    def test_delete_redirection(self):
        request_factory = RequestFactory()
        request = request_factory.post(
            reverse('achievement_management', args=[self.achievement_fr.learning_unit_year.id]),
            data={'achievement_id': self.achievement_fr.id, 'action': DELETE}
        )
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        request.user = self.user
        response = management(request, self.achievement_fr.learning_unit_year.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         "/learning_units/{}/specifications/".format(self.achievement_fr.learning_unit_year.id))

    def test_delete_permission_denied(self):
        self.person_entity.delete()
        request_factory = RequestFactory()
        request = request_factory.post(reverse('achievement_management',
                                               args=[self.achievement_fr.learning_unit_year.id]),
                                       data={'achievement_id': self.achievement_fr.id,
                                             'action': DELETE})
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            management(request, self.achievement_fr.learning_unit_year.id)

    def test_create_not_allowed(self):
        request_factory = RequestFactory()
        request = request_factory.get(self.reverse_learning_unit_yr)
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            create(request, self.learning_unit_year.id, self.achievement_fr.id)

        request = request_factory.post(self.reverse_learning_unit_yr)
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            create(request, self.learning_unit_year.id, self.achievement_fr.id)

    def test_create_first_not_allowed(self):
        request_factory = RequestFactory()
        request = request_factory.get(self.reverse_learning_unit_yr)
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            create_first(request, self.learning_unit_year.id)

        request = request_factory.post(self.reverse_learning_unit_yr)
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            create_first(request, self.learning_unit_year.id)

    def test_check_achievement_code(self):
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        url = reverse('achievement_check_code', args=[self.learning_unit_year.id])
        response = self.client.get(url, data={'code': self.achievement_fr.code_name})
        self.assertEqual(type(response), JsonResponse)


class TestLearningAchievementActions(TestCase):
    def setUp(self):
        self.language_fr = LanguageFactory(code="FR")
        self.language_en = LanguageFactory(code="EN")
        self.user = UserFactory()
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        self.person = PersonFactory(user=self.user)
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)
        self.superperson = PersonFactory(user=self.a_superuser)

        self.person_entity = PersonEntityFactory(person=self.superperson)

        self.academic_year = create_current_academic_year()
        self.learning_unit_year = LearningUnitYearFactory(
            academic_year=self.academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year__requirement_entity=self.person_entity.entity,
        )

    def test_delete(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=0)
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=0)
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year,
                                                      order=1)
        LearningAchievementFactory(language=self.language_en,
                                   learning_unit_year=self.learning_unit_year,
                                   order=1)
        request_factory = RequestFactory()
        request = request_factory.post(management)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request.user = self.user
        operation(request, achievement_fr_1.id, 'delete')
        self.assertCountEqual(LearningAchievement.objects.all(), [achievement_fr_0,
                                                                  achievement_en_0])

    def test_up(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_0 = achievement_fr_0.id
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_0 = achievement_en_0.id
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_1 = achievement_fr_1.id
        achievement_en_1 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_1 = achievement_en_1.id

        request_factory = RequestFactory()
        request = request_factory.post(management)
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        operation(request, achievement_fr_1.id, UP)

        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_1).order, 0)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_1).order, 0)

    def test_down(self):
        achievement_fr_0 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_0 = achievement_fr_0.id
        achievement_en_0 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_0 = achievement_en_0.id
        achievement_fr_1 = LearningAchievementFactory(language=self.language_fr,
                                                      learning_unit_year=self.learning_unit_year)
        id_fr_1 = achievement_fr_1.id
        achievement_en_1 = LearningAchievementFactory(language=self.language_en,
                                                      learning_unit_year=self.learning_unit_year)
        id_en_1 = achievement_en_1.id

        request_factory = RequestFactory()
        request = request_factory.post(reverse('achievement_management', args=[achievement_fr_0.learning_unit_year.id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        operation(request, achievement_fr_0.id, DOWN)

        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_fr_1).order, 0)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_0).order, 1)
        self.assertEqual(LearningAchievement.objects.get(pk=id_en_1).order, 0)

    def test_learning_achievement_edit(self):
        learning_achievement = LearningAchievementFactory(learning_unit_year=self.learning_unit_year)
        self.client.force_login(self.a_superuser)
        response = self.client.get(reverse('achievement_edit',
                                           args=[self.learning_unit_year.id, learning_achievement.id]),
                                   data={'achievement_id': learning_achievement.id})

        self.assertTemplateUsed(response, 'learning_unit/achievement_edit.html')
        self.assertIsInstance(response.context['form'], LearningAchievementEditForm)

    def test_learning_achievement_save(self):
        learning_achievement = LearningAchievementFactory(
            learning_unit_year=self.learning_unit_year,
            language=self.language_fr
        )
        learning_achievement_en = LearningAchievementFactory(
            learning_unit_year=self.learning_unit_year,
            language=self.language_en
        )
        response = self.client.post(reverse(
            'achievement_edit',
            kwargs={
                'learning_unit_year_id': self.learning_unit_year.id,
                'learning_achievement_id': learning_achievement.id
            }
        ),
            data={
                'code_name': 'AA1',
                'text_fr': 'Text',
                'lua_fr_id': learning_achievement.id,
                'lua_en_id': learning_achievement_en.id,
                'postpone': 0
            }
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch("cms.models.translated_text.update_or_create")
    def test_learning_achievement_save_triggers_cms_save(self, mock_translated_text_update_or_create):
        learning_achievement = LearningAchievementFactory(
            learning_unit_year=self.learning_unit_year,
            language=self.language_fr
        )
        learning_achievement_en = LearningAchievementFactory(
            learning_unit_year=self.learning_unit_year,
            language=self.language_en
        )
        TextLabelFactory(label='themes_discussed')

        self.client.post(reverse(
            'achievement_edit',
            kwargs={
                'learning_unit_year_id': self.learning_unit_year.id,
                'learning_achievement_id': learning_achievement.id
            }
        ),
            data={
                'code_name': 'AA1',
                'text_fr': 'Text',
                'lua_fr_id': learning_achievement.id,
                'lua_en_id': learning_achievement_en.id,
                'postpone': 0,
            }
        )
        self.assertTrue(mock_translated_text_update_or_create.called)

    def test_learning_achievement_create(self):
        achievement_fr = LearningAchievementFactory(language=self.language_fr,
                                                    learning_unit_year=self.learning_unit_year)

        self.client.force_login(self.a_superuser)
        response = self.client.get(reverse('achievement_create',
                                           args=[self.learning_unit_year.id, achievement_fr.id]),
                                   data={'language_code': self.language_fr.code})

        self.assertTemplateUsed(response, 'learning_unit/achievement_edit.html')
        context = response.context
        self.assertIsInstance(context['form'], LearningAchievementEditForm)
        self.assertEqual(context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(context['language_code'], self.language_fr.code)
        self.assertTrue(context['create'], self.language_fr.code)

    def test_learning_achievement_create_first(self):
        self.client.force_login(self.a_superuser)
        response = self.client.get(reverse('achievement_create_first', args=[self.learning_unit_year.id]),
                                   data={'language_code': FR_CODE_LANGUAGE})

        self.assertTemplateUsed(response, 'learning_unit/achievement_edit.html')
        context = response.context
        self.assertIsInstance(context['form'], LearningAchievementEditForm)
        self.assertEqual(context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(context['language_code'], FR_CODE_LANGUAGE)


class TestLearningAchievementPostponement(TestCase):

    @classmethod
    def setUpTestData(self):
        self.language_fr = LanguageFactory(code="FR")
        self.language_en = LanguageFactory(code="EN")
        self.user = UserFactory()
        flag, created = Flag.objects.get_or_create(name='learning_achievement_update')
        flag.users.add(self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_learningunit"))
        self.user.user_permissions.add(Permission.objects.get(codename="can_create_learningunit"))
        self.person = PersonFactory(user=self.user)
        self.person_entity = PersonEntityFactory(person=self.person)
        self.academic_years = [AcademicYearFactory(year=get_current_year()+i) for i in range(0, 5)]
        self.learning_unit = LearningUnitFactory(start_year=self.academic_years[0], end_year=self.academic_years[-1])
        self.learning_unit_years = [LearningUnitYearFactory(
            academic_year=academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year__requirement_entity=self.person_entity.entity,
            learning_unit=self.learning_unit,
            acronym="TEST0000"
        ) for academic_year in self.academic_years]

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_learning_achievement_create_with_postponement(self):
        create_response = self._create_achievements(code_name=1)
        self.assertEqual(create_response.status_code, 200)
        for achievement in LearningAchievement.objects.filter(language__code=FR_CODE_LANGUAGE):
            self.assertEqual(achievement.text, 'text')

    def test_learning_achievement_deletion_with_postponement(self):
        self._create_achievements(code_name=1)
        achievement = LearningAchievement.objects.filter(language__code=FR_CODE_LANGUAGE).first()
        operation_url = reverse('achievement_management', args=[self.learning_unit_years[0].id])
        self.client.post(operation_url, data={
            'achievement_id': achievement.id,
            'action': DELETE
        })
        self.assertFalse(LearningAchievement.objects.all().exists())

    def test_learning_achievement_move_up_with_postponement(self):
        self._move_achievement(achievement_code_name=2, operation=UP)
        self.assertEqual(LearningAchievement.objects.filter(code_name=1, order=1).count(), 10)
        self.assertEqual(LearningAchievement.objects.filter(code_name=2, order=0).count(), 10)

    def test_learning_achievement_move_down_with_postponement(self):
        self._move_achievement(achievement_code_name=1, operation=DOWN)
        self.assertEqual(LearningAchievement.objects.filter(code_name=1, order=1).count(), 10)
        self.assertEqual(LearningAchievement.objects.filter(code_name=2, order=0).count(), 10)

    def _create_achievements(self, code_name):
        create_url = reverse('achievement_create_first', args=[self.learning_unit_years[0].id])
        create_response = self.client.post(create_url, data={
            'language_code': 'fr-be',
            'code_name': code_name,
            'text_fr': 'text',
            'postpone': '1'
        })
        return create_response

    def _move_achievement(self, achievement_code_name, operation):
        for code_name in [1, 2]:
            self._create_achievements(code_name=code_name)
        operation_url = reverse('achievement_management', args=[self.learning_unit_years[0].id])
        self.client.post(operation_url, data={
            'achievement_id': LearningAchievement.objects.filter(code_name=achievement_code_name).first().id,
            'action': operation
        })
