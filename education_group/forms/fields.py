from django import forms
from django.utils.translation import gettext_lazy as _

from base.models import campus
from osis_role.contrib.forms.fields import EntityRoleChoiceField

from base.models.entity_version import EntityVersion
from education_group.auth.roles.central_manager import CentralManager
from education_group.auth.roles.faculty_manager import FacultyManager


class MainCampusChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = campus.find_main_campuses()
        super().__init__(queryset,  *args, **kwargs)


class ManagementEntitiesChoiceField(EntityRoleChoiceField):
    def __init__(self, person, initial, **kwargs):
        group_names = (FacultyManager.group_name, CentralManager.group_name, )
        self.initial = initial
        super().__init__(
            person=person,
            group_names=group_names,
            label=_('Management entity'),
            **kwargs,
        )

    def get_queryset(self):
        qs = super().get_queryset().pedagogical_entities().order_by('acronym')
        if self.initial:
            qs |= EntityVersion.objects.filter(pk=self.initial)
        return qs

    def clean(self, value):
        if value is not None:
            return EntityVersion.objects.get(pk=value).acronym
        return value
