import rules
from django.utils.translation import gettext_lazy as _

from osis_role.contrib import models as osis_role_models
from osis_role.contrib import admin as osis_role_admin


class StudentWorkerAdmin(osis_role_admin.RoleModelAdmin):
    list_display = osis_role_admin.RoleModelAdmin.list_display


class StudentWorker(osis_role_models.RoleModel):
    class Meta:
        verbose_name = _("Student worker")
        verbose_name_plural = _("Student workers")
        group_name = "student_update_UE_AA"

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({
            'base.can_access_catalog': rules.always_allow,
            'base.can_access_learningunit': rules.always_allow,
            'base.can_edit_learningunit_pedagogy': rules.always_allow,
            'base.can_edit_learningunit_specification': rules.always_allow
        })
