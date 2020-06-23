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

import factory.fuzzy

from learning_unit.ddd.domain.description_fiche import DescriptionFiche


class DescriptionFicheFactory(factory.Factory):

    class Meta:
        model = DescriptionFiche
        abstract = False

    resume = factory.fuzzy.FuzzyText(length=240)
    resume_en = factory.fuzzy.FuzzyText(length=240)
    teaching_methods = factory.fuzzy.FuzzyText(length=240)
    teaching_methods_en = factory.fuzzy.FuzzyText(length=240)
    evaluation_methods = factory.fuzzy.FuzzyText(length=240)
    evaluation_methods_en = factory.fuzzy.FuzzyText(length=240)
    other_informations = factory.fuzzy.FuzzyText(length=240)
    other_informations_en = factory.fuzzy.FuzzyText(length=240)
    online_resources = factory.fuzzy.FuzzyText(length=240)
    online_resources_en = factory.fuzzy.FuzzyText(length=240)
    bibliography = factory.fuzzy.FuzzyText(length=240)
    mobility = factory.fuzzy.FuzzyText(length=240)
