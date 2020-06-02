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

from dal import autocomplete
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from rules.contrib.views import permission_required

from base import models as mdl_base
from base.business.education_group import has_coorganization
from base.forms.education_group.common import EducationGroupModelForm
from base.forms.education_group.coorganization import OrganizationFormset
from base.forms.education_group.group import GroupForm
from base.forms.education_group.mini_training import MiniTrainingForm
from base.forms.education_group.training import TrainingForm, CertificateAimsForm
from base.models import program_manager
from base.models.certificate_aim import CertificateAim
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.group_element_year import GroupElementYear
from base.views.common import display_success_messages, display_warning_messages, show_error_message_for_form_invalid
from program_management.forms.tree.attach import GroupElementYearFormset


def get_education_group_year_by_pk(request, root_id, education_group_year_id):
    return get_object_or_404(
        EducationGroupYear.objects.select_related('education_group_type').prefetch_related(
            Prefetch(
                'groupelementyear_set',
                queryset=GroupElementYear.objects.select_related(
                    'child_leaf__learning_container_year',
                    'child_branch__education_group_type',
                    'parent__education_group_type'
                )
            )
        ),
        pk=education_group_year_id
    )


# TODO: Split view of update_certification_aims with update_education_group
@login_required
def update_education_group(request, root_id, education_group_year_id):
    education_group_year = get_object_or_404(
        EducationGroupYear.objects.select_related('education_group'),
        pk=education_group_year_id
    )
    person = request.user.person

    if program_manager.is_program_manager(request.user, education_group=education_group_year.education_group) \
            and not any((request.user.is_superuser, person.is_faculty_manager, person.is_central_manager)):
        return _update_certificate_aims(request, root_id, education_group_year)
    return update_education_group_year(request, root_id, education_group_year_id)


@permission_required('base.change_educationgroupcertificateaim',
                     fn=lambda request, root_id, education_group_year: education_group_year)
def _update_certificate_aims(request, root_id, education_group_year):
    root = get_object_or_404(EducationGroupYear, pk=root_id)
    form_certificate_aims = CertificateAimsForm(request.POST or None, instance=education_group_year)
    if form_certificate_aims.is_valid():
        url_redirect = _common_success_redirect(request, form_certificate_aims, root)
        return JsonResponse({'success_url': url_redirect.url})

    return render(request, "education_group/blocks/form/training_certificate.html", {
        "education_group_year": education_group_year,
        "form_certificate_aims": form_certificate_aims
    })


@login_required
@permission_required('base.change_educationgroup', fn=get_education_group_year_by_pk, raise_exception=True)
def update_education_group_year(request, root_id, education_group_year_id):
    education_group_year = get_education_group_year_by_pk(request, root_id, education_group_year_id)
    # Store root in the instance to avoid to pass the root in methods
    # it will be used in the templates.
    education_group_year.root = root_id

    groupelementyear_formset = GroupElementYearFormset(
        request.POST or None,
        prefix='group_element_year_formset',
        queryset=education_group_year.groupelementyear_set.all()
    )
    root = get_object_or_404(EducationGroupYear, pk=root_id)
    view_function = _get_view(education_group_year.education_group_type.category)
    return view_function(request, education_group_year, root, groupelementyear_formset)


def _get_view(category):
    return {
        education_group_categories.TRAINING: _update_training,
        education_group_categories.MINI_TRAINING: _update_mini_training,
        education_group_categories.GROUP: _update_group
    }[category]


def _common_success_redirect(request, form, root, groupelementyear_form=None):
    groupelementyear_changed = []
    if groupelementyear_form:
        groupelementyear_form.save()
        groupelementyear_changed = groupelementyear_form.changed_forms()

    education_group_year = form.save()
    success_msgs = []
    if not education_group_year.education_group.end_year or \
            education_group_year.education_group.end_year.year >= education_group_year.academic_year.year:
        success_msgs = [_get_success_message_for_update_education_group_year(root.pk, education_group_year)]

    if hasattr(form, 'education_group_year_postponed'):
        success_msgs += [
            _get_success_message_for_update_education_group_year(egy.id, egy)
            for egy in form.education_group_year_postponed
        ]
    if hasattr(form, 'education_group_year_deleted'):
        success_msgs += [
            _get_success_message_for_deleted_education_group_year(egy)
            for egy in form.education_group_year_deleted
        ]
    if groupelementyear_changed:
        anac = str(education_group_year.academic_year)
        if len(groupelementyear_changed) > 1:
            success_msgs += ["{} : <ul><li>{}</li></ul>".format(
                _("The following links has been updated"),
                "</li><li>".join([
                    " - ".join([gey.instance.child_branch.partial_acronym, gey.instance.child_branch.acronym, anac])
                    if gey.instance.child_branch else " - ".join([gey.instance.child_leaf.acronym, anac])
                    for gey in groupelementyear_changed
                ])
            )]
        else:
            gey = groupelementyear_changed[0].instance
            success_msgs += [_("The link of %(acronym)s has been updated") % {
                'acronym': " - ".join([gey.child_branch.partial_acronym, gey.child_branch.acronym, anac])
                if gey.child_branch else " - ".join([gey.child_leaf.acronym, anac])
            }]
    url = _get_success_redirect_url(root, education_group_year)
    display_success_messages(request, success_msgs, extra_tags='safe')

    if hasattr(form, "warnings"):
        display_warning_messages(request, form.warnings)

    return redirect(url)


def _get_success_message_for_update_education_group_year(root_id, education_group_year):
    link = reverse("education_group_read", args=[root_id, education_group_year.id])
    return _("Education group year <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfuly updated.") % {
        "link": link,
        "acronym": education_group_year.acronym,
        "academic_year": education_group_year.academic_year,
    }


def _get_success_message_for_deleted_education_group_year(education_group_year):
    return _("Education group year %(acronym)s (%(academic_year)s) successfuly deleted.") % {
        "acronym": education_group_year.acronym,
        "academic_year": education_group_year.academic_year,
    }


def _get_success_redirect_url(root, education_group_year):
    is_current_viewed_deleted = not mdl_base.education_group_year.search(id=education_group_year.id).exists()
    if is_current_viewed_deleted:
        # Case current updated is deleted, we will take the latest existing [At this stage, we always have lastest]
        qs = mdl_base.education_group_year.search().filter(education_group=education_group_year.education_group) \
            .order_by('academic_year__year') \
            .last()
        url = reverse("education_group_read", args=[qs.pk, qs.id])
    else:
        url = reverse("education_group_read", args=[root.pk, education_group_year.id])
    return url


def _update_group(request, education_group_year, root, groupelementyear_formset):
    # TODO :: IMPORTANT :: Fix urls patterns to get the GroupElementYear_id and the root_id in the url path !
    # TODO :: IMPORTANT :: Need to update form to filter on list of parents, not only on the first direct parent
    form_education_group_year = GroupForm(request.POST or None, instance=education_group_year, user=request.user)
    html_page = "education_group/update_groups.html"
    has_content = len(groupelementyear_formset.queryset) > 0
    can_change_content = request.user.has_perm('base.change_link_data', education_group_year)
    if request.method == 'POST':
        if form_education_group_year.is_valid() and \
                (not (has_content and can_change_content) or groupelementyear_formset.is_valid()):
            return _common_success_redirect(
                request,
                form_education_group_year,
                root, groupelementyear_formset if has_content and can_change_content else None
            )
        else:
            show_error_message_for_form_invalid(request)

    return render(request, html_page, {
        "education_group_year": education_group_year,
        "form_education_group_year": form_education_group_year.forms[forms.ModelForm],
        "form_education_group": form_education_group_year.forms[EducationGroupModelForm],
        'group_element_years': groupelementyear_formset,
        'show_minor_major_option_table': education_group_year.is_minor_major_option_list_choice,
        "show_content_tab": can_change_content
    })


def _update_training(request, education_group_year, root, groupelementyear_formset):
    # TODO :: IMPORTANT :: Fix urls patterns to get the GroupElementYear_id and the root_id in the url path !
    # TODO :: IMPORTANT :: Need to update form to filter on list of parents, not only on the first direct parent
    form_education_group_year = TrainingForm(request.POST or None, user=request.user, instance=education_group_year)
    coorganization_formset = None
    has_content = len(groupelementyear_formset.queryset) > 0
    can_change_content = request.user.has_perm('base.change_link_data', education_group_year)
    forms_valid = all(
        [form_education_group_year.is_valid(),
         not (has_content and can_change_content) or groupelementyear_formset.is_valid()]
    )
    if has_coorganization(education_group_year):
        coorganization_formset = OrganizationFormset(
            data=request.POST or None,
            form_kwargs={'education_group_year': education_group_year, 'user': request.user},
            queryset=education_group_year.coorganizations
        )
        forms_valid = forms_valid and coorganization_formset.is_valid()
    if request.method == 'POST':
        if forms_valid:
            if has_coorganization(education_group_year):
                coorganization_formset.save()
            return _common_success_redirect(
                request, form_education_group_year, root,
                groupelementyear_formset if has_content and can_change_content else None
            )
        else:
            show_error_message_for_form_invalid(request)

    return render(request, "education_group/update_trainings.html", {
        "education_group_year": education_group_year,
        "form_education_group_year": form_education_group_year.forms[forms.ModelForm],
        "form_education_group": form_education_group_year.forms[EducationGroupModelForm],
        "form_coorganization": coorganization_formset,
        "form_hops": form_education_group_year.hops_form,
        "show_coorganization": has_coorganization(education_group_year),
        "show_diploma_tab": form_education_group_year.show_diploma_tab(),
        "show_content_tab": can_change_content,
        'can_change_coorganization':
            request.user.has_perm('base.change_educationgrouporganization', education_group_year),
        'group_element_years': groupelementyear_formset,
        "is_finality_types": education_group_year.is_finality
    })


class CertificateAimAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return CertificateAim.objects.none()

        qs = CertificateAim.objects.all()

        if self.q:
            if self.q.isdigit():
                qs = qs.filter(code=self.q)
            else:
                qs = qs.filter(description__icontains=self.q)

        section = self.forwarded.get('section', None)
        if section:
            qs = qs.filter(section=section)

        return qs

    def get_result_label(self, result):
        return format_html('{} - {} {}', result.section, result.code, result.description)


def _update_mini_training(request, education_group_year, root, groupelementyear_formset):
    # TODO :: IMPORTANT :: Fix urls patterns to get the GroupElementYear_id and the root_id in the url path !
    # TODO :: IMPORTANT :: Need to upodate form to filter on list of parents, not only on the first direct parent
    form = MiniTrainingForm(request.POST or None, instance=education_group_year, user=request.user)
    can_change_content = request.user.has_perm('base.change_link_data', education_group_year)
    if request.method == 'POST':
        has_content = len(groupelementyear_formset.queryset) > 0
        forms_valid = all(
            [form.is_valid(), not (has_content and can_change_content) or groupelementyear_formset.is_valid()]
        )
        if forms_valid:
            return _common_success_redirect(
                request, form, root, groupelementyear_formset if has_content and can_change_content else None
            )
        else:
            show_error_message_for_form_invalid(request)

    return render(request, "education_group/update_minitrainings.html", {
        "form_education_group_year": form.forms[forms.ModelForm],
        "education_group_year": education_group_year,
        "form_education_group": form.forms[EducationGroupModelForm],
        'group_element_years': groupelementyear_formset,
        "show_content_tab": can_change_content,
    })
