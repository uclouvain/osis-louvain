##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

from reference.models import language


dic_code_language = {
    "chi": "chinese",
    "eng": "english",
    "fre": "french",
    "ger": "german",
    "jpn": "japanese"
}


def create_language(code, name):
    """
    Creates a language.
    :param code: code of the language (4 characters at max)
    :param name: name of the language
    :return: a language object
    """
    if language_exists(code, name):
        return None

    lang = language.Language(code=code, name=name)
    lang.save()
    return lang


def language_exists(code, name):
    """
    Check if the language already exists in the database.
    :param code: code of the language
    :param name: name of the language
    :return: true if the language already exists
    """
    if language.Language.objects.filter(code=code).exists():
        return True
    elif language.Language.objects.filter(name=name).exists():
        return True
    return False


def add_languages():
    """
    Add languages to the database
    :return:
    """
    # k corresponds to the code and v to the name.
    for (k,v) in dic_code_language.items():
        create_language(k, v)
