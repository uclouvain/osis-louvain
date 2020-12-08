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
from typing import Iterable, Dict

from django.db.models import Q

from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FORCE_MAJEURE
from base.models.learning_unit_year import LearningUnitYear
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from learning_unit.ddd.domain.description_fiche import DescriptionFicheForceMajeure
from learning_unit.ddd.repository.load_learning_unit_cms import _annotate_with_last_update_informations, \
    _translated_texts_to_domain, _build_identity_clause


def bulk_load_force_majeures(
        learning_unit_identities: Iterable['LearningUnitYearIdentity']
) -> Dict[int, 'DescriptionFicheForceMajeure']:
    if not learning_unit_identities:
        return defaultdict(DescriptionFicheForceMajeure)

    identity_clauses = [_build_identity_clause(identity) for identity in learning_unit_identities]
    identity_filter_clause = functools.reduce(operator.or_, identity_clauses)
    filtered_reference = LearningUnitYear.objects.filter(identity_filter_clause).values("id")

    qs = TranslatedText.objects.filter(
        entity=LEARNING_UNIT_YEAR
    ).filter(
        Q(text_label__label__in=CMS_LABEL_PEDAGOGY_FORCE_MAJEURE, language__in=['fr-be', 'en']),
        reference__in=filtered_reference
    ).select_related(
        "text_label"
    ).order_by(
        "reference"
    )
    qs = _annotate_with_last_update_informations(qs).values_list(
        "last_date_created", "last_author_last_name", "last_author_first_name", "text", "text_label__label", "language",
        "reference", named=True
    )
    return defaultdict(DescriptionFicheForceMajeure, {
        int(reference): _translated_texts_to_domain(list(translated_texts), DescriptionFicheForceMajeure)
        for reference, translated_texts in itertools.groupby(qs, key=lambda el: el.reference)
    })
