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
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.contrib.auth.models import User, Permission

class ErrorViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tmp', 'tmp@gmail.com', 'tmp')
        permission = Permission.objects.get(codename='can_access_academic_calendar')
        self.user.user_permissions.add(permission)

    @override_settings(DEBUG=False)
    def test_404_error(self):
        self.client.login(username='tmp', password='tmp')
        response = self.client.get(reverse('academic_calendar_read', args=[46898]), follow=True)
        self.assertEqual(response.status_code, 404)