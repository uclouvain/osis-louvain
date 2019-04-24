##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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

from django.utils.translation import ugettext_lazy as _
from django.test import TestCase
from django.utils import timezone

from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_component_year import LearningComponentYear
from base.models.academic_year import AcademicYear

now = timezone.now()


class LearningComponentYearTest(TestCase):

    current_academic_year = None

    def setUp(self):
        self.current_academic_year = AcademicYear(year=(now.year),
                                     start_date=datetime.date(now.year, now.month, 15),
                                     end_date=datetime.date(now.year + 1, now.month, 28))
        self.current_academic_year.save()

        self.current_academic_year_different = AcademicYear(year=(now.year)-1,
                                     start_date=datetime.date(now.year-1, now.month, 15),
                                     end_date=datetime.date(now.year + 2, now.month, 28))
        self.current_academic_year_different.save()

    def test_get_basic_inconsistent_msg_no_luy(self):
        learning_container = LearningContainer()
        learning_container.save()

        learning_container_year = LearningContainerYear(common_title="Biology",
                                                        acronym="LBIO1212",
                                                        academic_year=self.current_academic_year,
                                                        learning_container=learning_container)
        learning_container_year.save()
        #Composant annualisé est associé à son composant et à son conteneur annualisé
        learning_component_year = LearningComponentYear(learning_container_year=learning_container_year,
                                                        acronym="/C",
                                                        comment="TEST")
        learning_component_year.save()
        self.assertEqual(learning_component_year._get_basic_inconsistent_msg(), _('Volumes are inconsistent'))

