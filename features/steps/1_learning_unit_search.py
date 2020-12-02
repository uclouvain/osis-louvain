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
from behave import *

from attribution.tests.factories.attribution import AttributionFactory
from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.models.academic_year import AcademicYear
from base.models.learning_unit_year import LearningUnitYear

use_step_matcher("parse")


@given("{person} est tuteur de {luys} en {year}")
def step_impl(context, person, luys, year):
    """
    :type context: behave.runner.Context
    """
    ac_year = AcademicYear.objects.get(year=year[:4])
    luys = LearningUnitYear.objects.filter(acronym__in=luys.split(','), academic_year=ac_year)
    for luy in luys:
        # Use all possible factories. I have no idea which is the good one.
        attribution = AttributionNewFactory(
            learning_container_year=luy.learning_container_year,
            tutor__person__last_name=person,
            start_year=ac_year.year,
        )

        AttributionFactory(
            learning_unit_year=luy,
            tutor__person__last_name=person,
            start_year=ac_year.year,
        )

        AttributionChargeNewFactory(
            learning_component_year=luy.learningcomponentyear_set.first(),
            attribution=attribution
        )
