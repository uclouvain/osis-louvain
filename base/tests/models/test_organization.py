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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase
from django.utils import timezone

from base.models.organization import Organization
from base.tests.factories.entity_version import EntityVersionFactory


class OrganizationOrderingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Should be current partner (end_date=None)
        EntityVersionFactory(
            entity__organization__name='A',
            start_date=datetime.date(2015, 1, 1),
            parent=None,
        )

        # Is not current partner (because of the end_date)
        org_c = EntityVersionFactory(
            entity__organization__name='C',
            start_date=datetime.date(2015, 1, 1),
            end_date=datetime.date(2016, 1, 1),
            parent=None,
        ).entity.organization
        EntityVersionFactory(
            entity__organization=org_c,
            start_date=datetime.date(2012, 1, 1),
            end_date=datetime.date(2015, 1, 1),
            parent=None,
        )

        # Current partner again
        cls.org_b = EntityVersionFactory(
            entity__organization__name='B',
            entity__website='http://foo.com',
            start_date=datetime.date(2015, 1, 1),
            parent=None,
        ).entity.organization
        EntityVersionFactory(
            entity__organization=cls.org_b,
            start_date=datetime.date(2013, 1, 1),
            end_date=datetime.date(2015, 1, 1),
            parent=None,
        )

        # Is not current partner too
        EntityVersionFactory(
            entity__organization__name='D',
            start_date=datetime.date(2013, 1, 1),
            end_date=datetime.date(2015, 1, 1),
            parent=None,
        )

    def test_organization_ordering(self):
        organizations = Organization.objects.all()
        result = organizations.values_list('name', flat=True)
        self.assertEqual(list(result), ['A', 'B', 'C', 'D'])

        self.assertTrue(organizations[0].is_active)
        self.assertTrue(organizations[1].is_active)
        self.assertFalse(organizations[2].is_active)
        self.assertFalse(organizations[3].is_active)

    def test_organization_properties(self):
        organizations = Organization.objects.all()

        # Verify B properties
        self.assertEqual(organizations[1].website, 'http://foo.com')
        self.assertEqual(organizations[1].start_date, datetime.date(2013, 1, 1))
        self.assertEqual(organizations[1].end_date, None)

        # Verify C properties
        self.assertEqual(organizations[2].start_date, datetime.date(2012, 1, 1))
        self.assertEqual(organizations[2].end_date, datetime.date(2016, 1, 1))

        # Verify D properties
        self.assertEqual(organizations[3].start_date, datetime.date(2013, 1, 1))
        self.assertEqual(organizations[3].end_date, datetime.date(2015, 1, 1))


class OrganizationIsActiveTest(TestCase):
    def test_is_active_case_end_date_lower_than_today(self):
        root_inactive = EntityVersionFactory(
            entity__organization__name='A',
            start_date=datetime.date(2015, 1, 1),
            end_date=timezone.now() - datetime.timedelta(days=5),
            parent=None,
        )
        self.assertFalse(
            Organization.objects.all().filter(
                name="A",
                is_active=True
            ).exists()
        )

    def test_is_active_case_end_date_greater_than_today(self):
        root_active = EntityVersionFactory(
            entity__organization__name='A',
            start_date=datetime.date(2015, 1, 1),
            end_date=timezone.now() + datetime.timedelta(days=5),
            parent=None,
        )
        self.assertTrue(
            Organization.objects.all().filter(
                name="A",
                is_active=True
            ).exists()
        )

    def test_is_active_case_end_date_is_none(self):
        root_active = EntityVersionFactory(
            entity__organization__name='A',
            start_date=datetime.date(2015, 1, 1),
            end_date=None,
            parent=None,
        )
        self.assertTrue(
            Organization.objects.all().filter(
                name="A",
                is_active=True
            ).exists()
        )
