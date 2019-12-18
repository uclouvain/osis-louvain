############################################################################
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
############################################################################
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.views.generic.base import RedirectView, View

from base.models.education_group_year import EducationGroupYear
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache
from base.views.common import display_warning_messages, display_error_messages
from base.views.education_groups import perms
from program_management.business.group_element_years.attach import AttachEducationGroupYearStrategy, \
    AttachLearningUnitYearStrategy
from program_management.business.group_element_years.detach import DetachEducationGroupYearStrategy, \
    DetachLearningUnitYearStrategy
from program_management.business.group_element_years.management import fetch_elements_selected, fetch_source_link
from program_management.forms.group_element_year import GroupElementYearForm, BaseGroupElementYearFormset
from program_management.views.generic import GenericGroupElementYearMixin


class AttachCheckView(GenericGroupElementYearMixin, View):
    rules = []

    def get(self, request, *args, **kwargs):
        error_messages = []

        try:
            perms.can_change_education_group(self.request.user, self.education_group_year)
        except PermissionDenied as e:
            error_messages.append(str(e))

        elements_to_attach = fetch_elements_selected(self.request.GET, self.request.user)
        if not elements_to_attach:
            error_messages.append(_("Please cut or copy an item before attach it"))

        error_messages.extend(_check_attach(self.education_group_year, elements_to_attach))

        return JsonResponse({"error_messages": error_messages})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.rules:
            try:
                self.rules[0](self.request.user, self.education_group_year)

            except PermissionDenied as e:
                return render(request, 'education_group/blocks/modal/modal_access_denied.html', {'access_message': e})

        return super(AttachCheckView, self).dispatch(request, *args, **kwargs)


class PasteElementFromCacheToSelectedTreeNode(GenericGroupElementYearMixin, RedirectView):

    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        self.pattern_name = 'group_element_year_create'

        try:
            perms.can_change_education_group(self.request.user, self.education_group_year)
        except PermissionDenied as e:
            display_warning_messages(self.request, str(e))

        cached_data = ElementCache(self.request.user).cached_data

        if cached_data:

            action_from_cache = cached_data.get('action')

            if action_from_cache == ElementCache.ElementCacheAction.CUT.value:
                kwargs['group_element_year_id'] = fetch_source_link(self.request.GET, self.request.user).id
                self.pattern_name = 'group_element_year_move'

        return super().get_redirect_url(*args, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.rules:
            try:
                self.rules[0](self.request.user, self.education_group_year)

            except PermissionDenied as e:
                return render(request, 'education_group/blocks/modal/modal_access_denied.html', {'access_message': e})

        return super(PasteElementFromCacheToSelectedTreeNode, self).dispatch(request, *args, **kwargs)


class CreateGroupElementYearView(GenericGroupElementYearMixin, CreateView):
    template_name = "group_element_year/group_element_year_comment_inner.html"

    def get_form_class(self):
        elements_to_attach = fetch_elements_selected(self.request.GET, self.request.user)
        if not elements_to_attach:
            display_warning_messages(self.request, _("Please cut or copy an item before attach it"))

        return modelformset_factory(
            model=GroupElementYear,
            form=GroupElementYearForm,
            formset=BaseGroupElementYearFormset,
            extra=len(elements_to_attach),
        )

    def get_form_kwargs(self):
        """ For the creation, the group_element_year needs a parent and a child """
        kwargs = super().get_form_kwargs()

        # Formset don't use instance parameter
        if "instance" in kwargs:
            del kwargs["instance"]
        kwargs_form_kwargs = []

        children = fetch_elements_selected(self.request.GET, self.request.user)

        messages = _check_attach(self.education_group_year, children)
        if messages:
            display_error_messages(self.request, messages)

        for child in children:
            kwargs_form_kwargs.append({
                'parent': self.education_group_year,
                'child_branch': child if isinstance(child, EducationGroupYear) else None,
                'child_leaf': child if isinstance(child, LearningUnitYear) else None,
                'empty_permitted': False
            })

        kwargs["form_kwargs"] = kwargs_form_kwargs
        kwargs["queryset"] = GroupElementYear.objects.none()
        return kwargs

    def form_valid(self, form):
        ElementCache(self.request.user).clear()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = context["form"]
        if len(context["formset"]) > 0:
            context['is_education_group_year_formset'] = bool(context["formset"][0].instance.child_branch)
        context["education_group_year"] = self.education_group_year
        return context

    def get_success_message(self, cleaned_data):
        return _("The content of %(acronym)s has been updated.") % {"acronym": self.education_group_year.verbose}

    def get_success_url(self):
        """ We'll reload the page """
        return


class MoveGroupElementYearView(CreateGroupElementYearView):
    template_name = "group_element_year/group_element_year_comment_inner.html"

    @cached_property
    def detach_strategy(self):
        obj = self.get_object()
        strategy_class = DetachEducationGroupYearStrategy if obj.child_branch else DetachLearningUnitYearStrategy
        return strategy_class(obj)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        try:
            perms.can_change_education_group(self.request.user, self.get_object().parent)
        except PermissionDenied as e:
            msg = "{}: {}".format(str(self.get_object().parent), str(e))
            display_warning_messages(self.request, msg)

        if not self.detach_strategy.is_valid():
            display_error_messages(self.request, self.detach_strategy.errors)

        return kwargs

    def form_valid(self, form):
        self.detach_strategy.post_valid()
        obj = self.get_object()
        obj.delete()
        return super().form_valid(form)


def _check_attach(parent: EducationGroupYear, elements_to_attach):
    error_messages = []
    for element in elements_to_attach:
        try:
            strategy = AttachEducationGroupYearStrategy if isinstance(element, EducationGroupYear) else \
                AttachLearningUnitYearStrategy
            strategy(parent=parent, child=element).is_valid()
        except ValidationError as e:
            for msg in e.messages:
                msg_prefix = _("Element selected %(element)s") % {
                    "element": "{} - {}".format(element.academic_year, element.acronym)
                }
                error_messages.append("{}: {}".format(msg_prefix, msg))
    return error_messages
