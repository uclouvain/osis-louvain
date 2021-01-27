#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from base.models.person import get_user_interface_language
from base.views.common import display_success_messages
from cms.contrib.forms import CmsEditForm
from cms.models import translated_text_label
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText


class UpdateCmsView(FormView):
    """
        Base View to modify cms for french and english language for a given label.
        The view must receive the label value either from GET or POST parameters.
    """
    template_name = 'cms/modal/modal_cms_edit_inner.html'
    form_class = CmsEditForm

    def get_entity(self):
        raise NotImplementedError()

    def get_reference(self):
        raise NotImplementedError()

    def get_references(self):
        raise NotImplementedError()

    def get_success_message(self, to_postpone: bool):
        if to_postpone:
            return _("%(label)s has been updated (with postpone)") % {"label": self.translated_label}
        return _("%(label)s has been updated (without postpone)") % {"label": self.translated_label}

    @property
    def label(self):
        label = self.request.GET.get('label') or self.request.POST.get('label')
        if not label:
            raise Http404()
        return label

    @cached_property
    def text_label(self):
        return TextLabel.objects.filter(label=self.label, entity=self.get_entity()).first()

    @cached_property
    def translated_label(self) -> str:
        return translated_text_label.get_label_translation(
            text_entity=self.get_entity(),
            label=self.label,
            language=get_user_interface_language(self.request.user)
        )

    def get_title(self):
        return self.translated_label

    def can_postpone(self) -> bool:
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = self.label
        context["title"] = self.get_title()
        context["can_postpone"] = self.can_postpone()
        return context

    def get_initial(self):
        try:
            text_english = TranslatedText.objects.filter(
                reference=self.get_reference(),
                entity=self.get_entity(),
                text_label=self.text_label,
                language=settings.LANGUAGE_CODE_EN,
            ).values_list("text", flat=True)[0]
        except IndexError:
            text_english = ""

        try:
            text_french = TranslatedText.objects.filter(
                reference=self.get_reference(),
                entity=self.get_entity(),
                text_label=self.text_label,
                language=settings.LANGUAGE_CODE_FR,
            ).values_list("text", flat=True)[0]
        except IndexError:
            text_french = ""
        return {
            "label": self.label,
            "text_english": text_english,
            "text_french": text_french
        }

    def form_valid(self, form: 'CmsEditForm'):
        text_english = form.cleaned_data["text_english"]
        text_french = form.cleaned_data["text_french"]
        to_postpone = form.cleaned_data["to_postpone"]

        languages = [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]

        if to_postpone and not self.can_postpone():
            raise PermissionDenied

        references = self.get_references() if to_postpone else [self.get_reference()]

        for lang, text in zip(languages, [text_english, text_french]):
            for ref in references:
                obj, created = TranslatedText.objects.update_or_create(
                    reference=ref,
                    entity=self.get_entity(),
                    text_label=self.text_label,
                    language=lang,
                    defaults={"text": text}
                )

        display_success_messages(self.request, self.get_success_message(bool(to_postpone)))

        return super().form_valid(form)
