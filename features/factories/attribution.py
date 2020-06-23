# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import random

import factory

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from base.models.academic_year import current_academic_year
from base.models.learning_unit_year import LearningUnitYear
from base.models.tutor import Tutor


class AttributionGenerator:
    def __init__(self):
        self.tutors = list(Tutor.objects.all())
        luys_to_attribute = LearningUnitYear.objects.filter(
            academic_year=current_academic_year()
        ).prefetch_related(
            "learningcomponentyear_set"
        )
        for luy in luys_to_attribute:
            self._attribute_tutors_to_learning_unit_year(luy)

    def _attribute_tutors_to_learning_unit_year(self, luy: LearningUnitYear):
        number_tutors_to_attribute = random.randint(0, 3)
        tutors_to_attribute = random.sample(self.tutors, number_tutors_to_attribute)

        components = list(luy.learningcomponentyear_set.all())
        for tutor in tutors_to_attribute:
            AttributionChargeNewFactory.create_batch(
                len(components),
                attribution__tutor=tutor,
                learning_component_year=factory.Iterator(components)
            )