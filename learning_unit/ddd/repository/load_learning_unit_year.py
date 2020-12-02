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
import itertools
from typing import List, Dict

from django.conf import settings
from django.db.models import F, Subquery, OuterRef, QuerySet, Q, Prefetch

from attribution.ddd.repositories.attribution_repository import AttributionRepository
from base.models.entity_version import EntityVersion
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.learning_unit_year_subtypes import LEARNING_UNIT_YEAR_SUBTYPES
from base.models.enums.quadrimesters import DerogationQuadrimester, LearningUnitYearQuadrimester
from base.models.learning_achievement import LearningAchievement as LearningAchievementModelDb
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear as LearningUnitYearModel
from learning_unit.ddd.domain.achievement import AchievementIdentity, Achievement
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear, LecturingVolume, PracticalVolume, Entities
from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
from learning_unit.ddd.domain.proposal import Proposal
from learning_unit.ddd.repository.load_description_fiche import bulk_load_description_fiche
from learning_unit.ddd.repository.load_specification import bulk_load_specification
from learning_unit.ddd.repository.load_description_fiche_force_majeure import bulk_load_force_majeures
from learning_unit.ddd.repository.load_teaching_material import bulk_load_teaching_materials


def load_multiple_by_identity(
        learning_unit_year_identities: List['LearningUnitYearIdentity']
) -> List['LearningUnitYear']:

    filter_by_identity = _build_where_clause(learning_unit_year_identities[0])

    for identity in learning_unit_year_identities[1:]:
        filter_by_identity |= _build_where_clause(identity)

    qs = __get_queryset()
    qs = qs.filter(filter_by_identity)

    # FIXME :: data from another domain : attributions cannot be in Learning Unit Year repository
    attributions = AttributionRepository.search(learning_unit_year_ids=learning_unit_year_identities)
    attributions_by_ue = __build_sorted_attributions_grouped_by_ue(attributions)

    teaching_materials_by_learning_unit_identity = bulk_load_teaching_materials(learning_unit_year_identities)
    description_fiches = bulk_load_description_fiche(learning_unit_year_identities)
    force_majeures = bulk_load_force_majeures(learning_unit_year_identities)
    specifications_set = bulk_load_specification(learning_unit_year_identities)
    results = []
    for learning_unit_data in qs:
        learning_unit_identity = LearningUnitYearIdentity(code=learning_unit_data.acronym,
                                                          year=learning_unit_data.year)
        luy = __instanciate_learning_unit_year(
            learning_unit_data,
            teaching_materials=teaching_materials_by_learning_unit_identity.get(learning_unit_identity, []),
            attributions=attributions_by_ue.get(learning_unit_identity),
            description_fiche=description_fiches[learning_unit_data.id],
            force_majeure=force_majeures[learning_unit_data.id],
            specifications=specifications_set[learning_unit_data.id]
        )

        results.append(luy)
    return results


def _build_where_clause(node_identity: 'LearningUnitYearIdentity') -> Q:
    return Q(
        acronym=node_identity.code,
        academic_year__year=node_identity.year
    )


def __build_sorted_attributions_grouped_by_ue(qs_attributions: List['Attribution']) \
        -> Dict[LearningUnitYearIdentity, List['Attribution']]:
    attributions_grouped_by_ue = {}
    for learning_unit_year_id, attributions in itertools.groupby(
            qs_attributions,
            key=lambda attribution: (attribution.learning_unit_year.code, attribution.learning_unit_year.year)
    ):
        learning_unit_identity = LearningUnitYearIdentity(code=learning_unit_year_id[0], year=learning_unit_year_id[1])
        attributions_data = [attribution for attribution in attributions]

        attributions_grouped_by_ue.update({learning_unit_identity: attributions_data})
    return attributions_grouped_by_ue


def __build_achievements(qs):
    ue_achievements = sorted(qs, key=lambda el: el.order)
    achievements = []
    for code_name, elements in itertools.groupby(ue_achievements, key=lambda el: el.order):
        elements = list(elements)
        first_element = elements[0]  # code_name and consistency_id have same values in french and english
        achievement_parameters = {
            'code_name': first_element.code_name,
            'entity_id': AchievementIdentity(consistency_id=first_element.consistency_id)
        }
        for achievement in elements:
            if achievement.language_code == settings.LANGUAGE_CODE_EN[:2].upper():
                achievement_parameters['text_en'] = achievement.text
            if achievement.language_code == settings.LANGUAGE_CODE_FR[:2].upper():
                achievement_parameters['text_fr'] = achievement.text
        achievements.append(Achievement(**achievement_parameters))

    return achievements


def __instanciate_learning_unit_year(
        learning_unit_data: LearningUnitYearModel,
        teaching_materials=None,
        attributions=None,
        description_fiche=None,
        force_majeure=None,
        specifications=None
) -> LearningUnitYear:
    learning_unit_identity = LearningUnitYearIdentity(
        code=learning_unit_data.acronym,
        year=learning_unit_data.year
    )
    achievements = __build_achievements(learning_unit_data.learningachievement_set.all())
    return LearningUnitYear(
        entity_id=learning_unit_identity,
        id=learning_unit_data.id,
        year=learning_unit_data.year,
        acronym=learning_unit_data.acronym,
        type=LearningContainerYearType[learning_unit_data.type],
        specific_title_fr=learning_unit_data.specific_title_fr,
        specific_title_en=learning_unit_data.specific_title_en,
        common_title_fr=learning_unit_data.common_title_fr,
        common_title_en=learning_unit_data.common_title_en,
        start_year=learning_unit_data.start_year,
        end_year=learning_unit_data.end_year,
        proposal=Proposal(
            type=learning_unit_data.proposal_type,
            state=learning_unit_data.proposal_state,
        ),
        credits=learning_unit_data.credits,
        status=learning_unit_data.status,
        periodicity=PeriodicityEnum[learning_unit_data.periodicity] if learning_unit_data.periodicity else None,
        other_remark=learning_unit_data.other_remark,
        quadrimester=LearningUnitYearQuadrimester[learning_unit_data.quadrimester]
        if learning_unit_data.quadrimester else None,
        lecturing_volume=LecturingVolume(
            total_annual=learning_unit_data.pm_vol_tot,
            first_quadrimester=learning_unit_data.pm_vol_q1,
            second_quadrimester=learning_unit_data.pm_vol_q2,
            classes_count=learning_unit_data.pm_classes,
        ),
        practical_volume=PracticalVolume(
            total_annual=learning_unit_data.pp_vol_tot,
            first_quadrimester=learning_unit_data.pp_vol_q1,
            second_quadrimester=learning_unit_data.pp_vol_q2,
            classes_count=learning_unit_data.pp_classes,
        ),
        achievements=achievements,
        entities=Entities(requirement_entity_acronym=learning_unit_data.requirement_entity_acronym,
                          allocation_entity_acronym=learning_unit_data.allocation_entity_acronym),
        description_fiche=description_fiche,
        force_majeure=force_majeure,
        specifications=specifications,
        teaching_materials=teaching_materials,
        subtype=learning_unit_data.subtype,
        session=learning_unit_data.session,
        main_language=learning_unit_data.main_language,
        attributions=attributions,
    )


def __convert_string_to_enum(learn_unit_data: LearningUnitYearModel) -> LearningUnitYearModel:
    subtype_str = learn_unit_data.type
    learn_unit_data.type = LearningContainerYearType[subtype_str]
    if learn_unit_data.quadrimester:
        learn_unit_data.quadrimester = DerogationQuadrimester[learn_unit_data.quadrimester]
    learn_unit_data.subtype = dict(LEARNING_UNIT_YEAR_SUBTYPES)[learn_unit_data.subtype]
    return learn_unit_data


def __get_queryset() -> QuerySet:
    qs = LearningUnitYearModel.objects.all().prefetch_related(
        Prefetch(
            'learningachievement_set',
            LearningAchievementModelDb.objects.all().annotate(
                language_code=F('language__code'),
            ).order_by(
                'order',
                'language_code',
            )
        )
    )
    subquery_component = LearningComponentYear.objects.filter(
        learning_unit_year_id=OuterRef('pk')
    )
    subquery_component_pm = subquery_component.filter(
        type=LECTURING
    )
    subquery_component_pp = subquery_component.filter(
        type=PRACTICAL_EXERCISES
    )
    subquery_entity_requirement = EntityVersion.objects.filter(
        entity=OuterRef('learning_container_year__requirement_entity'),
    ).current(
        OuterRef('academic_year__start_date')
    ).values('acronym')[:1]

    subquery_allocation_requirement = EntityVersion.objects.filter(
        entity=OuterRef('learning_container_year__allocation_entity'),
    ).current(
        OuterRef('academic_year__start_date')
    ).values('acronym')[:1]

    qs = qs.annotate(
        specific_title_en=F('specific_title_english'),
        specific_title_fr=F('specific_title'),
        common_title_fr=F('learning_container_year__common_title'),
        common_title_en=F('learning_container_year__common_title_english'),
        year=F('academic_year__year'),
        proposal_type=F('proposallearningunit__type'),
        proposal_state=F('proposallearningunit__state'),
        start_year=F('learning_unit__start_year'),
        end_year=F('learning_unit__end_year'),
        type=F('learning_container_year__container_type'),
        other_remark=F('learning_unit__other_remark'),
        main_language=F('language__name'),

        # components (volumes) data
        pm_vol_tot=Subquery(subquery_component_pm.values('hourly_volume_total_annual')),
        pp_vol_tot=Subquery(subquery_component_pp.values('hourly_volume_total_annual')),
        pm_vol_q1=Subquery(subquery_component_pm.values('hourly_volume_partial_q1')),
        pp_vol_q1=Subquery(subquery_component_pp.values('hourly_volume_partial_q1')),
        pm_vol_q2=Subquery(subquery_component_pm.values('hourly_volume_partial_q2')),
        pp_vol_q2=Subquery(subquery_component_pp.values('hourly_volume_partial_q2')),
        pm_classes=Subquery(subquery_component_pm.values('planned_classes')),
        pp_classes=Subquery(subquery_component_pp.values('planned_classes')),

        requirement_entity_acronym=Subquery(subquery_entity_requirement),
        allocation_entity_acronym=Subquery(subquery_allocation_requirement),
    )

    return qs
