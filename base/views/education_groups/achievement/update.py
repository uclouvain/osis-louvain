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
import functools

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, UpdateView

from base.business.education_groups.general_information_sections import CMS_LABEL_PROGRAM_AIM, \
    CMS_LABEL_ADDITIONAL_INFORMATION
from base.forms.education_group.achievement import ActionForm, EducationGroupAchievementForm, \
    EducationGroupDetailedAchievementForm, EducationGroupAchievementCMSForm
from base.models.education_group_year import EducationGroupYear
from base.views.common import display_error_messages
from base.views.education_groups.achievement.common import EducationGroupAchievementMixin, \
    EducationGroupDetailedAchievementMixin
from base.views.mixins import AjaxTemplateMixin
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.text_label import TextLabel
from education_group.ddd.domain.service.identity_search import TrainingIdentitySearch
from education_group.views.proxy.read import Tab
from osis_role.contrib.views import PermissionRequiredMixin
from program_management.models.element import Element


class EducationGroupAchievementAction(EducationGroupAchievementMixin, FormView):
    form_class = ActionForm
    http_method_names = ('post',)
    permission_required = 'base.change_educationgroupachievement'
    raise_exception = True

    def form_valid(self, form):
        if form.cleaned_data['action'] == 'up':
            self.get_object().up()
        elif form.cleaned_data['action'] == 'down':
            self.get_object().down()
        return super().form_valid(form)

    def form_invalid(self, form):
        display_error_messages(self.request, _("Invalid action"))
        return HttpResponseRedirect(self.get_success_url())

    def get_permission_object(self):
        return self.get_object().education_group_year

    def get_success_url(self):
        prefix = 'training_' if self.education_group_year.is_training() else 'mini_training_'
        return reverse(
            prefix + 'skills_achievements', args=[self.kwargs['year'], self.kwargs['code']]
        ) + '?path={}&tab={}#achievement_{}'.format(
            self.request.GET['path'], Tab.SKILLS_ACHIEVEMENTS, self.kwargs['education_group_achievement_pk']
        )


class UpdateEducationGroupAchievement(PermissionRequiredMixin, AjaxTemplateMixin, EducationGroupAchievementMixin,
                                      UpdateView):
    template_name = "education_group/blocks/form/update_achievement.html"
    form_class = EducationGroupAchievementForm
    permission_required = 'base.change_educationgroupachievement'
    raise_exception = True
    force_reload = True

    def get_permission_object(self):
        return self.get_object().education_group_year


class UpdateEducationGroupDetailedAchievement(EducationGroupDetailedAchievementMixin, UpdateEducationGroupAchievement):
    form_class = EducationGroupDetailedAchievementForm
    force_reload = True

    def get_permission_object(self):
        return self.education_group_achievement.education_group_year


class EducationGroupDetailedAchievementAction(EducationGroupDetailedAchievementMixin, EducationGroupAchievementAction):
    def get_permission_object(self):
        return self.education_group_achievement.education_group_year

    def get_success_url(self):
        prefix = 'training_' if self.education_group_year.is_training() else 'mini_training_'
        return reverse(
            prefix + 'skills_achievements', args=[self.kwargs['year'], self.kwargs['code']]
        ) + '?path={}&tab={}#detail_achievements_{}'.format(
            self.request.GET['path'], Tab.SKILLS_ACHIEVEMENTS, self.kwargs['education_group_detail_achievement_pk']
        )


class EducationGroupAchievementCMS(PermissionRequiredMixin, SuccessMessageMixin, AjaxTemplateMixin, FormView):
    cms_text_label = None
    template_name = "education_group/blocks/modal/modal_pedagogy_edit.html"

    # PermissionRequiredMixin
    permission_required = 'base.change_educationgroupachievement'
    raise_exception = True

    @functools.lru_cache()
    def get_path(self) -> str:
        path = self.request.GET.get('path')
        if path is None:
            root_element = Element.objects.get(group_year__educationgroupversion__offer_id=self.kwargs['offer_id'])
            path = str(root_element.pk)
        return path

    @cached_property
    def education_group_year(self):
        return get_object_or_404(EducationGroupYear, pk=self.kwargs['education_group_year_id'])

    def get_form_kwargs(self):
        kwargs = {
            **super().get_form_kwargs(),
            'education_group_year': self.education_group_year,
            'cms_text_label': self.cms_text_label
        }
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        training_identity = TrainingIdentitySearch().get_from_education_group_year_id(self.kwargs['offer_id'])
        return reverse(
            'education_group_read_proxy',
            args=[training_identity.year, training_identity.acronym]
        ) + '?path={}&tab={}#achievement_'.format(self.get_path(), Tab.SKILLS_ACHIEVEMENTS)

    def get_initial(self):
        initial = super().get_initial()
        translated_texts = translated_text.search(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.pk,
            text_labels_name=[self.cms_text_label.label]
        ).values('text', 'language')

        for trans_text in translated_texts:
            if trans_text['language'] == settings.LANGUAGE_CODE_FR:
                initial['text_french'] = trans_text['text']
            elif trans_text['language'] == settings.LANGUAGE_CODE_EN:
                initial['text_english'] = trans_text['text']
        return initial

    def get_permission_object(self):
        return self.education_group_year


class EducationGroupAchievementProgramAim(EducationGroupAchievementCMS):
    form_class = EducationGroupAchievementCMSForm

    @cached_property
    def cms_text_label(self):
        return TextLabel.objects.prefetch_related(
            Prefetch('translatedtextlabel_set', to_attr="translated_text_labels")
        ).get(label=CMS_LABEL_PROGRAM_AIM)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["translated_label"] = _('the program aims')
        context["url_action"] = reverse(
            'education_group_achievement_program_aim',
            args=[self.kwargs["offer_id"], self.kwargs["offer_id"]]
        ) + '?path={}&tab={}#achievement_'.format(self.request.GET['path'], Tab.SKILLS_ACHIEVEMENTS)
        return context

    # SuccessMessageMixin
    def get_success_message(self, cleaned_data):
        return _("The program aim has been updated")


class EducationGroupAchievementAdditionalInformation(EducationGroupAchievementCMS):
    form_class = EducationGroupAchievementCMSForm

    @cached_property
    def cms_text_label(self):
        return TextLabel.objects.prefetch_related(
            Prefetch('translatedtextlabel_set', to_attr="translated_text_labels")
        ).get(label=CMS_LABEL_ADDITIONAL_INFORMATION)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["translated_label"] = _('additional informations')
        context["url_action"] = reverse(
            'education_group_achievement_additional_information',
            args=[self.kwargs["offer_id"], self.kwargs["offer_id"]]
        ) + '?path={}&tab={}#achievement_'.format(self.request.GET['path'], Tab.SKILLS_ACHIEVEMENTS)
        return context

    # SuccessMessageMixin
    def get_success_message(self, cleaned_data):
        return _("The additional informations has been updated")
