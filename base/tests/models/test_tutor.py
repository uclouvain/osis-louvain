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
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase

from base.models import tutor
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from attribution.tests.models import test_attribution
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestTutor(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.person = PersonFactory(first_name="James", last_name="Dupont", user=self.user)
        self.tutor = TutorFactory(person=self.person)
        TutorFactory()  # Create fake Tutor
        TutorFactory()  # Create fake Tutor
        self.learning_unit_year = LearningUnitYearFactory()
        self.attribution = test_attribution.create_attribution(tutor=self.tutor,
                                                               learning_unit_year=self.learning_unit_year,
                                                               score_responsible=False,
                                                               summary_responsible=True)

    def test_find_by_person(self):
        self.assertEqual(self.tutor, tutor.find_by_person(self.person))

    def test_find_by_person_empty(self):
        person_unknown = PersonFactory()
        self.assertIsNone(tutor.find_by_person(person_unknown))

    def test_find_by_person_wrong_id(self):
        self.assertIsNone(tutor.find_by_person(-1))

    def test_is_tutor(self):
        self.assertTrue(tutor.is_tutor(self.user))

    def test_is_not_tutor(self):
        user_unknown = UserFactory()
        self.assertFalse(tutor.is_tutor(user_unknown))

    def test_find_by_user(self):
        self.assertEqual(self.tutor, tutor.find_by_user(self.user))

    def test_find_by_user_wrong_id(self):
        self.assertIsNone(tutor.find_by_user(-1))

    def test_find_by_id(self):
        self.assertEqual(self.tutor, tutor.find_by_id(self.tutor.id))

    def test_find_by_id_wrong_id(self):
        self.assertIsNone(tutor.find_by_id(-1))

    def test_find_all_summary_responsibles_by_learning_unit_year(self):
        responsibles = tutor.find_all_summary_responsibles_by_learning_unit_year(self.learning_unit_year)
        self.assertCountEqual(responsibles, [self.tutor])


class MockRequest:
    COOKIES = {}


class MockSuperUser:
    def has_perm(self, perm):
        return True


request = MockRequest()
request.user = MockSuperUser()


class TestTutorAdmin(TestCase):
    def setUp(self):
        for _ in range(10):
            user = UserFactory()
            person = PersonFactory(user=user)
            TutorFactory(person=person)
            user.groups.clear()

        self.site = AdminSite()

    def test_add_to_group(self):
        setattr(request, 'session', 'session')
        msg = FallbackStorage(request)
        setattr(request, '_messages', msg)
        tutor_admin = tutor.TutorAdmin(tutor.Tutor, self.site)
        queryset = tutor.Tutor.objects.all()
        tutor_admin.add_to_group(request, queryset)
        msg = [m.message for m in get_messages(request)]
        self.assertIn("{} users added to the group 'tutors'.".format(10), msg)

    def test_add_to_group_no_tutor_group(self):
        setattr(request, 'session', 'session')
        msg = FallbackStorage(request)
        setattr(request, '_messages', msg)
        for group in Group.objects.all():
            group.delete()
        tutor_admin = tutor.TutorAdmin(tutor.Tutor, self.site)
        queryset = tutor.Tutor.objects.all()
        tutor_admin.add_to_group(request, queryset)
        msg = [m.message for m in get_messages(request)]
        self.assertIn("Group tutors doesn't exist.", msg)


class TestSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        TUTOR_NAMES = (
            {"first_name": "Jean", "last_name": "Pierrer"},
            {"first_name": "John", "last_name": "Doe"},
            {"first_name": "Morgan", "last_name": "Wakaba"},
            {"first_name": "Philip", "last_name": "Doe"}
        )

        cls.tutors = [TutorFactory(person=PersonFactory(**name)) for name in TUTOR_NAMES]

    def test_with_no_criterias(self):
        qs = tutor.search()
        self.assertQuerysetEqual(qs, self.tutors, transform=lambda o: o, ordered=False)

    def test_with_name_criteria(self):
        for tutor_obj in self.tutors:
            with self.subTest(tutor=tutor):
                name =  " ".join([tutor_obj.person.first_name, tutor_obj.person.last_name])
                qs = tutor.search(name=name)
                self.assertQuerysetEqual(qs, [tutor_obj], transform=lambda o: o, ordered=False)
