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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import string
from datetime import datetime

import factory.fuzzy
from dateutil.relativedelta import relativedelta

from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION, TRANSITION_PREFIX

CEMS = 'CEMS'


class EducationGroupVersionFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'program_management.EducationGroupVersion'
        django_get_or_create = ('version_name', 'offer', 'transition_name')

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.today() - relativedelta(years=1), datetime.today())

    transition_name = NOT_A_TRANSITION
    version_name = factory.Sequence(lambda n: 'VERSION%d' % n)
    root_group = factory.SubFactory(GroupYearFactory)
    offer = factory.SubFactory(
        EducationGroupYearFactory,
        partial_acronym=factory.SelfAttribute('..root_group.partial_acronym'),
        acronym=factory.SelfAttribute('..root_group.acronym'),
        academic_year=factory.SelfAttribute('..root_group.academic_year'),
        education_group_type=factory.SelfAttribute('..root_group.education_group_type')
    )
    title_fr = factory.fuzzy.FuzzyText(length=15)
    title_en = factory.fuzzy.FuzzyText(length=15)


class StandardEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = ''


class StandardTransitionEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = ''
    transition_name = TRANSITION_PREFIX


class ParticularTransitionEducationGroupVersionFactory(EducationGroupVersionFactory):
    version_name = CEMS
    transition_name = TRANSITION_PREFIX


def create_with_version(version_offer=None, **kwargs):
    group_yr = GroupYearFactory(**kwargs)
    if version_offer:
        EducationGroupVersionFactory(offer=version_offer, root_group=group_yr)
    return group_yr
