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

from base.models import offer_year
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.models import test_offer


def create_offer_year(acronym, title, academic_year):
    an_offer_year = offer_year.OfferYear(offer=test_offer.create_offer(title),
                                         academic_year=academic_year,
                                         acronym=acronym, title=title)
    an_offer_year.save()
    return an_offer_year


class OfferYearTest(TestCase):

    def test_get_last_offer_year_by_offer(self):
        an_offer = test_offer.create_offer("test_offer")
        academic_years = [
            AcademicYearFactory(year=2015+x) for x in range(3)
        ]
        offer_years = [
                OfferYearFactory(
                    offer=an_offer,
                    academic_year=academic_years[x],
                )
                for x in range(3)
            ]
        self.assertEqual(offer_year.get_last_offer_year_by_offer(an_offer), offer_years[2])

