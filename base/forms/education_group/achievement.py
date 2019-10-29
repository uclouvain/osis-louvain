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
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_FR, LANGUAGE_CODE_EN
from base.business.learning_units.achievement import UP, DOWN
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_year import EducationGroupYear
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.text_label import TextLabel

ACTION_CHOICES = [
    (UP, UP),
    (DOWN, DOWN),
]


class EducationGroupAchievementForm(forms.ModelForm):
    french_text = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('French')
    )

    english_text = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('English')
    )

    class Meta:
        model = EducationGroupAchievement
        fields = ["code_name", "french_text", "english_text"]


class EducationGroupDetailedAchievementForm(EducationGroupAchievementForm):
    class Meta(EducationGroupAchievementForm.Meta):
        model = EducationGroupDetailedAchievement


class ActionForm(forms.Form):
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)


class EducationGroupAchievementCMSForm(forms.Form):
    education_group_year = None
    cms_text_label = None

    text_french = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('French')
    )

    text_english = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('English')
    )

    def __init__(self, *args, **kwargs):
        self.education_group_year = kwargs.pop('education_group_year')
        if not isinstance(self.education_group_year, EducationGroupYear):
            raise AttributeError('education_group_year parms must be an instance of EducationGroupYear')
        self.cms_text_label = kwargs.pop('cms_text_label')
        if not isinstance(self.cms_text_label, TextLabel):
            raise AttributeError('cms_text_label parms must be an instance of TextLabel')
        super().__init__(*args, **kwargs)

    def save(self):
        translated_text_upserted = []
        for language in [LANGUAGE_CODE_FR, LANGUAGE_CODE_EN]:
            upsert_result = translated_text.update_or_create(
                entity=entity_name.OFFER_YEAR,
                reference=self.education_group_year.pk,
                text_label=self.cms_text_label,
                language=language,
                defaults={'text': self._get_related_text(language)}
            )
            translated_text_upserted.append(upsert_result)
        return translated_text_upserted

    def _get_related_text(self, language):
        if language == LANGUAGE_CODE_FR:
            return self.cleaned_data['text_french']
        elif language == LANGUAGE_CODE_EN:
            return self.cleaned_data['text_english']
        raise AttributeError('Unsupported language {}'.format(language))
