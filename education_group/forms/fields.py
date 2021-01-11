from ajax_select.fields import AutoCompleteSelectMultipleField
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from base.forms.learning_unit.entity_form import EntitiesVersionChoiceField
from base.models import campus
from base.models.entity_version import EntityVersion, find_pedagogical_entities_version
from education_group.auth.roles.central_manager import CentralManager
from education_group.auth.roles.faculty_manager import FacultyManager
from osis_role.contrib.forms.fields import EntityRoleModelChoiceField
from reference.models import domain


class MainCampusChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = campus.find_main_campuses()
        super().__init__(queryset,  *args, **kwargs)


class ManagementEntitiesModelChoiceField(EntityRoleModelChoiceField):
    def __init__(self, person, initial, **kwargs):
        group_names = (FacultyManager.group_name, CentralManager.group_name, )
        self.initial = initial
        super().__init__(
            person=person,
            group_names=group_names,
            label=_('Management entity'),
            to_field_name="acronym",
            **kwargs,
        )

    def get_queryset(self):
        qs = super().get_queryset().pedagogical_entities().order_by('acronym')
        if self.initial:
            date = timezone.now()
            qs |= EntityVersion.objects.current(date).filter(acronym=self.initial)
        return qs

    def clean(self, value):
        value = super(forms.ModelChoiceField, self).clean(value)
        if value:
            return value.acronym
        return None


class MainEntitiesVersionChoiceField(EntitiesVersionChoiceField):
    def __init__(self, queryset, *args, **kwargs):
        queryset = find_pedagogical_entities_version()
        super(MainEntitiesVersionChoiceField, self).__init__(queryset, *args, **kwargs)


class CreditField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        super().__init__(min_value=0, max_value=999, label=_("Credits"), **kwargs)


class SecondaryDomainsField(AutoCompleteSelectMultipleField):
    def clean(self, value):
        value = super().clean(value)
        return domain.Domain.objects.filter(pk__in=value)


class UpperCaseCharField(forms.CharField):
    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs['style'] = "text-transform: uppercase;"
        return attrs

    def to_python(self, value):
        value = super(UpperCaseCharField, self).to_python(value)
        if value:
            value = value.upper()
        return value
