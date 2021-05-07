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
import contextlib
import warnings
from typing import Optional, List

from django.db import IntegrityError
from django.db.models import F, Case, When, IntegerField, QuerySet
from django.db.models import Q

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from education_group.ddd.domain.exception import TrainingNotFoundException
from education_group.models.group import Group
from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from osis_common.ddd.interface import RootEntity
from program_management.ddd import command
from program_management.ddd.business_types import *
from program_management.ddd.domain import exception
from program_management.ddd.domain import program_tree
from program_management.ddd.domain import program_tree_version
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, STANDARD, NOT_A_TRANSITION
from program_management.ddd.repositories import program_tree as program_tree_repository
from program_management.models.education_group_version import EducationGroupVersion


class ProgramTreeVersionRepository(interface.AbstractRepository):
    @classmethod
    def save(cls, entity: RootEntity) -> None:
        raise NotImplementedError

    @classmethod
    def create(
            cls,
            program_tree_version: 'ProgramTreeVersion',
            **_
    ) -> 'ProgramTreeVersionIdentity':
        warnings.warn("DEPRECATED : use .save() function instead", DeprecationWarning, stacklevel=2)
        offer_acronym = program_tree_version.entity_id.offer_acronym
        year = program_tree_version.entity_id.year
        try:
            education_group_year_id = EducationGroupYear.objects.filter(
                acronym=offer_acronym,
                academic_year__year=year,
            ).values_list(
                'pk', flat=True
            )[0]
        except IndexError:
            raise TrainingNotFoundException(acronym=offer_acronym, year=year)

        group_year_id = GroupYear.objects.filter(
            partial_acronym=program_tree_version.program_tree_identity.code,
            academic_year__year=program_tree_version.program_tree_identity.year,
        ).values_list(
            'pk', flat=True
        )[0]

        try:
            educ_group_version = EducationGroupVersion.objects.create(
                version_name=program_tree_version.version_name,
                title_fr=program_tree_version.title_fr,
                title_en=program_tree_version.title_en,
                offer_id=education_group_year_id,
                transition_name=program_tree_version.entity_id.transition_name,
                root_group_id=group_year_id,
            )
            _update_start_year_and_end_year(
                educ_group_version,
                program_tree_version.start_year,
                program_tree_version.end_year_of_existence
            )
        except IntegrityError as ie:
            raise exception.ProgramTreeAlreadyExistsException
        return program_tree_version.entity_id

    @classmethod
    def update(cls, program_tree_version: 'ProgramTreeVersion', **_) -> 'ProgramTreeVersionIdentity':
        warnings.warn("DEPRECATED : use .save() function instead", DeprecationWarning, stacklevel=2)
        obj = EducationGroupVersion.objects.get(
            offer__acronym=program_tree_version.entity_identity.offer_acronym,
            offer__academic_year__year=program_tree_version.entity_identity.year,
            version_name=program_tree_version.entity_identity.version_name,
            transition_name=program_tree_version.entity_identity.transition_name,
        )
        obj.version_name = program_tree_version.version_name
        obj.title_fr = program_tree_version.title_fr
        obj.title_en = program_tree_version.title_en
        obj.save()

        _update_start_year_and_end_year(
            obj,
            program_tree_version.start_year,
            program_tree_version.end_year_of_existence
        )

        return program_tree_version.entity_id

    @classmethod
    def get(cls, entity_id: 'ProgramTreeVersionIdentity') -> 'ProgramTreeVersion':
        qs = _get_common_queryset().filter(
            version_name=entity_id.version_name,
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year=entity_id.year,
            transition_name=entity_id.transition_name,
        )
        try:
            return _instanciate_tree_version(qs.get())
        except EducationGroupVersion.DoesNotExist:
            raise exception.ProgramTreeVersionNotFoundException()

    @classmethod
    def get_last_in_past(cls, entity_id: 'ProgramTreeVersionIdentity') -> 'ProgramTreeVersion':
        qs = EducationGroupVersion.objects.filter(
            version_name=entity_id.version_name,
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year__lt=entity_id.year,
            transition_name=entity_id.transition_name
        ).order_by(
            'offer__academic_year'
        ).values_list(
            'offer__academic_year__year',
            flat=True,
        )
        if qs:
            last_past_year = qs.last()
            last_identity = ProgramTreeVersionIdentity(
                offer_acronym=entity_id.offer_acronym,
                year=last_past_year,
                version_name=entity_id.version_name,
                transition_name=entity_id.transition_name,
            )
            return cls.get(entity_id=last_identity)

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['ProgramTreeVersionIdentity']] = None,
            version_name: str = None,
            offer_acronym: str = None,
            transition_name: str = None,
            code: str = None,
            year: int = None,
            **kwargs
    ) -> List['ProgramTreeVersion']:
        qs = _get_common_queryset()
        if "element_ids" in kwargs:
            qs = qs.filter(root_group__element__in=kwargs['element_ids'])

        if version_name is not None:
            qs = qs.filter(version_name=version_name)
        if offer_acronym is not None:
            qs = qs.filter(offer__acronym=offer_acronym)
        if transition_name is not None:
            qs = qs.filter(transition_name=transition_name)
        if year is not None:
            qs = qs.filter(offer__academic_year__year=year)
        if code is not None:
            qs = qs.filter(root_group__partial_acronym=code)
        results = []
        for record_dict in qs:
            results.append(_instanciate_tree_version(record_dict))
        return results

    @classmethod
    def delete(
           cls,
           entity_id: 'ProgramTreeVersionIdentity',
           delete_program_tree_service: interface.ApplicationService = None
    ) -> None:
        program_tree_version = cls.get(entity_id)

        EducationGroupVersion.objects.filter(
            version_name=entity_id.version_name,
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year=entity_id.year,
            transition_name=entity_id.transition_name,
        ).delete()

        root_node = program_tree_version.get_tree().root_node
        cmd = command.DeleteProgramTreeCommand(code=root_node.code, year=root_node.year)
        delete_program_tree_service(cmd)

    @classmethod
    def search_all_versions_from_root_node(cls, root_node_identity: 'NodeIdentity') -> List['ProgramTreeVersion']:
        offer_ids = EducationGroupVersion.objects.filter(
            root_group__partial_acronym=root_node_identity.code,
            root_group__academic_year__year=root_node_identity.year
        ).values_list('offer_id', flat=True)

        return _search_versions_from_offer_ids(list(offer_ids))

    @classmethod
    def search_all_versions_from_root_nodes(cls, node_identities: List['NodeIdentity']) -> List['ProgramTreeVersion']:
        offer_ids = _search_by_node_entities(list(node_identities))
        return _search_versions_from_offer_ids(offer_ids)

    @classmethod
    def search_versions_from_trees(cls, trees: List['ProgramTree']) -> List['ProgramTreeVersion']:
        root_nodes_identities = [tree.root_node.entity_id for tree in trees]
        tree_versions = cls.search_all_versions_from_root_nodes(root_nodes_identities)

        result = []
        for tree_version in tree_versions:
            with contextlib.suppress(StopIteration):
                tree_version.tree = next(tree for tree in trees if tree.entity_id == tree_version.program_tree_identity)
                result.append(tree_version)
        return result


def _update_start_year_and_end_year(
        educ_group_version: EducationGroupVersion,
        start_year: int,
        end_year_of_existence: int
):
    # FIXME :: should add a field EducationgroupVersion.end_year
    # FIXME :: and should remove GroupYear.end_year
    # FIXME :: End_year is useful only for EducationGroupYear (training, minitraining) and programTreeVersions.
    # FIXME :: End year is not useful for Groups. For business, Group doesn't have a 'end date'.
    group = Group.objects.get(
        groupyear__educationgroupversion__pk=educ_group_version.pk
    )
    end_year_id = None
    if end_year_of_existence:
        end_year_id = AcademicYear.objects.only('pk').get(year=end_year_of_existence).pk
    group.end_year_id = end_year_id
    group.start_year_id = AcademicYear.objects.only('pk').get(year=start_year).pk
    group.save()


def _instanciate_tree_version(record_dict: dict) -> 'ProgramTreeVersion':
    identity = program_tree_version.ProgramTreeVersionIdentity(
        offer_acronym=record_dict['offer_acronym'],
        year=record_dict['offer_year'],
        version_name=record_dict['version_name'],
        transition_name=record_dict['transition_name'],
    )
    return program_tree_version.ProgramTreeVersion(
        entity_identity=identity,
        entity_id=identity,
        program_tree_identity=program_tree.ProgramTreeIdentity(record_dict['code'], record_dict['offer_year']),
        program_tree_repository=program_tree_repository.ProgramTreeRepository(),
        start_year=record_dict['start_year'],
        title_fr=record_dict['version_title_fr'],
        title_en=record_dict['version_title_en'],
        end_year_of_existence=record_dict['end_year_of_existence'],
    )


def _search_by_node_entities(entity_ids: List['NodeIdentity']) -> List[int]:
    if bool(entity_ids):

        qs = EducationGroupVersion.objects.all().values_list('offer_id', flat=True)

        filter_search_from = _build_where_clause(entity_ids[0])
        for identity in entity_ids[1:]:
            filter_search_from |= _build_where_clause(identity)
        qs = qs.filter(filter_search_from)
        return list(qs)
    return []


def _build_where_clause(node_identity: 'NodeIdentity') -> Q:
    return Q(
        Q(
            root_group__partial_acronym=node_identity.code,
            root_group__academic_year__year=node_identity.year
        )
    )


def _search_versions_from_offer_ids(offer_ids: List[int]) -> List['ProgramTreeVersion']:
    qs = _get_common_queryset()
    qs = qs.filter(
        offer_id__in=offer_ids,
    )
    results = []
    for record_dict in qs:
        results.append(_instanciate_tree_version(record_dict))
    return results


def _get_common_queryset() -> QuerySet:
    return EducationGroupVersion.objects.all().order_by(
        'version_name'
    ).annotate(
        code=F('root_group__partial_acronym'),
        offer_acronym=F('offer__acronym'),
        offer_year=F('offer__academic_year__year'),
        version_title_fr=F('title_fr'),
        version_title_en=F('title_en'),

        # FIXME :: should add a field EducationgroupVersion.end_year
        # FIXME :: and should remove GroupYear.end_year
        # FIXME :: End_year is useful only for EducationGroupYear (training, minitraining) and programTreeVersions.
        # FIXME :: End year is not useful for Groups. For business, Group doesn't have a 'end date'.
        end_year_of_existence=Case(
            When(
                Q(
                    offer__education_group_type__category__in={
                        Categories.TRAINING.name, Categories.MINI_TRAINING.name
                    }
                ) & Q(
                    version_name=STANDARD
                ) & Q(
                    transition_name=NOT_A_TRANSITION
                ),
                then=F('offer__education_group__end_year__year')
            ),
            default=F('root_group__group__end_year__year'),
            output_field=IntegerField(),
        ),
        start_year=Case(
            When(
                Q(
                    offer__education_group_type__category__in={
                        Categories.TRAINING.name, Categories.MINI_TRAINING.name
                    }
                ) & Q(
                    version_name=STANDARD
                ) & Q(
                    transition_name=NOT_A_TRANSITION
                ),
                then=F('offer__education_group__start_year__year')
            ),
            default=F('root_group__group__start_year__year'),
            output_field=IntegerField(),
        ),
    ).values(
        'code',
        'offer_acronym',
        'offer_year',
        'version_name',
        'version_title_fr',
        'version_title_en',
        'transition_name',
        'end_year_of_existence',
        'start_year',
    )
