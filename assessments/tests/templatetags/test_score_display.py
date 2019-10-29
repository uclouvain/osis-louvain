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
from decimal import Decimal

from django.template import Context, Template
from django.test import TestCase


class ScoreDisplayTagTests(TestCase):
    def test_score_display_empty(self):
        out = Template(
            "{% load score_display %}"
            "{{ score | score_display:is_decimal_scores }}"
        ).render(Context({
            'score': None,
            'is_decimal_scores': False
        }))
        self.assertEqual(out, "")

    def test_score_display_hyphen_value(self):
        out = Template(
            "{% load score_display %}"
            "{{ score | score_display:is_decimal_scores }}"
        ).render(Context({
            'score': "-",
            'is_decimal_scores': False
        }))
        self.assertEqual(out, "")

    def test_score_display_not_decimal(self):
        out = Template(
            "{% load score_display %}"
            "{{ score | score_display:is_decimal_scores }}"
        ).render(Context({
            'score': Decimal(15),
            'is_decimal_scores': False
        }))
        self.assertEqual(out, "15")

    def test_score_display_with_decimal(self):
        out = Template(
            "{% load score_display %}"
            "{{ score | score_display:is_decimal_scores }}"
        ).render(Context({
            'score': Decimal(15.5),
            'is_decimal_scores': True
        }))
        self.assertEqual(out, "15.50")
