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
from ajax_select import register, LookupChannel
from ajax_select.fields import AutoCompleteSelectMultipleField
from django.utils.translation import ugettext_lazy as _

from base.forms.education_group.common import CommonBaseForm, EducationGroupModelForm, \
    MainEntitiesVersionChoiceField, EducationGroupYearModelForm
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.entity_version import get_last_version
from base.models.enums import education_group_categories
from reference.models.domain import Domain


class TrainingEducationGroupYearForm(EducationGroupYearModelForm):
    category = education_group_categories.TRAINING

    domains = AutoCompleteSelectMultipleField(
        'domains', required=False, help_text="", label=_('studies_domain')
    )

    class Meta(EducationGroupYearModelForm.Meta):
        fields = ["acronym", "partial_acronym", "education_group_type", "title", "title_english",
                  "academic_year", "main_teaching_campus", "remark", "remark_english", "credits", "enrollment_enabled",
                  "partial_deliberation", "academic_type", "admission_exam",
                  "university_certificate", "duration", "duration_unit", "dissertation",
                  "internship", "primary_language", "other_language_activities",
                  "keywords", "active", "schedule_type", "enrollment_campus",
                  "other_campus_activities", "funding", "funding_direction", "funding_cud",
                  "funding_direction_cud",
                  "diploma_printing_title", "diploma_printing_orientation", "professional_title", "min_credits",
                  "max_credits", "administration_entity", "management_entity", "domains"]

        field_classes = {
            **EducationGroupYearModelForm.Meta.field_classes, **{"management_entity": MainEntitiesVersionChoiceField}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["domains"].widget.attrs['placeholder'] = _('Enter text to search')

        if getattr(self.instance, 'management_entity', None):
            self.initial['management_entity'] = get_last_version(self.instance.management_entity).pk

    def save(self, commit=True):
        education_group_year = super().save(commit=False)
        education_group_year.save()

        self.save_domains()

        return education_group_year

    def save_domains(self):
        self.instance.domains.clear()
        # Save_m2m can not be used because the many_to_many use a through parameter
        for domain_id in self.cleaned_data["domains"]:
            EducationGroupYearDomain.objects.get_or_create(
                education_group_year=self.instance,
                domain_id=domain_id)


class TrainingForm(CommonBaseForm):

    def __init__(self, data, instance=None, parent=None):
        education_group_year_form = TrainingEducationGroupYearForm(data, instance=instance, parent=parent)
        education_group = instance.education_group if instance else None
        education_group_form = EducationGroupModelForm(data, instance=education_group)
        super().__init__(education_group_year_form, education_group_form)


@register('domains')
class DomainsLookup(LookupChannel):

    model = Domain

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)

    def format_item_display(self, item):
        return u"<span class='tag'>%s</span>" % item.name
