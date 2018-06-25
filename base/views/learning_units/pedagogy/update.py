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
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from base import models as mdl
from base.business.learning_unit import CMS_LABEL_PEDAGOGY, get_cms_label_data, find_language_in_settings, \
    get_no_summary_responsible_teachers
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy
from base.forms.learning_unit_pedagogy import SummaryModelForm, LearningUnitPedagogyForm, \
    BibliographyModelForm, LearningUnitPedagogyEditForm
from base.models.bibliography import Bibliography
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.tutor import find_all_summary_responsibles_by_learning_unit_year
from base.views import layout
from base.views.common import display_error_messages, display_success_messages
from base.views.learning_units.common import get_common_context_learning_unit_year, get_text_label_translated
from base.views.learning_units.perms import PermissionDecorator
from cms.models import text_label


def update_learning_unit_pedagogy(request, learning_unit_year_id, context, template):
    person = get_object_or_404(Person, user=request.user)
    context.update(get_common_context_learning_unit_year(learning_unit_year_id, person))
    learning_unit_year = context['learning_unit_year']
    perm_to_edit = int(is_eligible_to_update_learning_unit_pedagogy(learning_unit_year, person))

    post = request.POST or None
    summary_form = SummaryModelForm(post, person, context['is_person_linked_to_entity'], instance=learning_unit_year)
    BibliographyFormset = inlineformset_factory(LearningUnitYear, Bibliography, fields=('title', 'mandatory'),
                                                max_num=10, extra=perm_to_edit, form=BibliographyModelForm,
                                                can_delete=perm_to_edit)
    bibliography_formset = BibliographyFormset(post, instance=learning_unit_year, form_kwargs={'person': person})

    if perm_to_edit and summary_form.is_valid() and bibliography_formset.is_valid():
        try:
            summary_form.save()
            bibliography_formset.save()

            display_success_messages(request, _("success_modification_learning_unit"))
            # Redirection on the same page
            return HttpResponseRedirect(request.path_info)

        except ValueError as e:
            display_error_messages(request, e.args[0])

    context.update(get_cms_pedagogy_form(request, learning_unit_year))
    context['summary_editable_form'] = summary_form
    context['bibliography_formset'] = bibliography_formset
    context['can_edit_information'] = perm_to_edit

    context['summary_responsibles'] = find_all_summary_responsibles_by_learning_unit_year(learning_unit_year)
    context['other_teachers'] = get_no_summary_responsible_teachers(learning_unit_year, context['summary_responsibles'])
    return layout.render(request, template, context)


# TODO Method similar with all cms forms
def get_cms_pedagogy_form(request, learning_unit_year):
    user_language = mdl.person.get_user_interface_language(request.user)
    return {
        'cms_labels_translated': get_cms_label_data(CMS_LABEL_PEDAGOGY, user_language),
        'form_french': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                language_code=settings.LANGUAGE_CODE_FR),
        'form_english': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                 language_code=settings.LANGUAGE_CODE_EN)
        }


@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
@require_http_methods(["GET", "POST"])
def learning_unit_pedagogy_edit(request, learning_unit_year_id):
    redirect_url = reverse("learning_unit_pedagogy", kwargs={'learning_unit_year_id': learning_unit_year_id})
    return edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url)


def edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url):
    if request.method == 'POST':
        form = LearningUnitPedagogyEditForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect(redirect_url)
    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    label_name = request.GET.get('label')
    language = request.GET.get('language')
    text_lb = text_label.find_by_name(label_name)
    form = LearningUnitPedagogyEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form
    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = get_text_label_translated(text_lb, user_language)
    context['language_translated'] = find_language_in_settings(language)
    return layout.render(request, "learning_unit/pedagogy_edit.html", context)
