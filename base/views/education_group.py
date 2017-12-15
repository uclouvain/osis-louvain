##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl

from base.forms.education_groups import EducationGroupFilter, MAX_RECORDS
from base.forms.education_groups_administrative_data import CourseEnrollmentForm, AdministrativeDataFormset
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.program_manager import is_program_manager

from . import layout
from cms.enums import entity_name
from cms import models as mdl_cms
from collections import OrderedDict
from django.conf import settings
from base.forms.education_group_general_informations import EducationGroupGeneralInformationsForm
from base.models.enums import academic_calendar_type

CODE_SCS = 'code_scs'
TITLE = 'title'
CREDITS_MIN = "credits_min"
CREDITS_MAX = "credits_max"
BLOCK = "block"
SESSIONS_DEROGATION = "sessions_derogation"
NUMBER_SESSIONS = 3


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_groups(request):
    if request.GET:
        form = EducationGroupFilter(request.GET)
    else:
        current_academic_year = mdl.academic_year.current_academic_year()
        form = EducationGroupFilter(initial={'academic_year': current_academic_year,
                                             'category': education_group_categories.TRAINING})

    object_list = None
    if form.is_valid():
        object_list = form.get_object_list()
        if not _check_if_display_message(request, object_list):
            object_list = None

    context = {
        'form': form,
        'object_list': object_list,
        'experimental_phase': True
    }
    return layout.render(request, "education_groups.html", context)


def _check_if_display_message(request, an_education_groups):
    if not an_education_groups:
        messages.add_message(request, messages.WARNING, _('no_result'))
    elif len(an_education_groups) > MAX_RECORDS:
        messages.add_message(request, messages.WARNING, _('too_many_results'))
        return False
    return True


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_read(request, education_group_year_id):
    root = request.GET.get('root')
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)
    education_group_languages = [education_group_language.language.name for education_group_language in
                                 mdl.education_group_language.find_by_education_group_year(education_group_year)]
    enums = mdl.enums.education_group_categories
    if root:
        parent = mdl.education_group_year.find_by_id(root)
    else:
        parent = education_group_year
    return layout.render(request, "education_group/tab_identification.html", locals())


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_parent_read(request, education_group_year_id):
    root = request.GET.get('root')
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)
    education_group_languages = [education_group_language.language.name for education_group_language in
                                 mdl.education_group_language.find_by_education_group_year(education_group_year)]
    enums = mdl.enums.education_group_categories
    if root:
        parent = mdl.education_group_year.find_by_id(root)
    else:
        parent = education_group_year
    return layout.render(request, "education_group/tab_identification.html", locals())


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_diplomas(request, education_group_year_id):
    return _education_group_diplomas_tab(request, education_group_year_id)


def _education_group_diplomas_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)
    parent = get_root(education_group_year_id, request)
    return layout.render(request, "education_group/tab_diplomas.html", locals())


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_general_informations(request, education_group_year_id):
    return _education_group_general_informations_tab(request, education_group_year_id)


def _education_group_general_informations_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)

    CMS_LABEL = mdl_cms.translated_text.find_by_entity_reference(entity_name.OFFER_YEAR, education_group_year_id)

    fr_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'fr-be'), None)
    en_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'en'), None)

    parent = get_root(education_group_year_id, request)

    context = {'parent': parent,
               'education_group_year': education_group_year,
               'cms_labels_translated': _get_cms_label_data(CMS_LABEL,
                                                            mdl.person.get_user_interface_language(request.user)),
               'form_french': EducationGroupGeneralInformationsForm(education_group_year=education_group_year,
                                                                    language=fr_language, text_labels_name=CMS_LABEL),
               'form_english': EducationGroupGeneralInformationsForm(education_group_year=education_group_year,
                                                                     language=en_language, text_labels_name=CMS_LABEL)}
    return layout.render(request, "education_group/tab_general_informations.html", context)


def _get_cms_label_data(cms_label, user_language):
    cms_label_data = OrderedDict()
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.OFFER_YEAR,
                                                             labels=cms_label,
                                                             language=user_language)
    for label in cms_label:
        translated_text = next((trans.label for trans in translated_labels if trans.text_label.label == label), None)
        cms_label_data[label] = translated_text
    return cms_label_data


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_administrative_data(request, education_group_year_id):
    return _education_group_administrative_data_tab(request, education_group_year_id)


def _education_group_administrative_data_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)

    parent = get_root(education_group_year_id, request)

    context = {'parent': parent,
               'education_group_year': education_group_year,
               'course_enrollment':get_dates(academic_calendar_type.COURSE_ENROLLMENT, education_group_year),
               'mandataries': mdl.mandatary.find_by_education_group_year(education_group_year),
               'pgm_mgrs': mdl.program_manager.find_by_education_group(education_group_year.education_group)}
    context.update({'exam_enrollments': get_sessions_dates(academic_calendar_type.EXAM_ENROLLMENTS,
                                                           education_group_year)})
    context.update({'scores_exam_submission': get_sessions_dates(academic_calendar_type.SCORES_EXAM_SUBMISSION,
                                                                 education_group_year)})
    context.update({'dissertation_submission': get_sessions_dates(academic_calendar_type.DISSERTATION_SUBMISSION,
                                                                  education_group_year)})
    context.update({'deliberation': get_sessions_dates(academic_calendar_type.DELIBERATION,
                                                       education_group_year)})
    context.update({'scores_exam_diffusion': get_sessions_dates(academic_calendar_type.SCORES_EXAM_DIFFUSION,
                                                                education_group_year)})
    context.update({"can_edit_administrative_data":
                        is_program_manager(request.user, education_group=education_group_year.education_group)})
    return layout.render(request, "education_group/tab_administrative_data.html", context)


@login_required
@permission_required('base.can_edit_offer_year_calendar', raise_exception=True)
def education_group_edit_administrative_data(request, education_group_year_id):
    education_group_year = get_object_or_404(EducationGroupYear, pk=education_group_year_id)
    if not is_program_manager(request.user, education_group=education_group_year.education_group):
        raise PermissionDenied("Only program managers of the education group can edit.")

    formset_session = AdministrativeDataFormset(request.POST or None,
                                                form_kwargs={'education_group_year': education_group_year})

    offer_year_calendar = mdl.offer_year_calendar.search(education_group_year_id=education_group_year_id,
                                                         academic_calendar_reference=academic_calendar_type.COURSE_ENROLLMENT).first()

    course_enrollment = CourseEnrollmentForm(request.POST or None, instance=offer_year_calendar)

    f1 = course_enrollment.is_valid()
    f2 = formset_session.is_valid()

    if f1 and f2:
        formset_session.save()
        course_enrollment.save()
        messages.add_message(request, messages.SUCCESS, _('The administrative data has been successfully modified'))
        return HttpResponseRedirect(reverse('education_group_administrative', args=(education_group_year_id,)))

    return layout.render(request, "education_group/tab_edit_administrative_data.html", locals())


def get_root(education_group_year_id, request):
    root = request.GET.get('root')
    if root:
        parent = mdl.education_group_year.find_by_id(root)
    else:
        parent = education_group_year_id
    return parent


def get_sessions_dates(an_academic_calendar_type, an_education_group_year):
    date_dict = {}

    for cpt in range(NUMBER_SESSIONS):
        session = mdl.session_exam_calendar.get_by_session_reference_and_academic_year(cpt+1,
                                                                                       an_academic_calendar_type,
                                                                                       an_education_group_year.academic_year)
        if session:
            dates = mdl.offer_year_calendar.get_by_education_group_year_and_academic_calendar(session.academic_calendar,
                                                                                              an_education_group_year)
            key = 'session{}'.format(cpt+1)
            date_dict.update({key: dates})

    return date_dict


def get_dates(an_academic_calendar_type, an_education_group_year):
    ac = mdl.academic_calendar.get_by_reference_and_academic_year(an_academic_calendar_type,
                                                                  an_education_group_year.academic_year)
    if ac:
        dates = mdl.offer_year_calendar.get_by_education_group_year_and_academic_calendar(ac, an_education_group_year)
        return {'dates': dates}
    else:
        return {}


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def education_group_content(request, education_group_year_id):
    return _education_group_content_tab(request, education_group_year_id)


def _education_group_content_tab(request, education_group_year_id):
    education_group_year = mdl.education_group_year.find_by_id(education_group_year_id)
    parent = get_root(education_group_year_id, request)
    context = {'parent': parent,
               'education_group_year': education_group_year,
               'group_elements': _group_elements(education_group_year),
               }
    return layout.render(request, "education_group/tab_content.html", context)


def _group_elements(education_group_yr):
    group_elements = mdl.group_element_year.find_by_parent(education_group_yr)
    if group_elements:
        return _get_group_elements_data(group_elements)

    return None


def _get_group_elements_data(group_elements):
    group_elements_data = []
    for group_element in group_elements:
        group_element_values={'group_element': group_element}
        if group_element.child_leaf:
            _get_learning_unit_detail(group_element_values, group_element)
        elif group_element.child_branch:
            _get_education_group_detail(group_element_values, group_element)
        group_elements_data.append(group_element_values)
    return _sorting(group_elements_data)


def _sorting(group_elements_data):
    return sorted(group_elements_data,
                  key= lambda k: (k.get('group_element').current_order is None,
                                  k.get('group_element').current_order == -1,
                                  k.get('group_element').current_order))


def _get_education_group_detail(dict_param, group_element):
    dict_param.update({CODE_SCS: group_element.child_branch.partial_acronym,
                 TITLE: group_element.child_branch.title,
                 CREDITS_MIN: group_element.min_credits,
                 CREDITS_MAX: group_element.max_credits,
                 BLOCK: None})
    return dict_param


def _get_learning_unit_detail(dict_param, group_element):
    dict_param.update({CODE_SCS: group_element.child_leaf.acronym,
                 TITLE: group_element.child_leaf.title,
                 CREDITS_MIN: None,
                 CREDITS_MAX: None,
                 BLOCK: group_element.block,
                 SESSIONS_DEROGATION: group_element.sessions_derogation})
    return dict_param
