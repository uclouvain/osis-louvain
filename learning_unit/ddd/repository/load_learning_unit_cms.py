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
import functools
import itertools
import operator
from collections import defaultdict
from typing import TypeVar, List, Generic, Iterable, Dict

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Prefetch
from reversion.models import Version

from base.models.learning_unit_year import LearningUnitYear
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from learning_unit.ddd.business_types import *
from learning_unit.ddd.domain.description_fiche import DescriptionFiche, DescriptionFicheForceMajeure
from learning_unit.ddd.domain.specifications import Specifications

LearningUnitCMS = TypeVar('LearningUnitCMS', DescriptionFiche, DescriptionFicheForceMajeure, Specifications)


def bulk_load_cms(
        learning_unit_identities: Iterable['LearningUnitYearIdentity'],
        filter_clause,
        domain_class: Generic[LearningUnitCMS],
        with_revisions: bool

) -> Dict[int, 'LearningUnitCMS']:
    if not learning_unit_identities:
        return defaultdict(domain_class)

    identity_clauses = [_build_identity_clause(identity) for identity in learning_unit_identities]
    identity_filter_clause = functools.reduce(operator.or_, identity_clauses)
    filtered_reference = LearningUnitYear.objects.filter(identity_filter_clause).values("id")

    model_content_type = ContentType.objects.get_for_model(TranslatedText)
    qs = TranslatedText.objects.filter(
        entity=LEARNING_UNIT_YEAR
    ).filter(
        filter_clause, reference__in=filtered_reference
    ).select_related(
        "text_label"
    ).order_by(
        "reference"
    ).only(
        "reference",
        "language",
        "text",
        "text_label__label"
    )
    if with_revisions:
        qs = qs.prefetch_related(
            Prefetch(
                "versions",
                queryset=Version.objects.filter(
                    content_type=model_content_type
                ).order_by(
                    "-revision__date_created"
                ).select_related(
                    "revision__user__person",
                    "revision"
                ).only(
                    "object_id",
                    "content_type",
                    "revision__date_created",
                    "revision__user__person__first_name",
                    "revision__user__person__last_name"
                ),
                to_attr="old_versions"
            )
        )

    return defaultdict(domain_class, {
        int(reference): _translated_texts_to_domain(list(translated_texts), domain_class)
        for reference, translated_texts in itertools.groupby(qs, key=lambda el: el.reference)
    })


def _translated_texts_to_domain(
        translated_texts: List[TranslatedText], domain_class: Generic[LearningUnitCMS]
) -> LearningUnitCMS:
    versions = itertools.chain.from_iterable((getattr(tt, "old_versions", []) for tt in translated_texts))
    versions_by_date = sorted(versions, key=lambda v: v.revision.date_created, reverse=True)
    latest_version = versions_by_date[0] if versions_by_date else None

    fields = {_convert_translated_text_to_field_name(tt): tt.text for tt in translated_texts}

    if latest_version:
        fields.update({
            'last_update': latest_version.revision.date_created,
            'author': latest_version.revision.user.person.full_name
        })

    return domain_class(**fields)


def _convert_translated_text_to_field_name(translate_text: TranslatedText) -> str:
    if translate_text.language == "fr-be":
        return translate_text.text_label.label.split("_force_majeure")[0]
    return "{}_{}".format(
        translate_text.text_label.label.split("_force_majeure")[0],
        translate_text.language.split("-")[0]
    )


def _build_identity_clause(learning_unit_identity: 'LearningUnitYearIdentity') -> Q:
    return Q(acronym=learning_unit_identity.code, academic_year__year=learning_unit_identity.year)
