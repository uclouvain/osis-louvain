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
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.person import get_user_interface_language
from cms.enums import entity_name
from cms.models import translated_text_label, translated_text
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from education_group.views.group.common_read import Tab, GroupRead
from osis_common.utils.models import get_object_or_none
from program_management.ddd.domain.node import Node


class GroupUpdateGeneralInformation(GroupRead):
    template_name = 'education_group/blocks/modal/modal_pedagogy_edit_inner.html'
    active_tab = Tab.GENERAL_INFO

    @staticmethod
    def get_form_class():
        return EducationGroupPedagogyEditForm

    def post(self, request, *args, **kwargs):
        if not self.have_general_information_tab():
            return redirect(
                reverse('group_identification', kwargs=self.kwargs) + "?path={}".format(self.get_path())
            )
        form = self.get_form_class()(request.POST)
        redirect_url = reverse('group_identification', kwargs=self.kwargs) + "?path={}".format(self.get_path())

        if form.is_valid():
            label = form.cleaned_data['label']

            self.update_cms(form, label)

            redirect_url += "#section_{label_name}".format(label_name=label)
        return redirect(redirect_url)

    def update_cms(self, form: EducationGroupPedagogyEditForm, label: str):
        for lang in [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]:
            self._update_cms_for_specific_lang(form, lang, label)

    def _update_cms_for_specific_lang(self, form: EducationGroupPedagogyEditForm, lang: str, label: str):
        node = self.get_object()
        entity = entity_name.get_offers_or_groups_entity_from_node(node)
        obj = translated_text.get_groups_or_offers_cms_reference_object(node)
        text_label = TextLabel.objects.filter(label=label, entity=entity).first()

        record, created = TranslatedText.objects.get_or_create(
            reference=obj.pk,
            entity=entity,
            text_label=text_label,
            language=lang
        )
        record.text = form.cleaned_data['text_english' if lang == settings.LANGUAGE_CODE_EN else 'text_french']
        record.save()

    def get_context_data(self, **kwargs):
        node = self.get_object()

        label_name = self.request.GET.get('label')

        initial_values = self.get_translated_texts(node)

        context = {
            'label': label_name,
            'form': EducationGroupPedagogyEditForm(initial=initial_values),
            'group_to_parent': self.request.GET.get("group_to_parent") or '0',
            'translated_label': translated_text_label.get_label_translation(
                text_entity=entity_name.get_offers_or_groups_entity_from_node(node),
                label=label_name,
                language=get_user_interface_language(self.request.user)
            )
        }

        return {
            **super().get_context_data(**kwargs),
            **context
        }

    def get_translated_texts(self, node: Node):
        initial_values = {'label': self.request.GET.get('label')}
        for lang in [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]:
            initial_values.update(self._get_translated_text_from_lang(node, lang))
        return initial_values

    def _get_translated_text_from_lang(self, node: Node, lang: str):
        obj = translated_text.get_groups_or_offers_cms_reference_object(node)
        label = self.request.GET.get('label')
        node = self.get_object()
        entity = entity_name.get_offers_or_groups_entity_from_node(node)
        text = get_object_or_none(
            TranslatedText.objects.select_related('text_label'),
            reference=str(obj.pk),
            text_label__label=label,
            text_label__entity=entity,
            entity=entity,
            language=lang
        )
        if text:
            return {'text_english' if lang == settings.LANGUAGE_CODE_EN else 'text_french': text.text}
        return {}

    def get_success_url(self):
        node = self.get_object()
        return reverse('group_general_information', args=[node.year, node.code]) + '?path={}'.format(self.get_path())
