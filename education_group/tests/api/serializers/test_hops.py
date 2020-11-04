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
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.models.hops import Hops
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.hops import HopsFactory
from education_group.api.serializers.hops import HopsListSerializer
from education_group.api.views.hops import HopsList


class HopsListSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.hops = HopsFactory(education_group_year__academic_year=cls.academic_year)
        ares_ability = Hops.objects.filter(
            education_group_year__academic_year=cls.academic_year
        ).values_list('ares_ability', flat=True)
        url = reverse('education_group_api_v1:' + HopsList.name, kwargs={'year': cls.academic_year.year})
        cls.serializer = HopsListSerializer(ares_ability, context={
            'request': RequestFactory().get(url),
            'language': settings.LANGUAGE_CODE_EN
        })

    def test_contains_expected_fields(self):
        expected_fields = [
            'count',
            'ares_abilities',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)
