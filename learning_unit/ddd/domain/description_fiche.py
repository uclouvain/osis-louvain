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


class DescriptionFiche:

    def __init__(
            self,
            resume: str = None,
            resume_en: str = None,
            teaching_methods: str = None,
            teaching_methods_en: str = None,
            evaluation_methods: str = None,
            evaluation_methods_en: str = None,
            other_informations: str = None,
            other_informations_en: str = None,
            online_resources: str = None,
            online_resources_en: str = None,
            bibliography: str = None,
            mobility: str = None,
    ):
        self.resume = resume
        self.resume_en = resume_en
        self.teaching_methods = teaching_methods
        self.teaching_methods_en = teaching_methods_en
        self.evaluation_methods = evaluation_methods
        self.evaluation_methods_en = evaluation_methods_en
        self.other_informations = other_informations
        self.other_informations_en = other_informations_en
        self.online_resources = online_resources
        self.online_resources_en = online_resources_en
        self.bibliography = bibliography
        self.mobility = mobility
