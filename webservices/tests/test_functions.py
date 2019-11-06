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
from django.test import TestCase

from base.tests.factories.education_group_year import EducationGroupYearFactory
from webservices.views import get_title_of_education_group_year


class GetTitleOrEducationGroupYear_TestCase(TestCase):
    def test_get_title_or_education_group_year(self):
        ega = EducationGroupYearFactory(title='french', title_english='english')

        title = get_title_of_education_group_year(ega, settings.LANGUAGE_CODE_FR)
        self.assertEqual('french', title)

        title = get_title_of_education_group_year(ega, settings.LANGUAGE_CODE_EN)
        self.assertEqual('english', title)
