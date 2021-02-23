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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import functools

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics

from base.business.education_groups import general_information_sections
from education_group.ddd import command
from education_group.ddd.service.read import get_group_service
from education_group.models.group_year import GroupYear
from osis_common.utils.models import get_object_or_none
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.models.education_group_version import EducationGroupVersion
from webservices.api.serializers.general_information import GeneralInformationSerializer


class GeneralInformation(generics.RetrieveAPIView):
    """
        Return the general informations for an Education Group Year
    """
    name = 'generalinformations_read'
    serializer_class = GeneralInformationSerializer

    def get_object(self):
        group = self.get_group()
        identity = ProgramTreeIdentity(code=group.code, year=group.year)
        tree = ProgramTreeRepository.get(entity_id=identity)
        return tree.root_node

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        serializer_context['language'] = self.kwargs['language']
        serializer_context['acronym'] = self.kwargs['acronym']
        serializer_context['offer'] = self.get_offer()
        serializer_context['group'] = self.get_group()
        return serializer_context

    @functools.lru_cache()
    def get_education_group_version(self):
        return get_object_or_none(
            EducationGroupVersion.standard.select_related(
                'offer__academic_year',
                'offer__admissioncondition',
                'offer__education_group_type',
                'root_group__academic_year'
            ).prefetch_related(
                'offer__educationgrouppublicationcontact_set',
                'offer__educationgroupachievement_set',
                'offer__management_entity__entityversion_set',
                'offer__publication_contact_entity__entityversion_set'
            ),
            Q(offer__acronym__iexact=self.kwargs['acronym']) |
            Q(root_group__partial_acronym__iexact=self.kwargs['acronym']),
            offer__academic_year__year=self.kwargs['year'],
            offer__education_group_type__name__in=general_information_sections.SECTIONS_PER_OFFER_TYPE.keys(),
            transition_name=NOT_A_TRANSITION
        )

    def get_group_db(self):
        version = self.get_education_group_version()
        if version:
            return version.root_group
        return get_object_or_404(
            GroupYear.objects.select_related('education_group_type', 'academic_year'),
            partial_acronym__iexact=self.kwargs['acronym'],
            academic_year__year=self.kwargs['year'],
            education_group_type__name__in=general_information_sections.SECTIONS_PER_OFFER_TYPE.keys(),
        )

    @functools.lru_cache()
    def get_group(self) -> 'Group':
        group_db = self.get_group_db()
        get_group_cmd = command.GetGroupCommand(code=group_db.partial_acronym, year=group_db.academic_year.year)
        return get_group_service.get_group(get_group_cmd)

    def get_offer(self):
        version = self.get_education_group_version()
        return version.offer
