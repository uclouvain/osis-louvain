##############################################################################
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
##############################################################################
from _decimal import Decimal
from typing import List

from attribution.ddd.domain.attribution import Attribution
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.quadrimesters import DerogationQuadrimester
from learning_unit.ddd.domain.achievement import Achievement
from learning_unit.ddd.domain.description_fiche import DescriptionFiche
from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
from learning_unit.ddd.domain.proposal import Proposal
from learning_unit.ddd.domain.specifications import Specifications
from learning_unit.ddd.domain.teaching_material import TeachingMaterial


class LecturingVolume:
    def __init__(
        self,
        total_annual: Decimal = None,
        first_quadrimester: Decimal = None,
        second_quadrimester: Decimal = None,
        classes_count: int = None,
    ):
        self.total_annual = total_annual
        self.first_quadrimester = first_quadrimester
        self.second_quadrimester = second_quadrimester
        self.classes_count = classes_count


class PracticalVolume:
    def __init__(
            self,
            total_annual: Decimal = None,
            first_quadrimester: Decimal = None,
            second_quadrimester: Decimal = None,
            classes_count: int = None,
    ):
        self.total_annual = total_annual
        self.first_quadrimester = first_quadrimester
        self.second_quadrimester = second_quadrimester
        self.classes_count = classes_count


class Entities:
    def __init__(
            self,
            requirement_entity_acronym: str = None,
            allocation_entity_acronym: str = None,
    ):
        self.requirement_entity_acronym = requirement_entity_acronym
        self.allocation_entity_acronym = allocation_entity_acronym


class LearningUnitYear:
    def __init__(
            self,
            entity_id: LearningUnitYearIdentity = None,
            id: int = None,
            year: int = None,
            acronym: str = None,
            type: LearningContainerYearType = None,
            common_title_fr: str = '',
            specific_title_fr: str = '',
            common_title_en: str = '',
            specific_title_en: str = '',
            start_year: int = None,
            end_year: int = None,
            proposal: Proposal = None,
            credits: Decimal = None,
            status: bool = None,
            periodicity: PeriodicityEnum = None,
            other_remark: str = None,
            quadrimester: DerogationQuadrimester = None,

            lecturing_volume: LecturingVolume = None,
            practical_volume: PracticalVolume = None,
            achievements: List['Achievement'] = None,

            entities: Entities = None,

            description_fiche: DescriptionFiche = None,
            specifications: Specifications = None,

            teaching_materials: List[TeachingMaterial] = None,
            subtype: str = None,
            session: str = None,
            main_language: str = None,
            attributions: List['Attribution'] = None,

    ):
        self.entity_id = entity_id
        self.id = id
        self.year = year
        self.acronym = acronym
        self.type = type
        self.common_title_fr = common_title_fr or ''
        self.specific_title_fr = specific_title_fr or ''
        self.common_title_en = common_title_en or ''
        self.specific_title_en = specific_title_en or ''
        self.start_date = start_year
        self.end_date = end_year
        self.proposal = proposal
        self.credits = credits
        self.status = status
        self.periodicity = periodicity
        self.other_remark = other_remark
        self.quadrimester = quadrimester
        self.lecturing_volume = lecturing_volume
        self.practical_volume = practical_volume
        self.achievements = achievements or []
        self.entities = entities
        self.description_fiche = description_fiche
        self.specifications = specifications
        self.teaching_materials = teaching_materials or []
        self.subtype = subtype
        self.session = session
        self.main_language = main_language
        self.attributions = attributions or []

    @property
    def full_title_fr(self):
        full_title = self.common_title_fr
        if self.specific_title_fr:
            full_title += ' - {}'.format(self.specific_title_fr)
        return full_title

    @property
    def full_title_en(self):
        full_title = self.common_title_en
        if self.specific_title_en:
            full_title += ' - {}'.format(self.specific_title_en)
        return full_title
