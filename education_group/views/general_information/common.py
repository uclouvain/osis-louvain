##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import functools
import itertools
from enum import Enum

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView, FormView
from django.utils.translation import gettext_lazy as _

from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.education_group_year import EducationGroupYear
from base.views.common import display_success_messages
from base.views.mixins import AjaxTemplateMixin
from cms.enums import entity_name
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from education_group.views.serializers import general_information
from osis_role.contrib.views import PermissionRequiredMixin, AjaxPermissionRequiredMixin


class Tab(Enum):
    GENERAL_INFO = 0


class CommonGeneralInformation(PermissionRequiredMixin, TemplateView):
    # PermissionRequiredMixin
    permission_required = 'base.view_educationgroup'
    raise_exception = True
    template_name = "education_group_app/general_information/common.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "object": self.get_object(),
            "tab_urls": self.get_tab_urls(),
            "sections": self.get_sections(),
            "update_label_url": self.get_update_label_url(),
            "publish_url": self.get_publish_url(),
            "can_edit_information": self.request.user.has_perm(
                "base.change_commonpedagogyinformation", self.get_object()
            ),
        }

    def get_tab_urls(self):
        return {
             Tab.GENERAL_INFO: {
                'text': _('General informations'),
                'active': True,
                'display': True,
                'url': reverse('common_general_information', kwargs={'year': self.kwargs['year']})
             }
        }

    def get_sections(self):
        return general_information.get_sections_of_common(self.kwargs['year'], self.request.LANGUAGE_CODE)

    def get_object(self):
        try:
            return EducationGroupYear.objects.get_common(academic_year__year=self.kwargs['year'])
        except EducationGroupYear.DoesNotExist:
            raise Http404

    def get_update_label_url(self):
        return reverse('update_common_general_information', kwargs={'year': self.kwargs['year']}) + "?path="

    def get_publish_url(self):
        return reverse('publish_common_general_information', kwargs={'year': self.kwargs['year']})


class UpdateCommonGeneralInformation(AjaxPermissionRequiredMixin, AjaxTemplateMixin, FormView):
    template_name = "education_group/blocks/modal/modal_pedagogy_edit_inner.html"
    form_class = EducationGroupPedagogyEditForm
    permission_required = 'base.change_commonpedagogyinformation'

    def form_valid(self, form):
        entity = entity_name.OFFER_YEAR
        text_label = TextLabel.objects.get(label=self.get_label(), entity=entity)

        TranslatedText.objects.update_or_create(
            reference=EducationGroupYear.objects.get_common(academic_year__year=self.kwargs['year']).pk,
            entity=entity,
            text_label=text_label,
            language=settings.LANGUAGE_CODE_FR,
            defaults={'text': form.cleaned_data['text_french']}
        )
        TranslatedText.objects.update_or_create(
            reference=EducationGroupYear.objects.get_common(academic_year__year=self.kwargs['year']).pk,
            entity=entity,
            text_label=text_label,
            language=settings.LANGUAGE_CODE_EN,
            defaults={'text': form.cleaned_data['text_english']}
        )
        display_success_messages(self.request, _('General informations have been updated'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'translated_label': self.get_translated_text()['label_translated']
        }

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'initial': {
                'label': self.get_label(),
                'text_french': self.get_translated_text()['text_fr'],
                'text_english': self.get_translated_text()['text_en'],
            },
        }

    def get_permission_object(self):
        try:
            return EducationGroupYear.objects.get_common(academic_year__year=self.kwargs['year'])
        except EducationGroupYear.DoesNotExist:
            raise Http404

    def get_success_url(self):
        return reverse('common_general_information', kwargs={'year': self.kwargs['year']})

    @functools.lru_cache()
    def get_translated_text(self):
        sections = general_information.get_sections_of_common(self.kwargs['year'], self.request.LANGUAGE_CODE)
        return next(
            translated_text for translated_text in itertools.chain.from_iterable(sections.values())
            if translated_text and translated_text['label_id'] == self.get_label()
        )

    def get_label(self):
        if self.request.method == 'POST':
            return self.request.POST.get('label')
        return self.request.GET.get('label')
