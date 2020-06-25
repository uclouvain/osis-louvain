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
import json

from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base.forms.education_group_admission import UpdateLineForm, UpdateTextForm
from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.admission_condition import AdmissionConditionLine, AdmissionCondition
from base.models.education_group_year import EducationGroupYear
from base.models.person import get_user_interface_language
from base.utils.cache import cache
from base.utils.cache_keys import get_tab_lang_keys, CACHE_TIMEOUT
from base.views.education_groups.perms import can_change_admission_condition, can_change_general_information
from cms.enums import entity_name
from cms.models import translated_text_label
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from education_group.ddd.domain.service.identity_search import TrainingIdentitySearch
from education_group.views.proxy.read import Tab
from osis_common.decorators.ajax import ajax_required


def education_group_year_pedagogy_edit_post(request, education_group_year_id, root_id):
    form = EducationGroupPedagogyEditForm(request.POST)
    training_identity = TrainingIdentitySearch().get_from_education_group_year_id(education_group_year_id)
    redirect_url = _get_admission_condition_success_url(training_identity.year, training_identity.acronym)
    if form.is_valid():
        label = form.cleaned_data['label']

        text_label = TextLabel.objects.filter(label=label).first()

        record, created = TranslatedText.objects.get_or_create(
            content_object=EducationGroupYear.objects.get(id=education_group_year_id),
            entity='offer_year',
            text_label=text_label,
            language='fr-be'
        )
        record.text = form.cleaned_data['text_french']
        record.save()

        record, created = TranslatedText.objects.get_or_create(
            content_object=EducationGroupYear.objects.get(id=education_group_year_id),
            entity='offer_year',
            text_label=text_label,
            language='en'
        )
        record.text = form.cleaned_data['text_english']
        record.save()

        redirect_url += "#section_{label_name}".format(label_name=label)
    return redirect(redirect_url)


def education_group_year_pedagogy_edit_get(request, education_group_year_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
    context = {
        'education_group_year': education_group_year,
    }
    label_name = request.GET.get('label')
    context['label'] = label_name
    initial_values = {'label': label_name}
    fr_text = TranslatedText.objects.filter(
        content_object=EducationGroupYear.objects.get(id=education_group_year_id),
        text_label__label=label_name,
        entity=entity_name.OFFER_YEAR,
        language='fr-be'
    ).first()
    if fr_text:
        initial_values['text_french'] = fr_text.text
    en_text = TranslatedText.objects.filter(
        reference_content_objectobject=EducationGroupYear.objects.get(id=education_group_year_id),
        text_label__label=label_name,
        entity=entity_name.OFFER_YEAR,
        language='en'
    ).first()
    if en_text:
        initial_values['text_english'] = en_text.text
    form = EducationGroupPedagogyEditForm(initial=initial_values)
    context['form'] = form
    context['group_to_parent'] = request.GET.get("group_to_parent") or '0'
    context['translated_label'] = translated_text_label.get_label_translation(
        text_entity=entity_name.OFFER_YEAR,
        label=label_name,
        language=get_user_interface_language(request.user)
    )
    return render(request, 'education_group/blocks/modal/modal_pedagogy_edit_inner.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
@can_change_general_information
def education_group_year_pedagogy_edit(request, offer_id, education_group_year_id):
    if request.method == 'POST':
        return education_group_year_pedagogy_edit_post(request, education_group_year_id, offer_id)
    return education_group_year_pedagogy_edit_get(request, education_group_year_id)


@login_required
@can_change_admission_condition
def education_group_year_admission_condition_remove_line(request, offer_id, education_group_year_id):
    admission_condition_line_id = request.GET['id']
    admission_condition = get_object_or_404(
        AdmissionCondition.objects.annotate(
            acronym=F('education_group_year__acronym'),
            year=F('education_group_year__academic_year__year')
        ),
        education_group_year__pk=education_group_year_id
    )
    admission_condition_line = get_object_or_404(AdmissionConditionLine,
                                                 admission_condition=admission_condition,
                                                 pk=admission_condition_line_id)
    admission_condition_line.delete()
    return redirect(_get_admission_condition_success_url(admission_condition.year, admission_condition.acronym))


def _get_admission_condition_success_url(year: int, acronym: str):
    return reverse('education_group_read_proxy', args=[year, acronym]) + '?tab={}'.format(Tab.ADMISSION_CONDITION)


def get_content_of_admission_condition_line(message, admission_condition_line, lang):
    return {
        'message': message,
        'section': admission_condition_line.section,
        'id': admission_condition_line.id,
        'diploma': getattr(admission_condition_line, 'diploma' + lang, ''),
        'conditions': getattr(admission_condition_line, 'conditions' + lang, ''),
        'access': admission_condition_line.access,
        'remarks': getattr(admission_condition_line, 'remarks' + lang, ''),
    }


def education_group_year_admission_condition_update_line_post(request, root_id, education_group_year_id):
    creation_mode = request.POST.get('admission_condition_line') == ''
    if creation_mode:
        # bypass the validation of the form
        request.POST = request.POST.copy()
        request.POST.update({'admission_condition_line': 0})

    form = UpdateLineForm(request.POST)
    if form.is_valid():
        save_form_to_admission_condition_line(education_group_year_id, creation_mode, form)

    training_identity = TrainingIdentitySearch().get_from_education_group_year_id(education_group_year_id)
    return redirect(_get_admission_condition_success_url(training_identity.year, training_identity.acronym))


def save_form_to_admission_condition_line(education_group_year_id, creation_mode, form):
    admission_condition_line_id = form.cleaned_data['admission_condition_line']
    language = form.cleaned_data['language']
    lang = '' if language == 'fr-be' else '_en'
    if not creation_mode:
        admission_condition_line = get_object_or_404(AdmissionConditionLine,
                                                     pk=admission_condition_line_id)
    else:
        section = form.cleaned_data['section']
        education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
        admission_condition_line = AdmissionConditionLine.objects.create(
            admission_condition=education_group_year.admissioncondition,
            section=section)

    admission_condition_line.access = form.cleaned_data['access']

    for key in ('diploma', 'conditions', 'remarks'):
        setattr(admission_condition_line, key + lang, form.cleaned_data[key])

    admission_condition_line.save()


def education_group_year_admission_condition_update_line_get(request):
    section = request.GET['section']
    language = request.GET['language']

    lang = '' if language == 'fr-be' else '_en'

    initial_values = {
        'language': language,
        'section': section,
    }

    admission_condition_line_id = request.GET.get('id')

    if admission_condition_line_id:
        admission_condition_line = get_object_or_404(AdmissionConditionLine,
                                                     pk=admission_condition_line_id,
                                                     section=section)

        initial_values['admission_condition_line'] = admission_condition_line.id

        response = get_content_of_admission_condition_line('read', admission_condition_line, lang)
        initial_values.update(response)

    form = UpdateLineForm(initial=initial_values)

    context = {
        'form': form
    }
    return render(request, 'education_group/condition_line_edit.html', context)


@login_required
@can_change_admission_condition
def education_group_year_admission_condition_update_line(request, offer_id, education_group_year_id):
    if request.method == 'POST':
        return education_group_year_admission_condition_update_line_post(request, offer_id, education_group_year_id)
    return education_group_year_admission_condition_update_line_get(request)


def education_group_year_admission_condition_update_text_post(request, root_id, education_group_year_id):
    form = UpdateTextForm(request.POST)

    if form.is_valid():
        education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
        section = form.cleaned_data['section']

        admission_condition = education_group_year.admissioncondition

        setattr(admission_condition, 'text_' + section, form.cleaned_data['text_fr'])
        setattr(admission_condition, 'text_' + section + '_en', form.cleaned_data['text_en'])
        admission_condition.save()

    training_identity = TrainingIdentitySearch().get_from_education_group_year_id(education_group_year_id)
    return redirect(_get_admission_condition_success_url(training_identity.year, training_identity.acronym))


def education_group_year_admission_condition_update_text_get(request, education_group_year_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
    section = request.GET['section']
    title = request.GET['title']

    form = UpdateTextForm(initial={
        'section': section,
        'text_fr': getattr(education_group_year.admissioncondition, 'text_' + section),
        'text_en': getattr(education_group_year.admissioncondition, 'text_' + section + '_en'),
    })

    context = {
        'form': form,
        'title': title,
    }
    return render(request, 'education_group/condition_text_edit.html', context)


@login_required
@can_change_admission_condition
def education_group_year_admission_condition_update_text(request, offer_id, education_group_year_id):
    if request.method == 'POST':
        return education_group_year_admission_condition_update_text_post(request, offer_id, education_group_year_id)
    return education_group_year_admission_condition_update_text_get(request, education_group_year_id)


@login_required
@ajax_required
@can_change_admission_condition
def education_group_year_admission_condition_line_order(request, offer_id, education_group_year_id):
    info = json.loads(request.body.decode('utf-8'))

    admission_condition_line = get_object_or_404(
        AdmissionConditionLine.objects.annotate(
            acronym=F('admission_condition__education_group_year__acronym'),
            year=F('admission_condition__education_group_year__academic_year__year')
        ),
        pk=info['record']
    )

    if info['action'] == 'up':
        admission_condition_line.up()
    elif info['action'] == 'down':
        admission_condition_line.down()

    success_url = _get_admission_condition_success_url(admission_condition_line.year, admission_condition_line.acronym)
    return JsonResponse({
        'success_url': success_url
    })


@login_required
def education_group_year_admission_condition_tab_lang_edit(request, offer_id, education_group_year_id, language):
    cache.set(get_tab_lang_keys(request.user), language, timeout=CACHE_TIMEOUT)
    training_identity = TrainingIdentitySearch().get_from_education_group_year_id(education_group_year_id)
    return redirect(_get_admission_condition_success_url(training_identity.year, training_identity.acronym))
