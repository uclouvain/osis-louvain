# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import urllib.parse

from django.urls.converters import StringConverter

from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType


class GroupTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in GroupType.get_names():
            raise ValueError("%s value: is not a valid group type")
        return value

    def to_url(self, value):
        return value


class MiniTrainingTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in MiniTrainingType.get_names():
            raise ValueError("%s value: is not a valid mini-training type")
        return value

    def to_url(self, value):
        return value


class TrainingTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in TrainingType.get_names():
            raise ValueError("%s value: is not a valid training type")
        return value

    def to_url(self, value):
        return value


class AcronymConverter:

    regex = StringConverter.regex

    def to_python(self, value):
        return urllib.parse.unquote_plus(value)

    def to_url(self, value):
        return urllib.parse.quote_plus(value)


class MiniTrainingAcronymConverter:

    regex = r'[a-zA-Z0-9_%\-%\/]+'

    def to_python(self, value):
        return urllib.parse.unquote_plus(value)

    def to_url(self, value):
        return urllib.parse.quote_plus(value)
