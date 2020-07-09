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
from collections import Counter

from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _, ngettext

import program_management.ddd.repositories.find_roots
from base.models import group_element_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from program_management.business.group_element_years.group_element_year_tree import EducationGroupHierarchy
from program_management.business.group_element_years.management import CheckAuthorizedRelationshipDetach


class DetachStrategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def is_valid(self):
        pass


class DetachEducationGroupYearStrategy(DetachStrategy):
    def __init__(self, link: GroupElementYear):
        self.link = link
        self.parent = self.link.parent
        self.education_group_year = self.link.child
        self.errors = []
        self.warnings = []

    def is_valid(self):
        """
                The user cannot delete the link if :
                    - the child has or is prerequisite
                    - the minimum of children is reached
                    - try to remove option (2m) which are present in one of its finality
        """
        check = CheckAuthorizedRelationshipDetach(self.parent, link_to_detach=self.link)
        if not check.is_valid():
            self.errors.extend(check.errors)

        self._check_detach_prerequisite_rules()

        if self._options_to_detach() and self.get_parents_program_master():
            self._check_detach_options_rules()

        return len(self.errors) == 0

    def post_valid(self):
        self.delete_prerequisites()

    def delete_prerequisites(self):
        prerequisites = Prerequisite.objects.filter(
            education_group_year__in=self._parents,
            learning_unit_year__in=self._learning_units_year_to_detach
        )
        for prerequisite in prerequisites:
            prerequisite.delete()

    def get_parents_program_master(self):
        return filter(lambda elem: elem.education_group_type.name in [
            TrainingType.PGRM_MASTER_120.name,
            TrainingType.PGRM_MASTER_180_240.name
        ], self._parents)

    @cached_property
    def _parents(self):
        return program_management.ddd.repositories.find_roots.find_roots(
            [self.parent],
            as_instances=True
        )[self.parent.pk] + [self.parent]

    @cached_property
    def _learning_units_year_to_detach(self):
        return EducationGroupHierarchy(root=self.education_group_year).get_learning_unit_year_list()

    def _options_to_detach(self):
        options_to_detach = EducationGroupHierarchy(root=self.education_group_year).get_option_list()
        if self.education_group_year.education_group_type.name == MiniTrainingType.OPTION.name:
            options_to_detach += [self.education_group_year]
        return options_to_detach

    # FIXME :: DEPRECATED :: use HasPrerequisiteValidator or IsPrerequisiteValidator instead
    def _check_detach_prerequisite_rules(self):
        for formation in self._parents:
            luys_inside_formation = Counter(EducationGroupHierarchy(root=formation).get_learning_unit_year_list())
            luys_to_detach = Counter(self._learning_units_year_to_detach)
            luys_inside_formation_after_detach = luys_inside_formation - luys_to_detach

            luys_that_are_prerequisites = LearningUnitYear.objects.filter(
                learning_unit__prerequisiteitem__prerequisite__learning_unit_year__in=list(
                    luys_inside_formation_after_detach.keys()
                ),
                learning_unit__prerequisiteitem__prerequisite__education_group_year=formation,
                id__in=[luy.id for luy in self._learning_units_year_to_detach]
            )
            luys_that_cannot_be_detached = [luy for luy in luys_that_are_prerequisites
                                            if luy not in luys_inside_formation_after_detach]
            if luys_that_cannot_be_detached:
                self.errors.append(
                    _("Cannot detach education group year %(acronym)s as the following learning units "
                      "are prerequisite in %(formation)s: %(learning_units)s") % {
                        "acronym": self.education_group_year.acronym,
                        "formation": formation.acronym,
                        "learning_units": ", ".join([luy.acronym for luy in luys_that_cannot_be_detached])
                    }
                )

        luys_that_have_prerequisites = LearningUnitYear.objects.filter(
            id__in=Prerequisite.objects.filter(
                education_group_year__in=self._parents,
                learning_unit_year__in=self._learning_units_year_to_detach
            ).values(
                "learning_unit_year__id"
            )
        )
        if luys_that_have_prerequisites:
            self.warnings.append(
                _("The prerequisites for the following learning units contained in education group year "
                  "%(acronym)s will we deleted: %(learning_units)s") % {
                    "acronym": self.education_group_year.acronym,
                    "learning_units": ", ".join([luy.acronym for luy in luys_that_have_prerequisites])
                }
            )

    # FiXME :: DEPRECATED :: Use DetachOptionValidator instead
    def _check_detach_options_rules(self):
        """
        In context of 2M when we detach an option [or group which contains option], we must ensure that
        these options are not present in MA/MD/MS
        """
        options_to_detach = self._options_to_detach()

        for master_2m in self.get_parents_program_master():
            master_2m_tree = EducationGroupHierarchy(root=master_2m)

            counter_options = Counter(master_2m_tree.get_option_list())
            counter_options.subtract(options_to_detach)
            options_to_check = [opt for opt, count in counter_options.items() if count == 0]
            if not options_to_check:
                continue

            finality_list = [elem.child for elem in master_2m_tree.to_list(flat=True)
                             if isinstance(elem.child, EducationGroupYear)
                             and elem.child.education_group_type.name in TrainingType.finality_types()]
            for finality in finality_list:
                mandatory_options = EducationGroupHierarchy(root=finality).get_option_list()
                missing_options = set(options_to_check) & set(mandatory_options)

                if missing_options:
                    self.errors.append(
                        ValidationError(
                            ngettext(
                                "Option \"%(acronym)s\" cannot be detach because it is contained in"
                                " %(finality_acronym)s program.",
                                "Options \"%(acronym)s\" cannot be detach because they are contained in"
                                " %(finality_acronym)s program.",
                                len(missing_options)
                            ) % {
                                "acronym": ', '.join(option.acronym for option in missing_options),
                                "finality_acronym": finality.acronym
                            })
                    )


# FiXME :: DEPRECATED :: Use IsPrerequisiteValidator instead
class DetachLearningUnitYearStrategy(DetachStrategy):
    def __init__(self, link: GroupElementYear):
        self.parent = link.parent
        self.learning_unit_year = link.child
        self.warnings = []
        self.errors = []

    def is_valid(self):
        if self.learning_unit_year.has_or_is_prerequisite(self.parent):
            self.errors.append(
                _("Cannot detach learning unit %(acronym)s as it has a prerequisite or it is a prerequisite.") % {
                    "acronym": self.learning_unit_year.acronym
                }
            )
        return len(self.errors) == 0

    def post_valid(self):
        pass
