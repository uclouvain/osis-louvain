##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base.models import entity_version
from base.models.entity import Entity
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.utils.utils import get_object_or_none
from osis_common.models.osis_model_admin import OsisModelAdmin


class ProposalLearningUnitAdmin(OsisModelAdmin):
    list_display = ('learning_unit_year', 'folder_id', 'entity', 'type', 'state')

    search_fields = ['folder_id', 'learning_unit_year__acronym']
    list_filter = ('type', 'state')
    raw_id_fields = ('learning_unit_year', 'author', 'entity')


class ProposalLearningUnit(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    author = models.ForeignKey('Person', null=True)
    date = models.DateTimeField(auto_now=True)
    learning_unit_year = models.OneToOneField('LearningUnitYear')
    type = models.CharField(
        max_length=50,
        choices=ProposalType.choices(),
        verbose_name=_("Type"),
        default=ProposalType.MODIFICATION.name
    )

    state = models.CharField(
        max_length=50,
        choices=ProposalState.choices(),
        verbose_name=_("State"),
        default=ProposalState.FACULTY.name
    )

    initial_data = JSONField(default={})
    entity = models.ForeignKey('Entity')
    folder_id = models.PositiveIntegerField()

    class Meta:
        permissions = (
            # TODO: Remove this permissions : already exists with can_change_proposal_learning_unit
            ("can_edit_learning_unit_proposal", "Can edit learning unit proposal"),
        )

    def __str__(self):
        return "{} - {}".format(self.folder_id, self.learning_unit_year)

    @property
    def folder(self):
        last_entity = entity_version.get_last_version(self.entity)
        return "{}{}".format(last_entity.acronym if last_entity else '', str(self.folder_id))


def find_by_learning_unit_year(a_learning_unit_year):
    return get_object_or_none(ProposalLearningUnit, learning_unit_year=a_learning_unit_year)


def find_by_learning_unit(a_learning_unit):
    return get_object_or_none(ProposalLearningUnit, learning_unit_year__learning_unit=a_learning_unit)


def filter_proposal_fields(queryset, **kwargs):
    """ Filter of proposal search on a LearningUnitYearQueryset """

    entity_folder_id = kwargs.get('entity_folder_id')
    folder_id = kwargs.get('folder_id')
    proposal_type = kwargs.get('proposal_type')
    proposal_state = kwargs.get('proposal_state')

    if entity_folder_id:
        queryset = queryset.filter(proposallearningunit__entity_id=entity_folder_id)

    if folder_id:
        queryset = queryset.filter(proposallearningunit__folder_id=folder_id)

    if proposal_type:
        queryset = queryset.filter(proposallearningunit__type=proposal_type)

    if proposal_state:
        queryset = queryset.filter(proposallearningunit__state=proposal_state)

    return queryset


def find_distinct_folder_entities():
    return Entity.objects.filter(proposallearningunit__isnull=False).distinct()


def is_learning_unit_year_in_proposal(luy):
    return ProposalLearningUnit.objects.filter(learning_unit_year=luy).exists()


def is_learning_unit_in_proposal(lu):
    return ProposalLearningUnit.objects.filter(learning_unit_year__learning_unit=lu).exists()
