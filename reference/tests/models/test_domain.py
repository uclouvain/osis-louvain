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
from django.test import TestCase

from reference.tests.factories.decree import DecreeFactory
from reference.tests.factories.domain import DomainFactory


class TestDomain(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.decree = DecreeFactory(name='Paysage')

    def test_str(self):
        dom = DomainFactory(decree=self.decree, code='10H', name='Test Domain')
        expected_value = "{decree}: {code} {name}".format(decree=dom.decree.name,
                                                          code=dom.code,
                                                          name=dom.name)
        self.assertEqual(str(dom), expected_value)

    def test_str_without_decree_and_code(self):
        dom = DomainFactory(decree=None, code='', name='Test Domain')
        expected_value = "{name}".format(name=dom.name)
        self.assertEqual(str(dom), expected_value)

    def test_str_without_decree(self):
        dom = DomainFactory(decree=None, code='10H', name='Test Domain')
        expected_value = "{code} {name}".format(code=dom.code,
                                                name=dom.name)
        self.assertEqual(str(dom), expected_value)

    def test_str_without_code(self):
        dom = DomainFactory(decree=self.decree, code='', name='Test Domain')
        expected_value = "{decree}: {name}".format(decree=dom.decree.name,
                                                   name=dom.name)
        self.assertEqual(str(dom), expected_value)

    def test_sorting_domain(self):
        expected_value = ('-decree__name', 'code', 'name')
        domain = DomainFactory(
            decree=self.decree,
            code='11',
            name='Test1'
        )
        self.assertEqual(domain._meta.ordering, expected_value)
