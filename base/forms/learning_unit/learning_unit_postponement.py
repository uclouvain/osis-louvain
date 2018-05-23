##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import OrderedDict

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create_2 import PartimForm, FullForm
from base.models import academic_year, learning_unit_year
from base.models.enums import learning_unit_year_subtypes, entity_container_year_link_type
from base.models.learning_unit import LearningUnit

FIELDS_TO_NOT_CHECK = ['academic_year']


# @TODO: Use LearningUnitPostponementForm to manage END_DATE of learning unit year
# TODO :: Maybe could we move this code to LearningUnitModelForm class?
class LearningUnitPostponementForm:
    learning_unit_instance = None
    subtype = None
    person = None
    check_consistency = True
    _forms_to_upsert = []
    _forms_to_delete = []
    _warnings = None
    consistency_errors = OrderedDict()
    _luy_upserted = []

    def __init__(self, person, start_postponement, end_postponement=None, learning_unit_instance=None,
                 learning_unit_full_instance=None, data=None, check_consistency=True):
        if learning_unit_instance and not isinstance(learning_unit_instance, LearningUnit):
            raise AttributeError('learning_unit_instance arg should be an instance of {}'.format(LearningUnit))
        if learning_unit_full_instance and not isinstance(learning_unit_full_instance, LearningUnit):
            raise AttributeError('learning_unit_full_instance arg should be an instance of {}'.format(LearningUnit))

        self.learning_unit_instance = learning_unit_instance
        self.learning_unit_full_instance = learning_unit_full_instance
        self.subtype = learning_unit_year_subtypes.PARTIM if learning_unit_full_instance else \
            learning_unit_year_subtypes.FULL
        self.start_postponement = start_postponement
        self.person = person
        self.check_consistency = check_consistency

        if end_postponement is None and self.learning_unit_instance and self.learning_unit_instance.end_year:
            end_postponement = academic_year.find_academic_year_by_year(self.learning_unit_instance.end_year)

        self.end_postponement = end_postponement
        self._init_forms(data)

    def _init_forms(self, data=None):
        """This function will init two forms var:
           forms_to_upsert: LearningUnitBaseForm which must be created/updated
           forms_to_delete: LearningUnitBaseForm which must be deleted
        """
        if self.end_postponement and self.learning_unit_instance:
            # CASE end year specify in learning unit
            self._forms_to_delete = self._get_forms_to_delete(self.end_postponement.year, self.learning_unit_instance)

        if self.learning_unit_instance:
            # Update case
            self._forms_to_upsert = self._get_forms_to_upsert(data, self.start_postponement)
        else:
            # Creation case
            start_year = self.start_postponement.year
            end_year = self.end_postponement.year if self.end_postponement else None
            self._forms_to_upsert = self._get_forms_to_insert(start_year, end_year, data)

    def _get_forms_to_upsert(self, data, start_academic_year):
        end_academic_year = self.end_postponement
        luy_to_upsert_qs = learning_unit_year.find_by_learning_unit(self.learning_unit_instance) \
                                             .filter(academic_year__year__gte=start_academic_year.year)\
                                             .select_related('academic_year')\
                                             .order_by('academic_year__year')

        # We do not need postponement for learning unit in the past
        if start_academic_year.is_past():
            luy = luy_to_upsert_qs.first()
            return [self._get_learning_unit_base_form(luy.academic_year,
                                                      learning_unit_instance=luy.learning_unit,
                                                      data=data)]

        if end_academic_year:
            luy_to_upsert_qs = luy_to_upsert_qs.filter(academic_year__year__lte=end_academic_year.year)

        # Learning unit base form with instance [TO UPDATE]
        luy_base_forms_update = [self._get_learning_unit_base_form(luy_to_upsert.academic_year,
                                                                   learning_unit_instance=luy_to_upsert.learning_unit,
                                                                   data=data)
                                 for luy_to_upsert in luy_to_upsert_qs]

        # Learning unit base form without instance [TO INSERT]
        lastest_luy = luy_to_upsert_qs.last()
        start_insert_year = lastest_luy.academic_year.year + 1 if lastest_luy else start_academic_year.year
        end_insert_year = end_academic_year.year if end_academic_year else None
        luy_base_forms_insert = self._get_forms_to_insert(start_insert_year, end_year=end_insert_year, data=data)

        return luy_base_forms_update + luy_base_forms_insert

    def _get_forms_to_insert(self, start_insert_year, end_year=None, data=None):
        luy_base_form_insert = []
        max_postponement_year = academic_year.compute_max_academic_year_adjournment()
        end_year = min(end_year,  max_postponement_year) if end_year else max_postponement_year

        if start_insert_year <= end_year:
            ac_years = academic_year.find_academic_years(start_year=start_insert_year, end_year=end_year)
            luy_base_form_insert = [self._get_learning_unit_base_form(ac_year, data=data, start_year=start_insert_year)
                                    for ac_year in ac_years]

        return luy_base_form_insert

    def _get_forms_to_delete(self, start_year, learning_unit_instance):
        end_year = self.end_postponement.year
        luy_to_delete_qs = learning_unit_year.find_by_learning_unit(self.learning_unit_instance)\
                                             .filter(academic_year__year__gt=end_year).select_related('academic_year')
        return [self._get_learning_unit_base_form(luy.academic_year, learning_unit_instance=learning_unit_instance)
                for luy in luy_to_delete_qs]

    def _get_learning_unit_base_form(self, academic_year, learning_unit_instance=None, data=None, start_year=None):
        form_kwargs = {
            'person': self.person,
            'learning_unit_instance': learning_unit_instance,
            'academic_year': academic_year,
            'start_year': start_year,
            'data': data.copy() if data else None,
            'learning_unit_full_instance': self.learning_unit_full_instance
        }
        if learning_unit_instance and data:
            learning_unit_year_full_instance = learning_unit_year.search(academic_year_id=academic_year.id,
                                                                         learning_unit=learning_unit_instance).get()
            management_form_updated = self._get_entity_formset_management_form(data, learning_unit_year_full_instance)
            form_kwargs['data'].update(management_form_updated)

        return FullForm(**form_kwargs) if self.subtype == learning_unit_year_subtypes.FULL else \
            PartimForm(**form_kwargs)

    def _get_entity_formset_management_form(self, data, learning_unit_year_full_instance):
        """This function will update specific key [related to learning container year]
           of management form provided by formset"""
        management_form = {}
        for index, type in enumerate(entity_container_year_link_type.ENTITY_TYPE_LIST):
            if data.get('entitycontaineryear_set-{}-learning_container_year'.format(index)):
                management_form['entitycontaineryear_set-{}-learning_container_year'.format(index)] = \
                    learning_unit_year_full_instance.learning_container_year.id
        return management_form

    def is_valid(self):
        if any([not form_instance.is_valid() for form_instance in self._forms_to_upsert]):
            return False

        if self.check_consistency:
            self._check_consistency()

        return True

    @property
    def errors(self):
        return [form_instance.errors for form_instance in self._forms_to_upsert]

    @transaction.atomic
    def save(self):
        if self._forms_to_upsert:
            current_learn_unit_year = self._forms_to_upsert[0].save()
            learning_unit = current_learn_unit_year.learning_unit
            self._luy_upserted.append(current_learn_unit_year)

            if len(self._forms_to_upsert) > 1:
                for form in self._forms_to_upsert[1:]:
                    if form.academic_year in self.consistency_errors:
                        break

                    form.learning_unit_form.instance = learning_unit
                    self._luy_upserted.append(form.save())

        return self._luy_upserted

    def _check_consistency(self):
        if not self.learning_unit_instance or not self._forms_to_upsert or len(self._forms_to_upsert) == 1:
            return True
        return not self._find_consistency_errors()

    def get_context(self):
        if self._forms_to_upsert:
            return self._forms_to_upsert[0].get_context()
        return {}

    def _find_consistency_errors(self):
        form_kwargs = {'learning_unit_instance': self.learning_unit_instance,
                       'start_year': self.learning_unit_instance.start_year}
        current_form = self._get_learning_unit_base_form(self.start_postponement, **form_kwargs)
        academic_years = sorted([form.instance.academic_year for form in self._forms_to_upsert],
                                key=lambda ac_year: ac_year.year)

        self.consistency_errors = OrderedDict()
        for ac_year in academic_years:
            next_form = self._get_learning_unit_base_form(ac_year, **form_kwargs)
            self._check_postponement_proposal_state(next_form.learning_unit_year_form.instance, ac_year)
            self._check_differences(current_form, next_form, ac_year)

        return self.consistency_errors

    @property
    def warnings(self):
        """ Warnings can be call only after saving the forms"""
        if self._warnings is None and self._luy_upserted:
            self._warnings = []
            # Add the warnings of the current year
            for form in self._forms_to_upsert[0]:
                if hasattr(form, 'warnings'):
                    self._warnings.extend(form.warnings)

            if self.consistency_errors:
                self._warnings.append(_('The learning unit has been updated until %(year)s.') % {
                    'year': self._luy_upserted[-1].academic_year
                })
                for ac, errors in self.consistency_errors.items():
                    for error in errors:
                        self._warnings.append(
                            _("Consistency error in %(academic_year)s : %(error)s") % {
                                'academic_year': ac, 'error': error}
                        )

        return self._warnings

    def _check_postponement_proposal_state(self, luy, ac_year):
        if luy.is_in_proposal():
            self.consistency_errors.setdefault(ac_year, []).append(
                _("learning_unit_in_proposal_cannot_save") % {
                    'luy': luy.acronym, 'academic_year': ac_year
                }
            )

    def _check_differences(self, current_form, next_form, ac_year):

        differences = [
            _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                'col_name': next_form.label_fields[col_name],
                'new_value': next_form.instances_data[col_name],
                'current_value': value
            } for col_name, value in current_form.instances_data.items()
            if next_form.instances_data[col_name] != value and col_name not in FIELDS_TO_NOT_CHECK
        ]

        if differences:
            self.consistency_errors.setdefault(ac_year, []).extend(differences)
