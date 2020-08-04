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
import waffle
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView

from base.views import common


class FlagMixin:
    flag = None

    def dispatch(self, request, *args, **kwargs):
        if self.flag and not waffle.flag_is_active(request, self.flag):
            raise Http404
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class RulesRequiredMixin(UserPassesTestMixin):
    """CBV mixin extends the permission_required with rules on objects """
    rules = []

    def test_func(self):
        if not self.rules:
            return True

        try:
            # Requires SingleObjectMixin or equivalent ``get_object`` method
            return all(self._call_rule(rule) for rule in self.rules)

        except PermissionDenied as e:
            # The rules can override the default message
            self.permission_denied_message = str(e)
            return False

    def _call_rule(self, rule):
        """ The signature can be override with another object """
        return rule(self.request.user, self.get_object())


class AjaxTemplateMixin:
    ajax_template_suffix = "_inner"
    partial_reload = None
    force_reload = False

    def get_template_names(self):
        template_names = super().get_template_names()
        if self.request.is_ajax():
            template_names = [
                self._convert_template_name_to_ajax_template_name(template_name) for template_name in template_names
            ]
        return template_names

    @staticmethod
    def _convert_template_name_to_ajax_template_name(template_name):
        if "_inner.html" not in template_name:
            split = template_name.split('.html')
            split[-1] = '_inner'
            split.append('.html')
            return "".join(split)
        return template_name

    def form_valid(self, form):
        response = super().form_valid(form)
        return self._ajax_response() or response

    def forms_valid(self, forms):
        response = super().forms_valid(forms)
        return self._ajax_response() or response

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return self._ajax_response() or response

    def _ajax_response(self):
        # When the form is saved, we return only the url, not all the template
        if self.request.is_ajax():
            response = {"success": True}
            url = self.get_success_url()
            if url:
                response['success_url'] = url
            if self.partial_reload:
                response['partial_reload'] = self.partial_reload
            if self.force_reload:
                response['force_reload'] = self.force_reload
            return JsonResponse(response)


class DeleteViewWithDependencies(FlagMixin, RulesRequiredMixin, AjaxTemplateMixin, DeleteView):
    success_message = "The objects are been deleted successfully"
    protected_template = None
    protected_messages = None

    def get(self, request, *args, **kwargs):
        self.protected_messages = self.get_protected_messages()

        # If there is some protected messages, change the template
        if self.protected_messages:
            self.template_name = self.protected_template
        return super().get(request, *args, **kwargs)

    def get_protected_messages(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["protected_messages"] = self.protected_messages
        return context

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        common.display_success_messages(request, _(self.success_message))
        return result


# Inspired by https://gist.github.com/badri/4a1be2423ce9353373e1b3f2cc67b80b
class MultiFormMixin(ContextMixin):
    form_classes = {}
    prefixes = {}

    initial = {}
    prefix = None
    success_url = None
    instantiated_forms = {}

    def get_form_classes(self):
        return self.form_classes

    def get_forms(self, form_classes):
        self.instantiated_forms = dict([(key, self._create_form(key, class_name))
                                        for key, class_name in form_classes.items()])
        return self.instantiated_forms

    def get_all_forms(self):
        return self.get_forms(self.form_classes)

    def get_form_kwargs(self, form_name):
        kwargs = {}
        kwargs.update({'initial': self.get_initial(form_name)})
        kwargs.update({'prefix': self.get_prefix(form_name)})
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def forms_valid(self, forms):
        for form_name, form in forms.items():
            form_valid_method = '{form_name}_valid'.format(form_name=form_name)
            if hasattr(self, form_valid_method):
                getattr(self, form_valid_method)(form)
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(self.get_context_data(**forms))

    def get_initial(self, form_name):
        initial_method = 'get_%s_initial' % form_name
        if hasattr(self, initial_method):
            return getattr(self, initial_method)()
        else:
            return {}

    def get_prefix(self, form_name):
        return self.prefixes.get(form_name, self.prefix)

    def get_success_url(self):
        return self.success_url

    def _create_form(self, form_name, form_class):
        form_kwargs = self.get_form_kwargs(form_name)
        form = form_class(**form_kwargs)
        return form


class ProcessMultipleFormsView(ProcessFormView):

    def get(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        return self.render_to_response(self.get_context_data(**forms))

    def post(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        return self.process_forms(form_classes)

    def process_forms(self, form_classes):
        forms = self.get_forms(form_classes)
        forms_are_valid = all(form.is_valid() for key, form in forms.items())
        if forms_are_valid:
            return self.forms_valid(forms)
        return self.forms_invalid(forms)


class BaseMultipleFormsView(MultiFormMixin, ProcessMultipleFormsView):
    """
    A base view for displaying several forms.
    """


class MultiFormsView(TemplateResponseMixin, BaseMultipleFormsView):
    """
    A view for displaying several forms, and rendering a template response.
    """


class MultiFormsSuccessMessageMixin:

    def forms_valid(self, forms):
        response = super().forms_valid(forms)
        success_message = self.get_success_message(forms)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def forms_invalid(self, forms):
        response = super().forms_invalid(forms)
        return response

    def get_success_message(self, forms):
        return ""
