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
from django.db.models import F, Subquery, OuterRef, QuerySet, Q

from attribution.ddd.repositories.attribution_repository import AttributionRepository
from base.business.learning_unit import CMS_LABEL_PEDAGOGY, CMS_LABEL_PEDAGOGY_FR_AND_EN, CMS_LABEL_SPECIFICATIONS
from base.models.entity_version import EntityVersion
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.learning_unit_year_subtypes import LEARNING_UNIT_YEAR_SUBTYPES
from base.models.enums.quadrimesters import DerogationQuadrimester
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear as LearningUnitYearModel
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from learning_unit.ddd.domain.description_fiche import DescriptionFiche
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear, LecturingVolume, PracticalVolume, Entities
from learning_unit.ddd.domain.learning_unit_year_identity import LearningUnitYearIdentity
from learning_unit.ddd.domain.proposal import Proposal
from learning_unit.ddd.domain.specifications import Specifications
from learning_unit.ddd.repository.load_teaching_material import bulk_load_teaching_materials
from osis_common.decorators.deprecated import deprecated


def __instanciate_volume_domain_object(learn_unit_data: dict) -> dict:
    learn_unit_data['lecturing_volume'] = LecturingVolume(total_annual=learn_unit_data.pop('pm_vol_tot'),
                                                          first_quadrimester=learn_unit_data.pop('pm_vol_q1'),
                                                          second_quadrimester=learn_unit_data.pop('pm_vol_q2'),
                                                          classes_count=learn_unit_data.pop('pm_classes'),
                                                          )
    learn_unit_data['practical_volume'] = PracticalVolume(total_annual=learn_unit_data.pop('pp_vol_tot'),
                                                          first_quadrimester=learn_unit_data.pop('pp_vol_q1'),
                                                          second_quadrimester=learn_unit_data.pop('pp_vol_q2'),
                                                          classes_count=learn_unit_data.pop('pp_classes'),
                                                          )
    return learn_unit_data


@deprecated  # Use :py:meth:`~learning_unit.ddd.repository.load_learning_unit_year.load_multiple_by_identity` instead !
def load_multiple(learning_unit_year_ids: List[int]) -> List['LearningUnitYear']:
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

    qs = LearningUnitYearModel.objects.filter(pk__in=learning_unit_year_ids).annotate(
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

    ).values(
        'id',
        'year',
        'acronym',
        'type',
        'specific_title_fr',
        'specific_title_en',
        'common_title_fr',
        'common_title_en',
        'start_year',
        'end_year',
        'proposal_type',
        'proposal_state',
        'credits',
        'status',
        'periodicity',
        'other_remark',
        'quadrimester',

        'pm_vol_tot',
        'pp_vol_tot',
        'pm_vol_q1',
        'pp_vol_q1',
        'pm_vol_q2',
        'pp_vol_q2',
        'pm_classes',
        'pp_classes',

        'requirement_entity_acronym',
        'allocation_entity_acronym',
        'subtype',
        'session',
        'main_language'
    )

    qs = _annotate_with_description_fiche_specifications(qs)

    results = []

    for learning_unit_data in qs:
        luy = LearningUnitYear(
            **__instanciate_volume_domain_object(__convert_string_to_enum(learning_unit_data)),
            proposal=Proposal(learning_unit_data.pop('proposal_type'),
                              learning_unit_data.pop('proposal_state')),
            entities=Entities(requirement_entity_acronym=learning_unit_data.pop('requirement_entity_acronym'),
                              allocation_entity_acronym=learning_unit_data.pop('allocation_entity_acronym')),
            description_fiche=DescriptionFiche(
                    resume=learning_unit_data.pop('cms_resume'),
                    resume_en=learning_unit_data.pop('cms_resume_en'),
                    teaching_methods=learning_unit_data.pop('cms_teaching_methods'),
                    teaching_methods_en=learning_unit_data.pop('cms_teaching_methods_en'),
                    evaluation_methods=learning_unit_data.pop('cms_evaluation_methods'),
                    evaluation_methods_en=learning_unit_data.pop('cms_evaluation_methods_en'),
                    other_informations=learning_unit_data.pop('cms_other_informations'),
                    other_informations_en=learning_unit_data.pop('cms_other_informations_en'),
                    online_resources=learning_unit_data.pop('cms_online_resources'),
                    online_resources_en=learning_unit_data.pop('cms_online_resources_en'),
                    bibliography=learning_unit_data.pop('cms_bibliography'),
                    mobility=learning_unit_data.pop('cms_mobility')
                ),
            specifications=Specifications(
                themes_discussed=learning_unit_data.pop('cms_themes_discussed'),
                themes_discussed_en=learning_unit_data.pop('cms_themes_discussed_en'),
                prerequisite=learning_unit_data.pop('cms_prerequisite'),
                prerequisite_en=learning_unit_data.pop('cms_prerequisite_en')
                ),
            teaching_materials=[]
            )
        results.append(luy)
    return results


def __convert_string_to_enum(learn_unit_data: dict) -> dict:
    subtype_str = learn_unit_data['type']
    learn_unit_data['type'] = LearningContainerYearType[subtype_str]
    if learn_unit_data.get('quadrimester'):
        learn_unit_data['quadrimester'] = DerogationQuadrimester[learn_unit_data['quadrimester']]
    learn_unit_data['subtype'] = dict(LEARNING_UNIT_YEAR_SUBTYPES)[learn_unit_data['subtype']]
    return learn_unit_data


def _annotate_with_description_fiche_specifications(original_qs1):
    original_qs = original_qs1
    qs = TranslatedText.objects.filter(
        reference=OuterRef('pk'),
        entity=LEARNING_UNIT_YEAR)

    annotations = build_annotations(
        qs,
        CMS_LABEL_PEDAGOGY+CMS_LABEL_SPECIFICATIONS,
        CMS_LABEL_PEDAGOGY_FR_AND_EN+CMS_LABEL_SPECIFICATIONS
    )
    original_qs = original_qs.annotate(**annotations)

    return original_qs


def build_annotations(qs: QuerySet, fr_labels: list, en_labels: list):
    annotations = {
        "cms_{}".format(lbl): Subquery(
            _build_subquery_text_label(qs, lbl, settings.LANGUAGE_CODE_FR))
        for lbl in fr_labels
    }

    annotations.update({
        "cms_{}_en".format(lbl): Subquery(
            _build_subquery_text_label(qs, lbl, settings.LANGUAGE_CODE_EN))
        for lbl in en_labels}
    )
    return annotations


def _build_subquery_text_label(qs, cms_text_label, lang):

    return qs.filter(text_label__label="{}".format(cms_text_label), language=lang).values(
        'text')[:1]


def load_multiple_by_identity(learning_unit_year_identities: List['LearningUnitYearIdentity']) \
        -> List['LearningUnitYear']:
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

    filter_by_identity = _build_where_clause(learning_unit_year_identities[0])

    for identity in learning_unit_year_identities[1:]:
        filter_by_identity |= _build_where_clause(identity)

    qs = LearningUnitYearModel.objects.all()
    qs = qs.filter(filter_by_identity)

    attributions = AttributionRepository.search(learning_unit_year_ids=learning_unit_year_identities)
    attributions_by_ue = __build_sorted_attributions_grouped_by_ue(attributions)

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

    ).values(
        'id',
        'year',
        'acronym',
        'type',
        'specific_title_fr',
        'specific_title_en',
        'common_title_fr',
        'common_title_en',
        'start_year',
        'end_year',
        'proposal_type',
        'proposal_state',
        'credits',
        'status',
        'periodicity',
        'other_remark',
        'quadrimester',

        'pm_vol_tot',
        'pp_vol_tot',
        'pm_vol_q1',
        'pp_vol_q1',
        'pm_vol_q2',
        'pp_vol_q2',
        'pm_classes',
        'pp_classes',

        'requirement_entity_acronym',
        'allocation_entity_acronym',
        'subtype',
        'session',
        'main_language',
    )

    qs = _annotate_with_description_fiche_specifications(qs)
    teaching_materials_by_learning_unit_identity = bulk_load_teaching_materials(learning_unit_year_identities)
    results = []
    for learning_unit_data in qs:
        learning_unit_identity = LearningUnitYearIdentity(code=learning_unit_data['acronym'],
                                                          year=learning_unit_data['year'])
        attributions = attributions_by_ue.get(learning_unit_identity)
        luy = LearningUnitYear(
            entity_id=learning_unit_identity,
            **__instanciate_volume_domain_object(__convert_string_to_enum(learning_unit_data)),
            proposal=Proposal(learning_unit_data.pop('proposal_type'),
                              learning_unit_data.pop('proposal_state')),
            entities=Entities(requirement_entity_acronym=learning_unit_data.pop('requirement_entity_acronym'),
                              allocation_entity_acronym=learning_unit_data.pop('allocation_entity_acronym')),
            description_fiche=DescriptionFiche(
                    resume=learning_unit_data.pop('cms_resume'),
                    resume_en=learning_unit_data.pop('cms_resume_en'),
                    teaching_methods=learning_unit_data.pop('cms_teaching_methods'),
                    teaching_methods_en=learning_unit_data.pop('cms_teaching_methods_en'),
                    evaluation_methods=learning_unit_data.pop('cms_evaluation_methods'),
                    evaluation_methods_en=learning_unit_data.pop('cms_evaluation_methods_en'),
                    other_informations=learning_unit_data.pop('cms_other_informations'),
                    other_informations_en=learning_unit_data.pop('cms_other_informations_en'),
                    online_resources=learning_unit_data.pop('cms_online_resources'),
                    online_resources_en=learning_unit_data.pop('cms_online_resources_en'),
                    bibliography=learning_unit_data.pop('cms_bibliography'),
                    mobility=learning_unit_data.pop('cms_mobility')
            ),
            specifications=Specifications(
                themes_discussed=learning_unit_data.pop('cms_themes_discussed'),
                themes_discussed_en=learning_unit_data.pop('cms_themes_discussed_en'),
                prerequisite=learning_unit_data.pop('cms_prerequisite'),
                prerequisite_en=learning_unit_data.pop('cms_prerequisite_en')
                ),
            teaching_materials=teaching_materials_by_learning_unit_identity.get(learning_unit_identity, []),
            attributions=attributions
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
