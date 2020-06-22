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
import operator

import factory
from factory.django import DjangoModelFactory

from base.models.enums import education_group_categories, education_group_types


def _external_id_generator(obj):
    return "osis.education_group_type_{education_group_type}".format(
        education_group_type=obj.name.lower().replace("_", "")
    )


def _is_learning_unit_child_allowed(obj):
    types_for_which_learning_unit_child_is_allowed = (
        education_group_types.GroupType.COMMON_CORE.name,
        education_group_types.GroupType.COMPLEMENTARY_MODULE.name,
        education_group_types.GroupType.SUB_GROUP.name
    )
    return obj.name in types_for_which_learning_unit_child_is_allowed


class EducationGroupTypeFactory(DjangoModelFactory):
    class Meta:
        model = "base.EducationGroupType"
        django_get_or_create = ('name',)

    external_id = factory.lazy_attribute(_external_id_generator)
    category = education_group_categories.TRAINING
    name = factory.Iterator(education_group_types.TrainingType.choices(), getter=operator.itemgetter(0))
    learning_unit_child_allowed = factory.lazy_attribute(_is_learning_unit_child_allowed)

    class Params:
        minitraining = factory.Trait(
            category=education_group_categories.MINI_TRAINING,
            name=factory.Iterator(education_group_types.MiniTrainingType.choices(), getter=operator.itemgetter(0))
        )

        group = factory.Trait(
            category=education_group_categories.GROUP,
            name=factory.Iterator(education_group_types.GroupType.choices(), getter=operator.itemgetter(0))
        )


class TrainingEducationGroupTypeFactory(EducationGroupTypeFactory):
    pass


class MiniTrainingEducationGroupTypeFactory(EducationGroupTypeFactory):
    minitraining = True


class GroupEducationGroupTypeFactory(EducationGroupTypeFactory):
    group = True
