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
from django.forms import formset_factory
from internship.forms import form_offer_preference


class TestOfferPreferenceFormset(TestCase):
    def setUp(self):
        self.FormsetOfferPreference = formset_factory(form_offer_preference.OfferPreferenceForm,
                                                      formset=form_offer_preference.OfferPreferenceFormSet)

    def test_invalid_same_preference(self):
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-offer': '4',
            'form-0-preference': '1',
            'form-0-priority': 'on',
            'form-1-offer': '5',
            'form-1-preference': '1',
            'form+1-priority': 'on'
        }

        formset = self.FormsetOfferPreference(data)
        self.assertFalse(formset.is_valid())

    def test_invalid_same_offer(self):
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-offer': '4',
            'form-0-preference': '1',
            'form-0-priority': 'on',
            'form-1-offer': '4',
            'form-1-preference': '2',
            'form-1-priority': 'on',
        }

        formset = self.FormsetOfferPreference(data)
        self.assertFalse(formset.is_valid())

    def test_valid_formset(self):
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-offer': '4',
            'form-0-preference': '1',
            'form-0-priority': 'on',
            'form-1-offer': '5',
            'form-1-preference': '2',
            'form-1-priority': 'on',
        }

        formset = self.FormsetOfferPreference(data)
        self.assertTrue(formset.is_valid())

        data = {'form-TOTAL_FORMS': '4',
                'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '4',
                'form-MAX_NUM_FORMS': '4',
                'form-0-offer': '10',
                'form-0-preference': '1',
                'form-0-priority': 'off',
                'form-1-offer': '25',
                'form-1-preference': '2',
                'form-1-priority': 'off',
                'form-2-offer': '3',
                'form-2-preference': '3',
                'form-2-priority': 'off',
                'form-3-offer': '89',
                'form-3-preference': '4',
                'form-3-priority': 'off',
                }
        formset = self.FormsetOfferPreference(data)
        self.assertTrue(formset.is_valid())