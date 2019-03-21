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
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from waffle.decorators import waffle_flag

from base.forms.education_group.common import EducationGroupModelForm, EducationGroupTypeForm
from base.forms.education_group.group import GroupForm
from base.forms.education_group.mini_training import MiniTrainingForm
from base.forms.education_group.training import TrainingForm
from base.models.academic_year import current_academic_year, AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.exceptions import ValidationWarning
from base.utils.cache import RequestCache
from base.views.common import display_success_messages
from base.views.education_groups.perms import can_create_education_group
from base.views.mixins import FlagMixin, AjaxTemplateMixin
from osis_common.decorators.ajax import ajax_required

FORMS_BY_CATEGORY = {
    education_group_categories.GROUP: GroupForm,
    education_group_categories.TRAINING: TrainingForm,
    education_group_categories.MINI_TRAINING: MiniTrainingForm,
}

TEMPLATES_BY_CATEGORY = {
    education_group_categories.GROUP: "education_group/create_groups.html",
    education_group_categories.TRAINING: "education_group/create_trainings.html",
    education_group_categories.MINI_TRAINING: "education_group/create_mini_trainings.html",
}


class SelectEducationGroupTypeView(FlagMixin, AjaxTemplateMixin, FormView):
    flag = "education_group_create"
    # rules = [can_create_education_group]
    # raise_exception = True
    template_name = "education_group/blocks/form/education_group_type.html"
    form_class = EducationGroupTypeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["category"] = self.kwargs["category"]
        kwargs["parent"] = get_object_or_404(
            EducationGroupYear, pk=self.kwargs["parent_id"]
        ) if self.kwargs.get("parent_id") else None
        return kwargs

    def form_valid(self, form):
        # Attach education_group_type to use it in get_success_url
        self.kwargs["education_group_type_pk"] = form.cleaned_data["name"].pk
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(create_education_group, kwargs=self.kwargs)


@login_required
@waffle_flag("education_group_create")
@can_create_education_group
def create_education_group(request, category, education_group_type_pk, parent_id=None):
    parent = get_object_or_404(EducationGroupYear, id=parent_id) if parent_id is not None else None
    education_group_type = get_object_or_404(EducationGroupType, pk=education_group_type_pk)

    request_cache = RequestCache(request.user, reverse('education_groups'))
    cached_data = request_cache.cached_data or {}

    academic_year = cached_data.get('academic_year')
    if not academic_year:
        cached_data['academic_year'] = current_academic_year()

    initial_academic_year = parent.academic_year_id if parent else cached_data.get('academic_year')
    form_education_group_year = FORMS_BY_CATEGORY[category](
        request.POST or None,
        parent=parent,
        user=request.user,
        education_group_type=education_group_type,
        initial={'academic_year': initial_academic_year}
    )

    if form_education_group_year.is_valid():
        return _common_success_redirect(request, form_education_group_year, parent)

    data = {
        "form_education_group_year": form_education_group_year.forms[forms.ModelForm],
        "form_education_group": form_education_group_year.forms[EducationGroupModelForm],
        "parent": parent,
    }

    if category == education_group_categories.TRAINING:
        data.update(
            {
                "form_hops": form_education_group_year.hops_form,
            }
        )

    return render(request, TEMPLATES_BY_CATEGORY.get(category), data)


def _common_success_redirect(request, form, parent=None):
    education_group_year = form.save()
    parent_id = parent.pk if parent else education_group_year.pk

    success_msg = [_get_success_message_for_creation_education_group_year(parent_id, education_group_year)]
    if hasattr(form, 'education_group_year_postponed'):
        success_msg += [
            _get_success_message_for_creation_education_group_year(egy.id, egy)
            for egy in form.education_group_year_postponed
        ]
    display_success_messages(request, success_msg, extra_tags='safe')

    # Redirect
    url = reverse("education_group_read", args=[parent_id, education_group_year.pk])
    return redirect(url)


def _get_success_message_for_creation_education_group_year(parent_id, education_group_year):
    link = reverse("education_group_read", args=[parent_id, education_group_year.id])
    return _("Education group year <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> successfully created.") % {
        "link": link,
        "acronym": education_group_year.acronym,
        "academic_year": education_group_year.academic_year,
    }


@ajax_required
@login_required
@permission_required("base.add_educationgroup", raise_exception=True)
def validate_field(request, category, education_group_year_pk=None):
    accepted_fields = ["partial_acronym", "acronym"]

    academic_year = AcademicYear.objects.get(pk=request.GET["academic_year"])
    acronym = request.GET.get("acronym")
    partial_acronym = request.GET.get("partial_acronym")

    egy = EducationGroupYear(academic_year=academic_year, acronym=acronym, partial_acronym=partial_acronym,
                             education_group_type=EducationGroupType(category=category))

    # This is an update
    if education_group_year_pk:
        egy = get_object_or_404(EducationGroupYear, pk=education_group_year_pk)
        egy.acronym = acronym
        egy.partial_acronym = partial_acronym

    response = {}

    for field in accepted_fields:
        try:
            attr_name = 'clean_{field_name}'.format(field_name=field)
            clean_field_func = getattr(egy, attr_name)
            if clean_field_func:
                clean_field_func(raise_warnings=True)
        except ValidationWarning as w:
            response[field] = {'msg': w.message_dict[field][0], 'level': messages.DEFAULT_TAGS[messages.WARNING]}
        except ValidationError as e:
            response[field] = {'msg': e.message_dict[field][0], 'level': messages.DEFAULT_TAGS[messages.ERROR]}

    return JsonResponse(response)
