##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

import rules
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.auth.predicates import is_linked_to_offer, is_scores_responsible_period_opened
from base.models.academic_year import current_academic_year
from base.models.education_group import EducationGroup
from base.models.entity import Entity
from base.models.entity_version import find_parent_of_type_into_entity_structure, EntityVersion
from base.models.enums.entity_type import FACULTY
from base.models.learning_unit_enrollment import LearningUnitEnrollment
from education_group.auth.predicates import is_education_group_extended_daily_management_calendar_open
from education_group.contrib.admin import EducationGroupRoleModelAdmin
from education_group.contrib.models import EducationGroupRoleModel
from osis_role.contrib import predicates as osis_role_predicates


class ProgramManagerAdmin(VersionAdmin, EducationGroupRoleModelAdmin):
    list_display = ('person', 'education_group_most_recent_acronym', 'changed',)
    raw_id_fields = ('person', 'education_group')
    search_fields = ('education_group__educationgroupyear__acronym', 'person__first_name', 'person__last_name')


class ProgramManager(EducationGroupRoleModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    person = models.ForeignKey('Person', on_delete=models.PROTECT, verbose_name=gettext_lazy("person"))
    education_group = models.ForeignKey(EducationGroup, on_delete=models.CASCADE)
    is_main = models.BooleanField(default=False, verbose_name=gettext_lazy('Main'))

    @property
    def name(self):
        return self.__str__()

    @property
    def education_group_most_recent_acronym(self):
        return self.education_group.most_recent_acronym

    def __str__(self):
        return "{} - {}".format(self.person, self.education_group)

    class Meta:
        verbose_name = _("Program manager")
        verbose_name_plural = _("Program managers")
        group_name = "program_managers"
        unique_together = ('person', 'education_group',)

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({
            'assessments.can_access_scoreencoding': rules.always_allow,
            'assessments.change_scoresresponsible': is_scores_responsible_period_opened,
            'assessments.view_scoresresponsible': is_scores_responsible_period_opened,
            'base.can_access_catalog': rules.always_allow,
            'base.can_access_evaluation': rules.always_allow,
            'base.can_access_externallearningunityear': rules.always_allow,
            'base.can_access_learningunit': rules.always_allow,
            'base.can_access_offer': rules.always_allow,
            'base.can_access_education_group': rules.always_allow,
            'base.can_access_student_path': rules.always_allow,
            'base.can_attach_node': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a link")
            ),
            'base.can_detach_node': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a link")
            ),
            'base.change_group': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a group")
            ),
            'base.change_link_data': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a link")
            ),
            'base.change_training':
                is_linked_to_offer &
                is_education_group_extended_daily_management_calendar_open,
            'base.change_minitraining': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a minitraining")
            ),
            'base.change_educationgroupcertificateaim': is_linked_to_offer,
            'base.is_institution_administrator': rules.always_allow,
            'base.view_educationgroup': rules.always_allow,
            'program_management.change_training_version': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a specific version")
            ),
            'program_management.change_minitraining_version': osis_role_predicates.always_deny(
                message=_("Program manager is not allowed to modify a specific version")
            ),
            'base.view_publish_btn': rules.always_deny,
        })


def find_by_person(a_person):
    return ProgramManager.objects.filter(person=a_person).select_related(
        'education_group', 'person',
    )


def is_program_manager(user, learning_unit_year=None, education_group=None):
    """
    Args:
        user: an instance of auth.User
        learning_unit_year: an annual learning unit to check whether it is in the managed offers of the user.
        education_group: an annual offer to check whether the user is its program manager.

    Returns: True if the user manage an offer. False otherwise.
    """
    if user.has_perm('base.is_administrator'):
        return True
    elif learning_unit_year:
        offers_user = ProgramManager.objects.filter(person__user=user).values('education_group_id', flat=True)
        result = LearningUnitEnrollment.objects.filter(learning_unit_year=learning_unit_year) \
            .filter(offer_enrollment__education_group_year__education_group_id__in=offers_user).exists()
    elif education_group:
        result = ProgramManager.objects.filter(person__user=user, education_group=education_group).exists()
    else:
        result = ProgramManager.objects.filter(person__user=user).exists()

    return result


def find_by_management_entity(administration_entities: List['EntityVersion']):
    if administration_entities:
        return ProgramManager.objects.filter(
            education_group__educationgroupyear__management_entity__in=[ev.entity for ev in administration_entities]
        ).select_related(
            'person'
        ).order_by(
            'person__last_name',
            'person__first_name'
        ).distinct(
            'person__last_name',
            'person__first_name',
        )

    return None


def get_learning_unit_years_attached_to_program_managers(programs_manager_qs, entity_structure):
    current_ac = current_academic_year()
    allowed_entities_scopes = set()

    offer_enrollments_education_group_year = LearningUnitEnrollment.objects.filter(
        offer_enrollment__education_group_year__academic_year=current_ac,
        offer_enrollment__education_group_year__education_group__in=programs_manager_qs.values_list(
            'education_group',
            flat=True
        )
    ).distinct(
        'offer_enrollment__education_group_year'
    ).prefetch_related(
        Prefetch(
            'offer_enrollment__education_group_year__administration_entity',
            queryset=Entity.objects.all().prefetch_related('entityversion_set')
        )
    )
    lu_enrollments = LearningUnitEnrollment.objects.filter(
        offer_enrollment__education_group_year__academic_year=current_ac,
        offer_enrollment__education_group_year__education_group__in=programs_manager_qs.values_list(
            'education_group',
            flat=True
        )
    ).distinct(
        'learning_unit_year'
    ).prefetch_related(
        Prefetch(
            'offer_enrollment__education_group_year__administration_entity',
            queryset=Entity.objects.all().prefetch_related('entityversion_set')
        )
    )

    for learning_unit_enrollment in offer_enrollments_education_group_year:
        education_group_year = learning_unit_enrollment.offer_enrollment.education_group_year
        administration_fac_level = find_parent_of_type_into_entity_structure(
           education_group_year.administration_entity_version,
           entity_structure,
           FACULTY
        )
        if not administration_fac_level:
            administration_fac_level = education_group_year.administration_entity

        allowed_entities_scopes.add(administration_fac_level.pk)
        allowed_entities_scopes = allowed_entities_scopes.union({
            entity_version.entity_id for entity_version in
            entity_structure[administration_fac_level.pk].get('all_children', [])
        })

    return lu_enrollments.filter(
        learning_unit_year__learning_container_year__requirement_entity__in=allowed_entities_scopes
    ).values_list('learning_unit_year__id', flat=True)
