##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import itertools

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, Case, When, Value, IntegerField, Q
from django.shortcuts import get_object_or_404, render
from reversion.models import Version

from attribution.models.attribution import Attribution
from base import models as mdl
from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY, \
    CMS_LABEL_PEDAGOGY
from base.business.learning_units import perms
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy
from base.models.person import Person
from base.models.teaching_material import TeachingMaterial
from base.views.common import add_to_session
from base.views.learning_units.common import get_common_context_learning_unit_year
from base.views.learning_units.detail import SEARCH_URL_PART
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    if SEARCH_URL_PART in request.META.get('HTTP_REFERER', ''):
        add_to_session(request, 'search_url', request.META.get('HTTP_REFERER'))
    return read_learning_unit_pedagogy(request, learning_unit_year_id, {}, "learning_unit/pedagogy.html")


def read_learning_unit_pedagogy(request, learning_unit_year_id, context, template):
    person = get_object_or_404(Person, user=request.user)
    context.update(get_common_context_learning_unit_year(learning_unit_year_id, person))

    learning_unit_year = context['learning_unit_year']
    perm_to_edit = is_eligible_to_update_learning_unit_pedagogy(learning_unit_year, person)
    user_language = mdl.person.get_user_interface_language(request.user)

    translated_labels_with_text = TranslatedTextLabel.objects.filter(
        language=user_language,
        text_label__label__in=CMS_LABEL_PEDAGOGY
    ).prefetch_related(
        Prefetch(
            "text_label__translatedtext_set",
            queryset=TranslatedText.objects.filter(
                language=settings.LANGUAGE_CODE_FR,
                entity=LEARNING_UNIT_YEAR,
                reference=learning_unit_year_id
            ),
            to_attr="text_fr"
        ),
        Prefetch(
            "text_label__translatedtext_set",
            queryset=TranslatedText.objects.filter(
                language=settings.LANGUAGE_CODE_EN,
                entity=LEARNING_UNIT_YEAR,
                reference=learning_unit_year_id
            ),
            to_attr="text_en"
        )
    ).annotate(
        label_ordering=Case(
            *[When(text_label__label=label, then=Value(i)) for i, label in enumerate(CMS_LABEL_PEDAGOGY)],
            default=Value(len(CMS_LABEL_PEDAGOGY)),
            output_field=IntegerField()
        )
    ).select_related(
        "text_label"
    ).order_by(
        "label_ordering"
    )
    teaching_materials = TeachingMaterial.objects.filter(learning_unit_year=learning_unit_year).order_by('order')
    attributions = Attribution.objects.filter(learning_unit_year=learning_unit_year).select_related(
        "tutor__person"
    ).order_by("tutor__person")

    translated_text_ids = itertools.chain.from_iterable(
        (*translated_label.text_label.text_fr, *translated_label.text_label.text_en)
        for translated_label in translated_labels_with_text
    )

    reversion = Version.objects.filter(
        Q(
            content_type=ContentType.objects.get_for_model(TranslatedText),
            object_id__in=map(lambda obj: obj.id, translated_text_ids)
        ) | Q(
            content_type=ContentType.objects.get_for_model(TeachingMaterial),
            object_id__in=map(lambda obj: obj.id, teaching_materials)
        )
    ).select_related(
        "revision",
        "revision__user"
    ).prefetch_related(
        Prefetch(
            "revision__user__person",
            to_attr="author"
        )

    ).order_by(
        "-revision__date_created"
    ).first()

    context['cms_labels_translated'] = translated_labels_with_text
    context['teaching_materials'] = teaching_materials
    context['can_edit_information'] = perm_to_edit
    context['can_edit_summary_locked_field'] = perms.can_edit_summary_locked_field(learning_unit_year, person)
    context['cms_label_pedagogy_fr_only'] = CMS_LABEL_PEDAGOGY_FR_ONLY
    context['attributions'] = attributions
    context["version"] = reversion
    return render(request, template, context)
