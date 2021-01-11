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
import datetime
import attr


@attr.s(slots=True)
class DescriptionFiche:
    resume = attr.ib(type=str, default=None)
    resume_en = attr.ib(type=str, default=None)
    teaching_methods = attr.ib(type=str, default=None)
    teaching_methods_en = attr.ib(type=str, default=None)
    evaluation_methods = attr.ib(type=str, default=None)
    evaluation_methods_en = attr.ib(type=str, default=None)
    other_informations = attr.ib(type=str, default=None)
    other_informations_en = attr.ib(type=str, default=None)
    online_resources = attr.ib(type=str, default=None)
    online_resources_en = attr.ib(type=str, default=None)
    bibliography = attr.ib(type=str, default=None)
    mobility = attr.ib(type=str, default=None)
    last_update = attr.ib(type=datetime.datetime, default=None)
    author = attr.ib(type=str, default=None)


@attr.s(slots=True)
class DescriptionFicheForceMajeure:
    teaching_methods = attr.ib(type=str, default=None)
    teaching_methods_en = attr.ib(type=str, default=None)
    evaluation_methods = attr.ib(type=str, default=None)
    evaluation_methods_en = attr.ib(type=str, default=None)
    other_informations = attr.ib(type=str, default=None)
    other_informations_en = attr.ib(type=str, default=None)
    last_update = attr.ib(type=datetime.datetime, default=None)
    author = attr.ib(type=str, default=None)
