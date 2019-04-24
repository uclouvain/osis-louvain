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
import operator
from collections import OrderedDict

from django.db import transaction
from django.db.models import Max
from django.http import QueryDict
from django.utils.translation import ugettext as _

from base.forms.learning_unit.external_learning_unit import ExternalLearningUnitBaseForm
from base.forms.learning_unit.learning_unit_create_2 import FullForm
from base.forms.learning_unit.learning_unit_partim import PartimForm
from base.models import academic_year
from base.models.academic_year import AcademicYear
from base.models.entity_component_year import EntityComponentYear
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_component_year_type import LECTURING
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.models.proposal_learning_unit import is_learning_unit_year_in_proposal

FIELDS_TO_NOT_POSTPONE = {
    'is_vacant': 'learning_container_year.is_vacant',
    'type_declaration_vacant': 'learning_container_year.type_declaration_vacant',
    'attribution_procedure': 'attribution_procedure'
}
FIELDS_TO_NOT_CHECK = ['academic_year', 'id'] + list(FIELDS_TO_NOT_POSTPONE.keys())


# @TODO: Use LearningUnitPostponementForm to manage END_DATE of learning unit year
# TODO :: Maybe could we move this code to LearningUnitModelForm class?
class LearningUnitPostponementForm:
    learning_unit_instance = None
    subtype = None
    person = None
    check_consistency = True
    _forms_to_upsert = None
    _forms_to_delete = None
    _warnings = None
    consistency_errors = None
    _luy_upserted = None

    def __init__(self, person, start_postponement, end_postponement=None, learning_unit_instance=None,
                 learning_unit_full_instance=None, data=None, check_consistency=True,
                 external=False):
        self.check_input_instance(learning_unit_full_instance, learning_unit_instance)

        self.learning_unit_instance = learning_unit_instance
        self.learning_unit_full_instance = learning_unit_full_instance
        self.subtype = learning_unit_year_subtypes.PARTIM if learning_unit_full_instance else \
            learning_unit_year_subtypes.FULL
        self.start_postponement = start_postponement
        self.person = person
        self.check_consistency = check_consistency
        self.external = external

        # end_year can be given by the request (eg: for partims)
        end_year = data and data.get('end_year')
        if end_year:
            end_postponement = academic_year.find_academic_year_by_year(end_year)

        self.end_postponement = self._get_academic_end_year(end_postponement)
        self._compute_forms_to_insert_update_delete(data)

    @staticmethod
    def check_input_instance(learning_unit_full_instance, learning_unit_instance):
        if learning_unit_instance and not isinstance(learning_unit_instance, LearningUnit):
            raise AttributeError('learning_unit_instance arg should be an instance of {}'.format(LearningUnit))
        if learning_unit_full_instance and not isinstance(learning_unit_full_instance, LearningUnit):
            raise AttributeError('learning_unit_full_instance arg should be an instance of {}'.format(LearningUnit))

    def _get_academic_end_year(self, end_postponement):
        if end_postponement is None:
            if self.learning_unit_instance and self.learning_unit_instance.end_year:
                end_postponement = academic_year.find_academic_year_by_year(self.learning_unit_instance.end_year)
            elif self.learning_unit_full_instance and self.learning_unit_full_instance.end_year:
                end_postponement = academic_year.find_academic_year_by_year(self.learning_unit_full_instance.end_year)
        return end_postponement

    def _compute_max_postponement_year(self) -> int:
        """ Compute the maximal year for the postponement of the learning unit

        If the learning unit is a partim, the max year is the max year of the full
        """
        if self.subtype == learning_unit_year_subtypes.PARTIM:
            max_postponement_year = self.learning_unit_full_instance.learningunityear_set.aggregate(
                Max('academic_year__year')
            )['academic_year__year__max']
        else:
            max_postponement_year = academic_year.compute_max_academic_year_adjournment()

        end_year = self.end_postponement.year if self.end_postponement else None
        return min(end_year, max_postponement_year) if end_year else max_postponement_year

    def _compute_forms_to_insert_update_delete(self, data):
        if self._has_proposal(self.learning_unit_instance) and \
                (self.person.is_faculty_manager and not self.person.is_central_manager):
            proposal = ProposalLearningUnit.objects.filter(
                learning_unit_year__learning_unit=self.learning_unit_instance
            ).order_by('learning_unit_year__academic_year__year').first()
            max_postponement_year = proposal.learning_unit_year.academic_year.year
            ac_year_postponement_range = AcademicYear.objects.filter(
                year__gte=self.start_postponement.year,
                year__lt=proposal.learning_unit_year.academic_year.year
            )

            existing_learn_unit_years = LearningUnitYear.objects \
                .filter(academic_year__year__gte=self.start_postponement.year) \
                .filter(academic_year__year__lt=max_postponement_year) \
                .filter(learning_unit=self.learning_unit_instance) \
                .select_related('learning_container_year', 'learning_unit', 'academic_year') \
                .order_by('academic_year__year')
        else:
            max_postponement_year = self._compute_max_postponement_year()
            ac_year_postponement_range = AcademicYear.objects.min_max_years(
                self.start_postponement.year,
                max_postponement_year
            )
            existing_learn_unit_years = LearningUnitYear.objects.filter(
                academic_year__year__gte=self.start_postponement.year,
                learning_unit=self.learning_unit_instance,
            ).select_related(
                'learning_container_year', 'learning_unit', 'academic_year'
            ).order_by('academic_year__year')
        to_delete = to_update = to_insert = []

        if self.start_postponement.is_past():
            to_update = self._init_forms_in_past(existing_learn_unit_years, data)
        else:
            if self._is_update_action():
                to_delete = [
                    self._instantiate_base_form_as_update(luy, index_form=index)
                    for index, luy in enumerate(existing_learn_unit_years)
                    if luy.academic_year.year > max_postponement_year
                ]
                to_update = [
                    self._instantiate_base_form_as_update(luy, index_form=index, data=data)
                    for index, luy in enumerate(existing_learn_unit_years)
                    if luy.academic_year.year <= max_postponement_year
                ]
                existing_ac_years = [luy.academic_year for luy in existing_learn_unit_years]
                to_insert = []
                # FIXME: We use data copy because data is immuniable and acronym, academic_year and container_type
                # is not in data with edition form
                for index, ac_year in enumerate(ac_year_postponement_range):
                    if ac_year not in existing_ac_years:
                        data_to_insert = None
                        if data and existing_learn_unit_years:
                            data_to_insert = data.copy()
                            data_to_insert["acronym_0"] = existing_learn_unit_years[0].acronym[0]
                            data_to_insert["acronym_1"] = existing_learn_unit_years[0].acronym[1:]
                            data_to_insert["container_type"] = \
                                existing_learn_unit_years[0].learning_container_year.container_type
                            data_to_insert["academic_year"] = str(ac_year.id)
                            # FIXME: component-initial_forms must be 0 for the insert in DB
                            data_to_insert["component-INITIAL_FORMS"] = 0
                            to_insert.append(self._instantiate_base_form_as_insert(ac_year, data_to_insert))
                        else:
                            to_insert.append(self._instantiate_base_form_as_insert(ac_year, data))
            else:
                to_insert = [
                    self._instantiate_base_form_as_insert(ac_year, data)
                    for index, ac_year in enumerate(ac_year_postponement_range)
                ]

        self._forms_to_delete = to_delete
        self._forms_to_upsert = to_update + to_insert

    def _init_forms_in_past(self, luy_queryset, data):
        if self._is_update_action() and luy_queryset.exists():
            first_luy = luy_queryset.first()
            return [self._instantiate_base_form_as_update(first_luy, data=data)]
        else:
            return [self._instantiate_base_form_as_insert(self.start_postponement, data)]

    def _instantiate_base_form_as_update(self, luy_to_update, index_form=0, data=None):

        def is_first_form(index):
            return index == 0

        if data is None or is_first_form(index_form):
            data_to_postpone = data
        else:
            data_to_postpone = self._get_data_to_postpone(luy_to_update, data)
            self._update_form_set_data(data_to_postpone, luy_to_update)

        return self._get_learning_unit_base_form(
            luy_to_update.academic_year,
            learning_unit_instance=luy_to_update.learning_unit,
            data=data_to_postpone
        )

    @staticmethod
    def _update_form_set_data(data_to_postpone, luy_to_update):
        learning_component_years = LearningComponentYear.objects.filter(learning_unit_year=luy_to_update)
        for learning_component_year in learning_component_years:
            if learning_component_year.type == LECTURING:
                data_to_postpone['component-0-id'] = learning_component_year.id
            else:
                data_to_postpone['component-1-id'] = learning_component_year.id

    def _instantiate_base_form_as_insert(self, ac_year, data):
        return self._get_learning_unit_base_form(ac_year, data=data, start_year=self.start_postponement.year)

    @staticmethod
    def _get_data_to_postpone(lunit_year, data):
        data_to_postpone = QueryDict('', mutable=True)
        data_to_postpone.update({key: data[key] for key in data if key not in FIELDS_TO_NOT_POSTPONE.keys()})
        for key, attr_path in FIELDS_TO_NOT_POSTPONE.items():
            data_to_postpone[key] = operator.attrgetter(attr_path)(lunit_year)
        return data_to_postpone

    def _get_learning_unit_base_form(self, ac_year, learning_unit_instance=None, data=None, start_year=None):
        form_kwargs = {
            'person': self.person,
            'learning_unit_instance': learning_unit_instance,
            'academic_year': ac_year,
            'start_year': start_year,
            'data': data.copy() if data else None,
            'learning_unit_full_instance': self.learning_unit_full_instance,
            'postposal': not data
        }
        if self.external:
            return ExternalLearningUnitBaseForm(**form_kwargs)
        return FullForm(**form_kwargs) if self.subtype == learning_unit_year_subtypes.FULL else \
            PartimForm(**form_kwargs)

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
        self._luy_upserted = []
        if self._forms_to_upsert:
            current_learn_unit_year = self._forms_to_upsert[0].save()
            learning_unit = current_learn_unit_year.learning_unit
            self._luy_upserted.append(current_learn_unit_year)

            if len(self._forms_to_upsert) > 1:
                for form in self._forms_to_upsert[1:]:
                    if self.consistency_errors and form.academic_year in self.consistency_errors:
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
        if self._has_proposal(self.learning_unit_instance) and \
                (self.person.is_faculty_manager and not self.person.is_central_manager):
            max_postponement_year = self._compute_max_postponement_year()
            academic_years = academic_year.find_academic_years(start_year=self.start_postponement.year,
                                                               end_year=max_postponement_year)
        else:
            academic_years = sorted([form.instance.academic_year for form in self._forms_to_upsert if form.instance],
                                    key=lambda ac_year: ac_year.year)

        self.consistency_errors = OrderedDict()
        for ac_year in academic_years:
            next_form = self._get_learning_unit_base_form(ac_year, **form_kwargs)
            self._check_postponement_proposal_state(next_form.learning_unit_year_form.instance, ac_year)
            self._check_postponement_repartition_volume(next_form.learning_unit_year_form.instance)
            self._check_differences(current_form, next_form, ac_year)

        return self.consistency_errors

    @property
    def warnings(self):
        """ Warnings can be call only after saving the forms"""
        if self._warnings is None and self._luy_upserted:
            self._warnings = []
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
        if is_learning_unit_year_in_proposal(luy):
            self.consistency_errors.setdefault(ac_year, []).append(
                _("The learning unit %(luy)s is in proposal, can not"
                  " save the change from the year %(academic_year)s") % {
                    'luy': luy.acronym, 'academic_year': ac_year
                }
            )

    def _check_postponement_repartition_volume(self, luy):
        """ Check if the repartition volume foreach entities has been changed in the future

        This volume is never edited in the form, so we have to load data separably
        """
        initial_learning_unit_year = self._forms_to_upsert[0].instance
        initial_values = EntityComponentYear.objects.filter(
            learning_component_year__learning_unit_year=initial_learning_unit_year
        ).values_list('repartition_volume', 'learning_component_year__type', 'entity_container_year__type')

        for reparation_volume, component_type, entity_type in initial_values:
            try:
                component = EntityComponentYear.objects.filter(
                    learning_component_year__type=component_type,
                    entity_container_year__type=entity_type,
                    learning_component_year__learning_unit_year=luy
                ).get()
            except EntityComponentYear.DoesNotExist:
                # Case: N year have additional requirement but N+1 doesn't have.
                # Not need to display message because, already done on _check_differences function
                component = None

            if component and component.repartition_volume != reparation_volume:
                name = component.learning_component_year.acronym + "-" + \
                       component.entity_container_year.entity.most_recent_acronym

                self.consistency_errors.setdefault(luy.academic_year, []).append(
                    _("The repartition volume of %(col_name)s has been already modified. "
                      "({%(new_value)s} instead of {%(current_value)s})") % {
                        'col_name': name,
                        'new_value': component.repartition_volume,
                        'current_value': reparation_volume
                    }
                )

    def _check_differences(self, current_form, next_form, ac_year):
        differences = [
            _("%(col_name)s has been already modified. ({%(new_value)s} instead of {%(current_value)s})") % {
                'col_name': next_form.label_fields.get(col_name, col_name),
                'new_value': self._get_translated_value(next_form.instances_data.get(col_name)),
                'current_value': self._get_translated_value(value)
            } for col_name, value in current_form.instances_data.items()
            if self._get_cmp_value(next_form.instances_data.get(col_name)) != self._get_cmp_value(value) and
            col_name not in FIELDS_TO_NOT_CHECK
        ]

        if differences:
            self.consistency_errors.setdefault(ac_year, []).extend(differences)

    @staticmethod
    def _get_cmp_value(value):
        """This function return comparable value. It consider empty string as null value"""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @staticmethod
    def _get_translated_value(value):
        if isinstance(value, bool):
            return _("yes") if value else _("no")
        elif value is None:
            return "-"
        return value

    def _is_update_action(self):
        return self.learning_unit_full_instance or self.learning_unit_instance

    @staticmethod
    def _has_proposal(luy):
        return ProposalLearningUnit.objects.filter(learning_unit_year__learning_unit=luy).exists()
