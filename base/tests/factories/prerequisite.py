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
import datetime
import string

import factory.fuzzy
from factory import post_generation

from base.models.enums import prerequisite_operator
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory, LearningUnitYearFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class PrerequisiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.Prerequisite"
        django_get_or_create = ('learning_unit_year', 'education_group_year', 'education_group_version')

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1), datetime.datetime(2017, 3, 1))
    learning_unit_year = factory.SubFactory(LearningUnitYearFactory)
    education_group_year = factory.SubFactory(EducationGroupYearFactory)
    main_operator = prerequisite_operator.AND
    education_group_version = factory.SubFactory(EducationGroupVersionFactory)

    @post_generation
    def items(obj, create, extracted, groups=None, **kwargs):
        """
        Generate PrerequisiteItems for to this Prerequisite based on the argument groups.
        :param groups: A tuple of tuples of LearningUnitYear. Ex: ((LSINF1101,), (LOSIS1254, LOSIS2569))
                       Each tuple contained corresponds to a different group.
        """
        if groups is None:
            groups = tuple()

        for index, group in enumerate(groups):
            for group_index, luy in enumerate(group):
                PrerequisiteItemFactory(
                    learning_unit=luy.learning_unit,
                    prerequisite=obj,
                    group_number=index+1,
                    position=group_index+1
                )
