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
from typing import TypeVar, List, Generic

from django.contrib.contenttypes.models import ContentType
from django.db.models import IntegerField, OuterRef, Subquery, Q
from django.db.models.functions import Cast
from reversion.models import Version

from cms.models.translated_text import TranslatedText
from learning_unit.ddd.domain.description_fiche import DescriptionFiche, DescriptionFicheForceMajeure
from learning_unit.ddd.domain.specifications import Specifications

LearningUnitCMS = TypeVar('LearningUnitCMS', DescriptionFiche, DescriptionFicheForceMajeure, Specifications)


def _annotate_with_last_update_informations(qs: 'QuerySet') -> 'QuerySet':
    model_content_type = ContentType.objects.get_for_model(qs.model)
    last_version_subquery = Version.objects.annotate(
        object_id_int=Cast("object_id", IntegerField())
    ).filter(
        content_type=model_content_type, object_id_int=OuterRef("id")
    ).order_by(
        "-revision__date_created"
    )
    return qs.annotate(
        last_date_created=Subquery(last_version_subquery.values("revision__date_created")[:1]),
        last_author_last_name=Subquery(last_version_subquery.values("revision__user__person__last_name")[:1]),
        last_author_first_name=Subquery(last_version_subquery.values("revision__user__person__first_name")[:1])
    )


def _translated_texts_to_domain(
        translated_texts: List[TranslatedText], domain_class: Generic[LearningUnitCMS]
) -> LearningUnitCMS:
    texts_with_date = (tt for tt in translated_texts
                       if hasattr(tt, "last_date_created") and tt.last_date_created is not None)
    texts_with_date = sorted(texts_with_date)

    fields = {_convert_translated_text_to_field_name(tt): tt.text for tt in translated_texts}
    if domain_class != Specifications and texts_with_date:

        fields.update({
            'last_update': texts_with_date[-1].last_date_created,
            'author': texts_with_date[-1].last_author_last_name + " " + texts_with_date[-1].last_author_first_name
        })
    return domain_class(**fields)


def _convert_translated_text_to_field_name(translate_text: TranslatedText) -> str:
    if translate_text.language == "fr-be":
        return translate_text.text_label__label.split("_force_majeure")[0]
    return "{}_{}".format(
        translate_text.text_label__label.split("_force_majeure")[0],
        translate_text.language.split("-")[0]
    )


def _build_identity_clause(learning_unit_identity: 'LearningUnitYearIdentity') -> Q:
    return Q(acronym=learning_unit_identity.code, academic_year__year=learning_unit_identity.year)
