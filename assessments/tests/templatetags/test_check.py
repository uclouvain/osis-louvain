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
from unittest.mock import Mock

from django.template import Context, Template
from django.test import TestCase


class CheckTagTests(TestCase):
    def test_check_tag_empty(self):
        out = Template(
            "{% load check %}"
            "{{ offers_on|is_checked:pgm_id }}"
        ).render(Context({
            'offers_on': [],
            'pgm_id': 15
        }))
        self.assertEqual(out, "")

    def test_check_tag_checked(self):
        mock = Mock()
        mock.id = 56
        mock_2 = Mock()
        mock_2.id = 15

        out = Template(
            "{% load check %}"
            "{{ offers_on|is_checked:pgm_id }}"
        ).render(Context({
            'offers_on': [mock, mock_2],
            'pgm_id': 15
        }))
        self.assertEqual(out, "checked")
