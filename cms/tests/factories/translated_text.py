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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import factory.fuzzy
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from .text_label import TextLabelFactory
from ...models.translated_text import TranslatedText


class TranslatedTextFactory(factory.django.DjangoModelFactory):
    class Meta:
        exclude = ['content_object']
        model = "cms.TranslatedText"

    language = settings.LANGUAGE_CODE_FR  # French default
    text_label = factory.SubFactory(TextLabelFactory)
    entity = factory.fuzzy.FuzzyText(prefix="Entity ", length=15)
    object_id = factory.SelfAttribute('content_object.id')
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object))
    text = None


class TranslatedTextFactoryEducationGroupYear(TranslatedTextFactory):
    content_object = factory.SubFactory(EducationGroupYearFactory)

    class Meta:
        model = TranslatedText


class TranslatedTextFactoryLearningUnitYear(TranslatedTextFactory):
    content_object = factory.SubFactory(LearningUnitYearFactory)

    class Meta:
        model = TranslatedText


class TranslatedTextRandomFactory(TranslatedTextFactory):
    text = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, ext_word_list=None)


class EnglishTranslatedTextRandomFactory(TranslatedTextRandomFactory):
    language = settings.LANGUAGE_CODE_EN
