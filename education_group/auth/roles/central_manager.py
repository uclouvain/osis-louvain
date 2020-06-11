import rules
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from education_group.auth import predicates
from education_group.auth.roles.utils import EducationGroupTypeScopeRoleMixin
from education_group.auth.scope import Scope
from osis_role.contrib import admin as osis_role_admin
from osis_role.contrib import models as osis_role_models
from osis_role.contrib import predicates as osis_role_predicates


class CentralManagerAdmin(osis_role_admin.EntityRoleModelAdmin):
    list_display = osis_role_admin.EntityRoleModelAdmin.list_display + ('scopes', )


class CentralManager(EducationGroupTypeScopeRoleMixin, osis_role_models.EntityRoleModel):
    scopes = ArrayField(
        models.CharField(max_length=200, choices=Scope.choices()),
        blank=True,
    )

    class Meta:
        verbose_name = _("Central manager")
        verbose_name_plural = _("Central managers")
        group_name = "central_managers"

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({
            'base.can_access_catalog': rules.always_allow,  # Perms Backward compibility
            'base.view_educationgroup': rules.always_allow,
            'base.add_training':
                predicates.is_user_attached_to_management_entity &
                predicates.is_maximum_child_not_reached_for_training_category,
            'base.add_minitraining':
                predicates.is_user_attached_to_management_entity &
                predicates.is_maximum_child_not_reached_for_mini_training_category,
            'base.add_group':
                predicates.is_user_attached_to_management_entity &
                predicates.is_not_orphan_group &
                predicates.is_maximum_child_not_reached_for_group_category,
            # TODO : split in training, minitraining, group
            'base.change_educationgroup':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.delete_all_training':
                predicates.are_all_trainings_removable,
            'base.delete_all_minitraining':
                predicates.are_all_minitrainings_removable,
            'base.delete_all_group':
                predicates.are_all_groups_removable,
            'base.delete_training':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.delete_minitraining':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.delete_group':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.can_attach_node':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.can_detach_node':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_educationgroupcertificateaim':
                osis_role_predicates.always_deny(
                    message=_('Certificate aim can only be edited by program manager')
                ),
            'base.change_commonpedagogyinformation':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_pedagogyinformation':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_commonadmissioncondition':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_admissioncondition':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_educationgrouporganization':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.add_educationgroupachievement':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_educationgroupachievement':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.delete_educationgroupachievement':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.can_edit_education_group_administrative_data':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_education_group_type_authorized_according_to_user_scope,
            'base.change_link_data':
                predicates.is_education_group_year_older_or_equals_than_limit_settings_year &
                predicates.is_user_attached_to_management_entity,
        })
