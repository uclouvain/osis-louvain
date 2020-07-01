import rules
from django.db import models
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from osis_common.models.serializable_model import SerializableModelAdmin
from osis_role.contrib import admin as osis_role_admin
from osis_role.contrib import models as osis_role_models


class EntityManagerAdmin(VersionAdmin, SerializableModelAdmin, osis_role_admin.EntityRoleModelAdmin):
    list_display = ('person', 'structure', 'entity')
    search_fields = ['person__first_name', 'person__last_name', 'structure__acronym']


class EntityManager(osis_role_models.EntityRoleModel):
    structure = models.ForeignKey('Structure', on_delete=models.CASCADE)
    with_child = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Entity manager")
        verbose_name_plural = _("Entity managers")
        group_name = "entity_managers"

    def __str__(self):
        return u"%s" % self.person

    @classmethod
    def rule_set(cls):
        return rules.RuleSet({
            "base.view_educationgroup": rules.always_allow,
            "assessments.change_scoresresponsible": rules.always_allow,
            "assessments.view_scoresresponsible": rules.always_allow,
            "base.change_programmanager": rules.always_allow,
            "base.view_programmanager": rules.always_allow,
            "base.can_access_catalog": rules.always_allow,
            "base.is_institution_administrator": rules.always_allow,
        })
