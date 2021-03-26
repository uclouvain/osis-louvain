import rules
from django.utils.translation import gettext_lazy as _

from learning_unit.auth import predicates
from osis_role.contrib import admin as osis_role_admin
from osis_role.contrib import models as osis_role_models


class CentralManagerAdmin(osis_role_admin.EntityRoleModelAdmin):
    list_display = osis_role_admin.EntityRoleModelAdmin.list_display


class CentralManager(osis_role_models.EntityRoleModel):
    class Meta:
        default_related_name = 'learning_unit'
        verbose_name = _("Central manager")
        verbose_name_plural = _("Central managers")
        group_name = "central_managers_for_ue"

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({
            'base.can_access_catalog': rules.always_allow,
            'base.view_educationgroup': rules.always_allow,
            'base.can_create_learningunit': predicates.is_learning_unit_edition_for_central_manager_period_open,
            'base.can_create_partim':
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_learning_unit_year_full &
                predicates.is_external_learning_unit_with_cograduation,
            'base.can_access_learningunit': rules.always_allow,
            'base.can_access_externallearningunityear': rules.always_allow,
            'base.can_delete_learningunit':
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_learning_unit_start_year_after_year_limit &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.has_learning_unit_prerequisite_dependencies &
                predicates.has_learning_unit_no_application_all_years,
            'base.can_edit_learningunit':
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_learning_unit_year_older_or_equals_than_limit_settings_year &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_external_learning_unit_with_cograduation &
                predicates.is_not_in_proposal_state_for_this_and_previous_years,
            'base.add_externallearningunityear': predicates.is_learning_unit_edition_for_central_manager_period_open,
            'base.can_propose_learningunit':
                predicates.is_learning_unit_year_not_in_past &
                predicates.is_learning_unit_year_not_a_partim &
                predicates.is_learning_unit_container_type_editable &
                predicates.is_not_in_proposal_state_any_year &
                predicates.is_proposal_extended_management_calendar_open &
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_external_learning_unit_with_cograduation,
            'base.can_propose_learningunit_end_date':
                predicates.is_learning_unit_year_not_in_past &
                predicates.is_learning_unit_year_not_a_partim &
                predicates.is_learning_unit_container_type_editable &
                predicates.is_not_in_proposal_state_any_year &
                predicates.is_proposal_extended_management_calendar_open &
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_external_learning_unit_with_cograduation,
            'base.can_edit_learning_unit_proposal':
                predicates.is_in_proposal_state &
                predicates.is_year_in_proposal_state &
                predicates.is_proposal_extended_management_calendar_open &
                (predicates.is_user_attached_to_current_requirement_entity |
                 predicates.is_user_attached_to_requirement_entity),
            'base.can_edit_learning_unit_proposal_date':
                predicates.is_in_proposal_state &
                predicates.is_year_in_proposal_state &
                predicates.is_proposal_extended_management_calendar_open &
                (predicates.is_user_attached_to_current_requirement_entity |
                 predicates.is_user_attached_to_requirement_entity),
            'base.can_cancel_proposal':
                predicates.is_in_proposal_state &
                predicates.is_year_in_proposal_state &
                (predicates.is_not_proposal_of_type_creation |
                 (
                     predicates.has_learning_unit_no_application_this_year &
                     predicates.has_learning_unit_no_attribution_this_year
                 )
                 ) &
                (predicates.is_user_attached_to_current_requirement_entity |
                 predicates.is_user_attached_to_requirement_entity) &
                predicates.is_external_learning_unit_with_cograduation,
            'base.can_edit_learningunit_date':
                predicates.is_learning_unit_year_older_or_equals_than_limit_settings_year &
                predicates.has_learning_unit_no_application_in_future &
                predicates.has_learning_unit_no_attribution_in_future &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_external_learning_unit_with_cograduation &
                predicates.is_not_in_proposal_state_for_this_and_previous_years,
            'base.can_edit_learningunit_pedagogy':
                predicates.is_learning_unit_year_older_or_equals_than_limit_settings_year &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_user_attached_to_current_requirement_entity,
            'base.can_edit_learningunit_specification':
                predicates.is_learning_unit_edition_for_central_manager_period_open,
            'base.can_consolidate_learningunit_proposal':
                predicates.is_in_proposal_state &
                predicates.is_year_in_proposal_state &
                predicates.is_proposal_in_state_to_be_consolidated &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                (predicates.is_user_attached_to_current_requirement_entity |
                 predicates.is_user_attached_to_requirement_entity) &
                (predicates.is_not_proposal_of_type_suppression |
                    (predicates.has_learning_unit_no_application_all_years &
                     predicates.has_learning_unit_no_attribution_this_year
                     )
                 ),
            'base.can_add_charge_repartition':
                predicates.is_learning_unit_year_a_partim &
                predicates.is_user_attached_to_current_requirement_entity,
            'base.can_change_attribution':
                predicates.is_learning_unit_type_allowed_for_attributions &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_user_attached_to_current_requirement_entity,
            'base.can_delete_attribution':
                (predicates.is_learning_unit_year_a_partim |
                 predicates.is_learning_unit_type_allowed_for_attributions) &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_user_attached_to_current_requirement_entity,
            'base.can_edit_summary_locked_field':
                # to be verified (may be add failed message)
                rules.always_deny,
            'base.can_update_learning_achievement':
                predicates.is_user_attached_to_current_requirement_entity &
                predicates.is_learning_unit_edition_for_central_manager_period_open &
                predicates.is_learning_unit_year_older_or_equals_than_limit_settings_year,
            'base.can_refuse_learning_unit_proposal':
                predicates.is_in_proposal_state &
                predicates.is_year_in_proposal_state &
                (predicates.is_user_attached_to_current_requirement_entity |
                 predicates.is_user_attached_to_requirement_entity) &
                (predicates.is_not_proposal_of_type_creation |
                    (predicates.has_learning_unit_no_attribution_this_year &
                     predicates.has_learning_unit_no_application_this_year)
                 ),
        })
