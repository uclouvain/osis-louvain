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

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.utils import timezone

from base.models import synchronization


def create_synchronization(date=None):
    if date is None:
        date = timezone.now()
    sync = synchronization.Synchronization(date=date)
    sync.save()
    return sync


class MultipleSynchronizationTest(TestCase):

    def setUp(self):
        self.current_year = timezone.now().year
        sync_date = datetime.datetime(self.current_year, 10, 28, 20, 00, 59, 99999,
                                      tzinfo=timezone.get_current_timezone())
        create_synchronization(date=sync_date)
        sync_date = datetime.datetime(self.current_year, 10, 28, 20, 1, 0, 0,
                                      tzinfo=timezone.get_current_timezone())
        self.latest_sync_id = create_synchronization(date=sync_date).id
        sync_date = datetime.datetime(self.current_year, 10, 27, 23, 59, 59, 99999,
                                      tzinfo=timezone.get_current_timezone())
        create_synchronization(date=sync_date)

    def test_find_last_synchronization_date(self):
        sync = synchronization.Synchronization.objects.get(pk=self.latest_sync_id)
        self.assertEqual(sync.date, synchronization.find_last_synchronization_date())


class NonExistingSynchronizationTest(TestCase):

    def test_find_last_synchronization_date(self):
        self.assertRaises(ObjectDoesNotExist, synchronization.find_last_synchronization_date())
