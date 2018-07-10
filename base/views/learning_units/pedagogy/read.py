##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404

from base import models as mdl
from base.business.learning_unit import get_no_summary_responsible_teachers, CMS_LABEL_PEDAGOGY_FR_ONLY, \
    get_cms_label_data, CMS_LABEL_PEDAGOGY
from base.business.learning_units import perms
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm
from base.models import teaching_material
from base.models.person import Person
from base.models.tutor import find_all_summary_responsibles_by_learning_unit_year
from base.views import layout
from base.views.learning_units.common import get_common_context_learning_unit_year


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = {
        'experimental_phase': True,
        'create_teaching_material_urlname': 'teaching_material_create',
        'update_teaching_material_urlname': 'teaching_material_edit',
        'delete_teaching_material_urlname': 'teaching_material_delete',
        'update_mobility_modality_urlname': 'mobility_modality_update'
    }
    template = "learning_unit/pedagogy.html"
    return read_learning_unit_pedagogy(request, learning_unit_year_id, context, template)


# @TODO: Supprimer form_french/form_english et utiliser une liste pour l'affichage à la place des formulaires
def read_learning_unit_pedagogy(request, learning_unit_year_id, context, template):
    person = get_object_or_404(Person, user=request.user)
    context.update(get_common_context_learning_unit_year(learning_unit_year_id, person))
    learning_unit_year = context['learning_unit_year']
    perm_to_edit = is_eligible_to_update_learning_unit_pedagogy(learning_unit_year, person)
    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_PEDAGOGY, user_language)
    context['form_french'] = LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                      language_code=settings.LANGUAGE_CODE_FR)
    context['form_english'] = LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                       language_code=settings.LANGUAGE_CODE_EN)
    context['teaching_materials'] = teaching_material.find_by_learning_unit_year(learning_unit_year)
    context['can_edit_information'] = perm_to_edit
    context['can_edit_summary_locked_field'] = perms.can_edit_summary_locked_field(learning_unit_year, person)
    context['summary_responsibles'] = find_all_summary_responsibles_by_learning_unit_year(learning_unit_year)
    context['other_teachers'] = get_no_summary_responsible_teachers(learning_unit_year, context['summary_responsibles'])
    context['cms_label_pedagogy_fr_only'] = CMS_LABEL_PEDAGOGY_FR_ONLY
    return layout.render(request, template, context)
