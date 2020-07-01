##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import string

import factory.fuzzy
from factory import DjangoModelFactory

from testing.providers import Language


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = 'reference.Language'
        django_get_or_create = ('code',)
        exclude = ("_language", )

    _language = factory.Faker("language")

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    code = factory.SelfAttribute("_language.code")
    name = factory.SelfAttribute("_language.name")
    recognized = factory.Faker('boolean', chance_of_getting_true=50)


class FrenchLanguageFactory(LanguageFactory):
    code = "FR"
    name = "Français"


class EnglishLanguageFactory(LanguageFactory):
    code = "EN"
    name = "Anglais"
