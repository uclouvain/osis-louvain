############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
import random

import factory

from base.business.learning_unit_proposal import copy_learning_unit_data
from base.models.academic_year import AcademicYear, compute_max_academic_year_adjournment, current_academic_year
from base.models.campus import Campus
from base.models.entity_version import EntityVersion
from base.models.enums import learning_container_year_types
from base.models.enums.entity_type import FACULTY
from base.models.enums.organization_type import MAIN
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.learning_unit import LearningUnitFactoryWithAnnualizedData
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory

LEARNING_UNIT_START_YEAR = 2015


class LearningUnitGenerator:
    def __init__(self):
        self.entities_version = list(EntityVersion.objects.filter(entity_type=FACULTY).select_related("entity"))
        self.campuses = list(Campus.objects.filter(organization__type=MAIN))
        self.academic_years_range = AcademicYear.objects.filter(
            year__gte=LEARNING_UNIT_START_YEAR,
            year__lte=compute_max_academic_year_adjournment()
        )

        self.learning_units = self.create_courses()
        self.learning_units.extend(self.create_all_types())

        proposal_academic_year = current_academic_year().year + 1
        self.learning_units.extend(self.create_learning_units_in_creation_proposal(proposal_academic_year))
        self.learning_units.extend(self.create_learning_units_in_modification_proposal(proposal_academic_year))
        self.learning_units.extend(self.create_learning_units_in_suppression_proposal(proposal_academic_year))

    def create_courses(self):
        return self._create_learning_units(
            learningunityears__learning_container_year__container_type=learning_container_year_types.COURSE,
        )

    def create_all_types(self, n=40):
        return self._create_learning_units(n=n)

    def create_learning_units_in_creation_proposal(self, proposal_academic_year):
        proposal_academic_year_obj = next(acy for acy in self.academic_years_range if acy.year == proposal_academic_year)
        learning_units = LearningUnitFactoryWithAnnualizedData.create_batch(
            5,
            start_year__year=proposal_academic_year,
            learningunityears__academic_years=[proposal_academic_year_obj],
            learningunityears__learning_container_year__requirement_entity=factory.Iterator(
                self.entities_version, getter=lambda ev: ev.entity
            ),
            learningunityears__campus=factory.LazyFunction(lambda: random.choice(self.campuses)),
        )

        luys_obj = LearningUnitYear.objects.filter(
            learning_unit__in=learning_units,
            academic_year__year=proposal_academic_year
        ).select_related(
            "learning_container_year__requirement_entity"
        )

        for luy in luys_obj:
            ProposalLearningUnitFactory(
                learning_unit_year=luy,
                type=ProposalType.CREATION.name,
                state=ProposalState.FACULTY.name,
                entity=luy.learning_container_year.requirement_entity,
            )

        return learning_units

    def create_learning_units_in_modification_proposal(self, proposal_academic_year):
        learning_units = self.create_all_types(n=5)

        luys_obj = LearningUnitYear.objects.filter(
            learning_unit__in=learning_units,
            academic_year__year=proposal_academic_year
        ).select_related(
            "learning_container_year__requirement_entity"
        )

        for luy in luys_obj:
            ProposalLearningUnitFactory(
                learning_unit_year=luy,
                type=ProposalType.MODIFICATION.name,
                state=ProposalState.FACULTY.name,
                entity=luy.learning_container_year.requirement_entity,
                initial_data=copy_learning_unit_data(luy)
            )

        return learning_units

    def create_learning_units_in_suppression_proposal(self, proposal_academic_year):
        learning_units = self.create_all_types(n=5)

        luys_obj = LearningUnitYear.objects.filter(
            learning_unit__in=learning_units,
            academic_year__year=proposal_academic_year
        ).select_related(
            "learning_container_year__requirement_entity"
        )

        for luy in luys_obj:
            ProposalLearningUnitFactory(
                learning_unit_year=luy,
                type=ProposalType.SUPPRESSION.name,
                state=ProposalState.FACULTY.name,
                entity=luy.learning_container_year.requirement_entity,
                initial_data=copy_learning_unit_data(luy)
            )

        acy = AcademicYear.objects.get(year=proposal_academic_year)
        for lu in learning_units:
            lu.end_date = acy
            lu.save()

        return learning_units

    def _create_learning_units(self, n=60, **kwargs):
        return LearningUnitFactoryWithAnnualizedData.create_batch(
            n,
            start_year__year=LEARNING_UNIT_START_YEAR,
            learningunityears__academic_years=self.academic_years_range,
            learningunityears__learning_container_year__requirement_entity=factory.Iterator(
                self.entities_version, getter=lambda ev: ev.entity
            ),
            learningunityears__campus=factory.LazyFunction(lambda: random.choice(self.campuses)),
            **kwargs
        )
