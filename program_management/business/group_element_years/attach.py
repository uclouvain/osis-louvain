##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import abc

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ngettext, gettext

from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from program_management.business.group_element_years import group_element_year_tree


class AttachStrategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def is_valid(self):
        pass


class AttachEducationGroupYearStrategy(AttachStrategy):
    def __init__(self, parent: EducationGroupYear, child: EducationGroupYear, instance=None):
        self.parent = parent
        self.child = child
        self.instance = instance

    @cached_property
    def parents(self):
        return EducationGroupYear.hierarchy.filter(pk=self.parent.pk).get_parents() \
            .select_related('education_group_type')

    def is_valid(self):
        if self.parent.education_group_type.name in TrainingType.root_master_2m_types() or \
                self.parents.filter(education_group_type__name__in=TrainingType.root_master_2m_types()).exists():
            self._check_end_year_constraints_on_2m()
            self._check_attach_options_rules()

        if not self.instance:
            self._check_new_attach_is_not_duplication()
            GroupElementYear(parent=self.parent, child_branch=self.child, child_leaf=None).clean()
        return True

    # FIXME :: DEPRECATED - Use AttachFinalityEndDateValidator instead
    def _check_end_year_constraints_on_2m(self):
        """
        In context of 2M, when we add a finality [or group which contains finality], we must ensure that
        the end date of all 2M is greater or equals of all finalities
        """
        finalities_to_add_qs = EducationGroupYear.objects.filter(
            pk=self.child.pk) | EducationGroupYear.hierarchy.filter(pk=self.child.pk).get_children()
        finalities_to_add_qs = finalities_to_add_qs.filter(education_group_type__name__in=TrainingType.finality_types())

        root_2m_qs = self.parents | EducationGroupYear.objects.filter(pk=self.parent.pk)
        root_2m_qs = root_2m_qs.filter(
            education_group_type__name__in=TrainingType.root_master_2m_types(),
            education_group__end_year__isnull=False,
        ).order_by('education_group__end_year')

        errors = []
        if finalities_to_add_qs.exists() and root_2m_qs.exists():
            root_2m_early_end_date = root_2m_qs.first()
            invalid_finalities_acronyms = finalities_to_add_qs.filter(
                Q(education_group__end_year__year__gt=root_2m_early_end_date.education_group.end_year.year) |
                Q(education_group__end_year__isnull=True)
            ).values_list('acronym', flat=True)

            if invalid_finalities_acronyms:
                errors.append(
                    ValidationError(
                        ngettext(
                            "Finality \"%(acronym)s\" has an end date greater than %(root_acronym)s program.",
                            "Finalities \"%(acronym)s\" have an end date greater than %(root_acronym)s program.",
                            len(invalid_finalities_acronyms)
                        ) % {
                            "acronym": ', '.join(invalid_finalities_acronyms),
                            "root_acronym": root_2m_early_end_date.acronym
                        }
                    )
                )

        if errors:
            raise ValidationError(errors)

    def _get_missing_options(self):
        """
            In context of MA/MD/MS when we add an option [or group which contains options],
            this options must exist in parent context (2m)
        """
        options_missing_by_finality = {}

        options_to_add = group_element_year_tree.EducationGroupHierarchy(root=self.child).get_option_list()
        if self.child.education_group_type.name == MiniTrainingType.OPTION.name:
            options_to_add += [self.child]

        finalities_qs = self.parents | EducationGroupYear.objects.filter(pk=self.parent.pk)
        finalities_pks = finalities_qs.filter(
            education_group_type__name__in=TrainingType.finality_types()
        ).values_list('pk', flat=True)
        if self.child.education_group_type.name in TrainingType.finality_types():
            finalities_pks = list(finalities_pks) + [self.parent.pk]
        if finalities_pks:
            root_2m_qs = EducationGroupYear.hierarchy.filter(pk__in=finalities_pks).get_parents().filter(
                education_group_type__name__in=TrainingType.root_master_2m_types()
            )

            for root in root_2m_qs:
                options_in_2m = group_element_year_tree.EducationGroupHierarchy(root=root).get_option_list()
                options_missing_by_finality[root] = set(options_to_add) - set(options_in_2m)
        return options_missing_by_finality

    # FIXME :: DEPRECATED -  Use AttachOptionsValidator
    def _check_attach_options_rules(self):
        errors = []
        for root, missing_options in self._get_missing_options().items():
            if missing_options:
                errors.append(
                    ValidationError(
                        ngettext(
                            "Option \"%(acronym)s\" must be present in %(root_acronym)s program.",
                            "Options \"%(acronym)s\" must be present in %(root_acronym)s program.",
                            len(missing_options)
                        ) % {
                            "acronym": ', '.join(option.acronym for option in missing_options),
                            "root_acronym": root.acronym
                        })
                )
        if errors:
            raise ValidationError(errors)

    # FIXME :: DEPRECATED - Use NodeDuplicationValidator
    def _check_new_attach_is_not_duplication(self):
        if GroupElementYear.objects.filter(parent=self.parent, child_branch=self.child).exists():
            raise ValidationError(gettext("You can not add the same child several times."))


class AttachLearningUnitYearStrategy(AttachStrategy):
    def __init__(self, parent: EducationGroupYear, child: LearningUnitYear, instance=None):
        self.parent = parent
        self.child = child
        self.instance = instance

    def is_valid(self):
        if not self.instance:
            self._check_new_attach_is_not_duplication()
            GroupElementYear(parent=self.parent, child_branch=None, child_leaf=self.child).clean()
        if not self.parent.education_group_type.learning_unit_child_allowed:
            raise ValidationError(gettext("You can not add a learning unit to a %(category)s of type %(type)s.") % {
                'category': self.parent.education_group_type.get_category_display(),
                'type': self.parent.education_group_type.get_name_display()
            })
        return True

    # FIXME :: DEPRECATED - Use NodeDuplicationValidator
    def _check_new_attach_is_not_duplication(self):
        if GroupElementYear.objects.filter(parent=self.parent, child_leaf=self.child).exists():
            raise ValidationError(gettext("You can not add the same child several times."))


def can_attach_learning_units(egy: EducationGroupYear):
    return egy.education_group_type.category == education_group_categories.Categories.GROUP.name
