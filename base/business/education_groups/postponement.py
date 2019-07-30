# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django import forms
from django.db import Error
from django.utils.translation import ugettext as _

from base.business.education_groups import create
from base.business.utils.model import model_to_dict_fk, compare_objects, update_object
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.hops import Hops

EDUCATION_GROUP_MAX_POSTPONE_YEARS = 6
FIELD_TO_EXCLUDE = ['id', 'uuid', 'external_id', 'academic_year', 'linked_with_epc', 'publication_contact_entity']
HOPS_FIELDS = ('ares_study', 'ares_graca', 'ares_ability')


class ConsistencyError(Error):
    def __init__(self, last_instance_updated, differences, *args, **kwargs):
        self.last_instance_updated = last_instance_updated
        self.differences = differences
        super().__init__(*args, **kwargs)


def _compute_end_year(education_group):
    """
        This function compute the end year that the postponement must achieve
        :arg education_group: The education group that we want to postpone
    """

    # Compute max postponement based on config EDUCATION_GROUP_MAX_POSTPONE_YEARS
    max_postponement_end_year = starting_academic_year().year + EDUCATION_GROUP_MAX_POSTPONE_YEARS

    if education_group.end_year:
        # Get the min [Prevent education_group.end_year > academic_year.year provided by system]
        max_postponement_end_year = min(max_postponement_end_year, education_group.end_year)

    # Lookup on database, get the latest existing education group year [Prevent desync end_date and data]
    latest_egy = education_group.educationgroupyear_set.select_related('academic_year') \
        .order_by('academic_year__year').last()

    return max(max_postponement_end_year, latest_egy.academic_year.year)


def _postpone_m2m(education_group_year, postponed_egy, hops_values):
    fields_to_exclude = []

    opts = education_group_year._meta
    for f in opts.many_to_many:
        if f.name in fields_to_exclude:
            continue
        m2m_cls = f.remote_field.through

        # Remove records of postponed_egy
        m2m_cls.objects.all().filter(education_group_year=postponed_egy).delete()

        # Recreate records
        for m2m_obj in m2m_cls.objects.all().filter(education_group_year_id=education_group_year):
            m2m_data_to_postpone = model_to_dict_fk(m2m_obj, exclude=['id', 'external_id', 'education_group_year'])
            m2m_cls(education_group_year=postponed_egy, **m2m_data_to_postpone).save()

    if hops_values and any(elem in HOPS_FIELDS and hops_values[elem] for elem in hops_values):
        _postpone_hops(hops_values, postponed_egy)


def duplicate_education_group_year(old_education_group_year, new_academic_year, dict_initial_egy=None,
                                   hops_values=None):
    dict_new_value = model_to_dict_fk(old_education_group_year, exclude=FIELD_TO_EXCLUDE)

    defaults_values = {x: v for x, v in dict_new_value.items() if not isinstance(v, list)}

    postponed_egy, created = EducationGroupYear.objects.get_or_create(
        education_group=old_education_group_year.education_group,
        academic_year=new_academic_year,
        # Create object without m2m relations
        defaults=defaults_values
    )

    # During create of new postponed object, we need to update only the m2m relations
    if created:
        # Postpone the m2m [languages / secondary_domains]
        _postpone_m2m(old_education_group_year, postponed_egy, hops_values)

    # During the update, we need to check if the postponed object has been modify
    else:
        dict_postponed_egy = model_to_dict_fk(postponed_egy, exclude=FIELD_TO_EXCLUDE)
        differences = compare_objects(dict_initial_egy, dict_postponed_egy) \
            if dict_initial_egy and dict_postponed_egy else {}

        if differences:
            raise ConsistencyError(postponed_egy, differences)

        update_object(postponed_egy, dict_new_value)
        # Postpone the m2m [languages / secondary_domains]
        _postpone_m2m(old_education_group_year, postponed_egy, hops_values)

    return postponed_egy


def _postpone_hops(hops_values, postponed_egy):
    Hops.objects.update_or_create(education_group_year=postponed_egy,
                                  defaults={'ares_study': hops_values['ares_study'],
                                            'ares_graca': hops_values['ares_graca'],
                                            'ares_ability': hops_values['ares_ability']})


class PostponementEducationGroupYearMixin:
    """
    This mixin will report the modification to the futures years.

    If one of the future year is already modified, it will stop the postponement and append a warning message
    """
    field_to_exclude = FIELD_TO_EXCLUDE
    dict_initial_egy = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.postpone_start_year = None
        self.postpone_end_year = None
        # The list will not include the current instance of education group year
        self.education_group_year_postponed = []
        self.postponement_errors = {}
        self.warnings = []

        if not self._is_creation():
            self.dict_initial_egy = model_to_dict_fk(
                self.forms[forms.ModelForm].instance, exclude=self.field_to_exclude
            )

    def save(self):
        education_group_year = super().save()

        self.postpone_start_year = education_group_year.academic_year.year
        self.postpone_end_year = _compute_end_year(education_group_year.education_group)
        self._start_postponement(education_group_year)

        create.create_initial_group_element_year_structure(self.education_group_year_postponed)
        return education_group_year

    def _start_postponement(self, education_group_year):
        for academic_year in AcademicYear.objects.filter(year__gt=self.postpone_start_year,
                                                         year__lte=self.postpone_end_year):
            try:
                # hops is not relevant for a mini-training
                if education_group_year.is_mini_training():
                    postponed_egy = duplicate_education_group_year(
                        education_group_year, academic_year, self.dict_initial_egy
                    )
                else:
                    postponed_egy = duplicate_education_group_year(
                        education_group_year, academic_year, self.dict_initial_egy, self.hops_form.data
                    )
                self.education_group_year_postponed.append(postponed_egy)

            except ConsistencyError as e:
                self.add_postponement_errors(e)

            finally:
                education_group_year = EducationGroupYear.objects.get(
                    academic_year=academic_year,
                    education_group=education_group_year.education_group
                )

    def add_postponement_errors(self, consistency_error):
        for difference in consistency_error.differences:
            error = _("%(col_name)s has been already modified.") % {
                "col_name": _(EducationGroupYear._meta.get_field(difference).verbose_name).title(),
            }

            self.warnings.append(
                _("Consistency error in %(academic_year)s : %(error)s") % {
                    'academic_year': consistency_error.last_instance_updated.academic_year,
                    'error': error
                }
            )
