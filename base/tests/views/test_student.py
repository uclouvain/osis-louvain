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
from unittest.mock import Mock

from django.test import TestCase, RequestFactory
from django.urls import reverse
from requests.exceptions import RequestException

from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory


class StudentsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_manager = ProgramManagerFactory(
            person=PersonWithPermissionsFactory("can_access_student")
        )

        cls.students_db = StudentFactory.create_batch(10)
        cls.url = reverse("students")

    def setUp(self):
        self.client.force_login(self.program_manager.person.user)

    def test_without_research_criteria(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'student/students.html')
        self.assertFalse(response.context['students'].object_list)

    def test_search_by_registration_id(self):
        response = self.client.get(self.url, data={'registration_id': self.students_db[0].registration_id})

        self.assertTemplateUsed(response, 'student/students.html')
        self.assertEqual(response.context['students'].object_list, [self.students_db[0]])

    def test_search_by_name(self):
        response = self.client.get(self.url, data={'name': self.students_db[1].person.last_name[:2]})

        self.assertTemplateUsed(response, 'student/students.html')
        self.assertIn(self.students_db[1], response.context['students'].object_list)


class TestStudentRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_manager = ProgramManagerFactory(
            person=PersonWithPermissionsFactory("can_access_student")
        )

    def setUp(self):
        self.client.force_login(self.program_manager.person.user)

    def test_student_read(self):
        student = StudentFactory()
        response = self.client.get(reverse('student_read', args=[student.id]))

        self.assertTemplateUsed(response, 'student/student.html')
        self.assertEqual(response.context['student'], student)


class TestStudentPicture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.program_manager = ProgramManagerFactory(
            person=PersonWithPermissionsFactory("can_access_student")
        )

        cls.student_m = StudentFactory(person=PersonFactory(last_name='Durant', first_name='Thomas', gender='M'))
        cls.student_f = StudentFactory(person=PersonFactory(last_name='Durant', first_name='Alice', gender='F'))
        cls.url = reverse("students")

    def setUp(self):
        self.client.force_login(self.program_manager.person.user)

    @mock.patch('requests.get', side_effect=RequestException)
    def test_student_picture_unknown(self, mock_request_get):
        from base.views.student import student_picture
        from django.contrib.staticfiles.storage import staticfiles_storage

        request = RequestFactory().get(reverse(student_picture, args=[self.student_m.id]))
        request.user = self.program_manager.person.user
        response = student_picture(request, self.student_m.id)

        self.assertTrue(mock_request_get.called)
        self.assertEqual(response.url, staticfiles_storage.url('img/men_unknown.png'))

        request = RequestFactory().get(reverse(student_picture, args=[self.student_f.id]))
        request.user = self.program_manager.person.user
        response = student_picture(request, self.student_f.id)

        self.assertTrue(mock_request_get.called)
        self.assertEqual(response.url, staticfiles_storage.url('img/women_unknown.png'))

    @mock.patch('requests.get')
    def test_student_picture(self, mock_request_get):
        from base.views.student import student_picture

        mock_response = Mock()
        mock_response.json.return_value = {'photo_url': 'awesome/photo.png'}
        mock_response.content = b"an image"
        mock_response.status_code = 200
        mock_request_get.return_value = mock_response

        request = RequestFactory().get(reverse(student_picture, args=[self.student_m.id]))
        request.user = self.program_manager.person.user
        response = student_picture(request, self.student_m.id)

        self.assertTrue(mock_request_get.called)
        self.assertEqual(response.content, b'an image')

    def test_student_picture_for_non_existent_student(self):
        non_existent_student_id = 666
        request = RequestFactory().get(reverse('student_picture', args=[non_existent_student_id]))
        request.user = self.program_manager.person.user

        from base.views.student import student_picture
        from django.http import Http404

        self.assertRaises(Http404, student_picture, request, non_existent_student_id)
