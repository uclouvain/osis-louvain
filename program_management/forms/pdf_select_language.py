from django import forms
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _


class PDFSelectLanguage(forms.Form):
    language = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=settings.LANGUAGES,
        label=_('Select a language'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['language'] = translation.get_language()
