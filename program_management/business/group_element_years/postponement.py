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
import itertools

from django.db import Error, transaction
from django.db.models import Q, Exists, OuterRef
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from base.business.education_groups import postponement
from base.business.utils.model import update_related_object
from base.models.academic_year import starting_academic_year, AcademicYear
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import MiniTrainingType, TrainingType
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear, fetch_row_sql
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from base.models.prerequisite_item import PrerequisiteItem
from program_management.business.group_element_years import attach


class CopyWarning(Warning):
    pass


class ReuseOldLearningUnitYearWarning(CopyWarning):
    def __init__(self, obj: LearningUnitYear, academic_year):
        self.learning_unit_year = obj
        self.academic_year = academic_year

    def __str__(self):
        return _("Learning unit %(learning_unit_year)s does not exist in %(academic_year)s => "
                 "Learning unit is postponed with academic year of %(learning_unit_academic_year)s.") % {
                   "learning_unit_year": self.learning_unit_year.acronym,
                   "academic_year": self.academic_year,
                   "learning_unit_academic_year": self.learning_unit_year.academic_year
               }


class PrerequisiteItemWarning(CopyWarning):
    def __init__(self, prerequisite: Prerequisite, item: PrerequisiteItem, egy: EducationGroupYear):
        self.prerequisite = prerequisite
        self.item = item
        self.egy = egy

    def __str__(self):
        return _("%(prerequisite_item)s is not anymore contained in "
                 "%(education_group_year_root)s "
                 "=> the prerequisite for %(learning_unit_year)s "
                 "having %(prerequisite_item)s as prerequisite is not copied.") % {
                   "education_group_year_root": _display_education_group_year(self.egy),
                   "learning_unit_year": self.prerequisite.learning_unit_year.acronym,
                   "prerequisite_item": self.item.learning_unit.acronym
               }


class PrerequisiteWarning(CopyWarning):
    def __init__(self, luy: LearningUnitYear, egy: EducationGroupYear):
        self.luy = luy
        self.egy = egy

    def __str__(self):
        return _("%(learning_unit_year)s is not anymore contained in "
                 "%(education_group_year_root)s "
                 "=> the prerequisite for %(learning_unit_year)s is not copied.") % {
                   "education_group_year_root": _display_education_group_year(self.egy),
                   "learning_unit_year": self.luy.acronym,
               }


class EducationGroupYearNotEmptyWarning(CopyWarning):
    def __init__(self, obj: EducationGroupYear, academic_year):
        self.education_group_year = obj
        self.academic_year = academic_year

    def __str__(self):
        return _("%(education_group_year)s has already been copied in %(academic_year)s in another program. "
                 "It may have been already modified.") % {
                   "education_group_year": _display_education_group_year(self.education_group_year),
                   "academic_year": self.academic_year
               }


class ReferenceLinkEmptyWarning(CopyWarning):
    def __init__(self, obj: EducationGroupYear, ):
        self.education_group_year = obj

    def __str__(self):
        return _("%(education_group_year)s (reference link) has not been copied. Its content is empty.") % {
            "education_group_year": _display_education_group_year(self.education_group_year)
        }


class EducationGroupEndYearWarning(CopyWarning):
    def __init__(self, obj: EducationGroupYear, academic_year):
        self.education_group_year = obj
        self.academic_year = academic_year

    def __str__(self):
        return _("%(education_group_year)s is closed in %(end_year)s. This element will not be copied "
                 "in %(academic_year)s.") % {
                   "education_group_year": _display_education_group_year(self.education_group_year),
                   "end_year": self.education_group_year.education_group.end_year,
                   "academic_year": self.academic_year
               }


class FinalityOptionNotValidWarning(CopyWarning):
    def __init__(self, egy_option: EducationGroupYear, egy_root: EducationGroupYear, egy_finality: EducationGroupYear,
                 academic_year: AcademicYear):
        self.education_group_year_option = egy_option
        self.education_group_year_root = egy_root
        self.education_group_year_finality = egy_finality
        self.academic_year = academic_year

    def __str__(self):
        return _("The option %(education_group_year_option)s is not anymore accessible in "
                 "%(education_group_year_root)s "
                 "in %(academic_year)s => It is retired of the finality %(education_group_year_finality)s.") % {
                   "education_group_year_option": _display_education_group_year(self.education_group_year_option),
                   "education_group_year_root": _display_education_group_year(self.education_group_year_root),
                   "education_group_year_finality": _display_education_group_year(self.education_group_year_finality),
                   "academic_year": self.academic_year
               }


class NotPostponeError(Error):
    pass


class PostponeContent:
    """ Duplicate the content of a education group year content to the next academic year """

    def __init__(self, instance):
        """
        The instance must be a training in the current academic year with an end year greater than
        the next academic year.

        During the initialization, we'll also check if the current instance has a content to postpone.
        """
        if not isinstance(instance, EducationGroupYear):
            raise NotPostponeError(_('You are not allowed to copy the content of this kind of education group.'))

        self.instance = instance
        self.current_year = starting_academic_year()
        self.next_academic_year = self.instance.academic_year.next()

        self.check_instance()

        self.result = []
        self.warnings = []
        self.instance_n1 = self.get_instance_n1(self.instance)

        self.postponed_luy = []
        self.postponed_options = {}
        self.postponed_finalities = []

        self.number_links_created = 0
        self.number_elements_created = 0

    def check_instance(self):
        if self.instance.academic_year.year < self.current_year.year:
            raise NotPostponeError(_("You are not allowed to postpone this training in the past."))
        if self.instance.academic_year.year - 1 > self.current_year.year:
            raise NotPostponeError(_("You are not allowed to postpone this training in the future."))

        end_year = self.instance.education_group.end_year
        if end_year and end_year.year < self.next_academic_year.year:
            raise NotPostponeError(_("The end date of the education group is smaller than the year of postponement."))

        if not self.instance.groupelementyear_set.exists():
            raise NotPostponeError(_("This training has no content to postpone."))

    def get_instance_n1(self, instance):
        try:
            next_instance = instance.education_group.educationgroupyear_set.filter(
                academic_year=self.next_academic_year
            ).get()
        except EducationGroupYear.DoesNotExist:
            raise NotPostponeError(_("The root does not exist in the next academic year."))

        if self._check_if_already_postponed(next_instance):
            raise NotPostponeError(_("The content has already been postponed."))

        return next_instance

    @transaction.atomic
    def postpone(self):
        result = self._postpone(self.instance, self.instance_n1)
        self._post_postponement()
        return result

    def _postpone(self, instance: EducationGroupYear, next_instance: EducationGroupYear):
        """
        We'll postpone first the group_element_years of the root,
        after that, we'll postpone recursively all the child branches and child leafs.
        """

        children = instance.groupelementyear_set.select_related(
            'child_branch__academic_year',
            'child_branch__education_group'
        ).order_by("order", "parent__partial_acronym")
        for gr in children:
            new_gr = self._postpone_child(gr, next_instance)
            self.result.append(new_gr)

        return next_instance

    def _postpone_child(self, gr, next_instance):
        """ Determine if we have to postpone a leaf or a branch """
        new_gr = None

        if gr.child_branch:
            new_gr = next_instance.groupelementyear_set.filter(
                child_branch__education_group=gr.child.education_group
            ).first()

        if not new_gr:
            new_gr = update_related_object(gr, "parent", next_instance, commit_save=False)
            self.number_links_created += 1

        if new_gr.child_leaf:
            new_gr = self._postpone_child_leaf(gr, new_gr)
        else:
            new_gr = self._postpone_child_branch(gr, new_gr)
        new_gr.save()
        return new_gr

    def _post_postponement(self):
        # Postpone the prerequisite only at the end to be sure to have all learning units and education groups
        self._check_options()

        luys_not_postponed = LearningUnitYear.objects.filter(
            id__in=self._learning_units_id_in_n_instance
        ).exclude(
            learning_unit__in=LearningUnit.objects.filter(
                learningunityear__id__in=self._learning_units_id_in_n1_instance
            )
        ).annotate(
            has_prerequisite=Exists(
                PrerequisiteItem.objects.filter(
                    prerequisite__education_group_year__id=self.instance.id,
                    prerequisite__learning_unit_year__id=OuterRef("id"),
                )
            )
        )
        for luy in luys_not_postponed:
            if luy.has_prerequisite:
                self.warnings.append(PrerequisiteWarning(luy, self.instance_n1))

        for old_luy, new_luy in self.postponed_luy:
            self._postpone_prerequisite(old_luy, new_luy)

    def _postpone_child_leaf(self, old_gr, new_gr):
        """
        During the postponement of the learning units, we will take the next learning unit year
        but if it does not exist for N+1, we will attach the current instance.
        """
        old_luy = old_gr.child_leaf
        new_luy = old_luy.learning_unit.learningunityear_set.filter(academic_year=new_gr.parent.academic_year).first()
        if not new_luy:
            new_luy = old_luy
            self.warnings.append(ReuseOldLearningUnitYearWarning(old_luy, self.next_academic_year))

        self.postponed_luy.append((old_luy, new_luy))

        new_gr.child_leaf = new_luy
        return new_gr

    def _postpone_child_branch(self, old_gr: GroupElementYear, new_gr: GroupElementYear) -> GroupElementYear:
        """
        Unlike child leaf, the child branch must be postponed (recursively)
        """
        old_egy = old_gr.child_branch
        new_egy = old_egy.next_year()
        if new_egy:
            is_empty = self._is_empty(new_egy)
            if new_gr.link_type == LinkTypes.REFERENCE.name and is_empty:
                self.warnings.append(ReferenceLinkEmptyWarning(new_egy))
            elif not is_empty:
                if not (new_egy.is_training() or new_egy.education_group_type.name in MiniTrainingType.to_postpone()):
                    self.warnings.append(EducationGroupYearNotEmptyWarning(new_egy, self.next_academic_year))
            else:
                self._postpone(old_egy, new_egy)
        else:
            # If the education group does not exists for the next year, we have to postpone.
            new_egy = self._duplication_education_group_year(old_gr, old_egy)
            self.number_elements_created += 1

        new_gr.child_branch = new_egy
        if new_egy and new_egy.education_group_type.name == MiniTrainingType.OPTION.name:
            self.postponed_options[new_egy.id] = new_gr
        if new_egy and new_gr.parent.education_group_type.name in TrainingType.finality_types():
            self.postponed_finalities.append(new_gr)
        return new_gr

    # FIXME Should be moved to education group year. But cannot because of cyclic import.
    def _is_empty(self, egy: EducationGroupYear):
        """
        An education group year is empty if:
            - it has no children
            - all of his children are mandatory groups and they are empty
        """
        mandatory_groups = AuthorizedRelationship.objects.filter(
            parent_type=egy.education_group_type,
            min_count_authorized=1
        )
        return not GroupElementYear.objects.filter(
            (Q(parent=egy) & ~ Q(child_branch__education_group_type__authorized_child_type__in=mandatory_groups))
            | Q(parent__child_branch__parent=egy)
        ).exists()

    def _duplication_education_group_year(self, old_gr: GroupElementYear, old_egy: EducationGroupYear):
        if old_egy.education_group_type.category != Categories.GROUP.name:
            if old_egy.education_group.end_year and \
                    old_egy.education_group.end_year.year < self.next_academic_year.year:
                self.warnings.append(EducationGroupEndYearWarning(old_egy, self.next_academic_year))
                return None

        new_egy = postponement.duplicate_education_group_year(old_egy, self.next_academic_year)

        if old_gr.link_type != LinkTypes.REFERENCE.name:
            # Copy its children
            self._postpone(old_egy, new_egy)
        else:
            self.warnings.append(ReferenceLinkEmptyWarning(new_egy))

        return new_egy

    def _check_if_already_postponed(self, education_group_year):
        """
        Determine if the content has already been postponed.

        First we have to check the progeny of the education group (! recursive search )
        After verify if all nodes have an authorized relationship with a min count to 1 or a learning unit.
        """
        for gr in education_group_year.groupelementyear_set.all().select_related('child_branch__education_group_type'):
            if gr.child_leaf:
                return True

            relationship = education_group_year.education_group_type.authorized_parent_type.filter(
                child_type=gr.child_branch.education_group_type
            ).first()

            if not relationship or relationship.min_count_authorized == 0:
                return True

            if self._check_if_already_postponed(gr.child_branch):
                return True

        return False

    def _check_options(self):
        missing_options = {}
        for finality in self.postponed_finalities:
            missing_options[finality] = list(itertools.chain.from_iterable(attach.AttachEducationGroupYearStrategy(
                finality.parent, finality.child_branch
            )._get_missing_options().values()))

        for finality, options in missing_options.items():
            for option in options:
                if option.id in self.postponed_options and self.postponed_options[option.id].id:
                    self.warnings.append(
                        FinalityOptionNotValidWarning(
                            option,
                            self.instance_n1,
                            finality.parent,
                            self.next_academic_year
                        )
                    )
                    self.postponed_options[option.id].delete()

    def _postpone_prerequisite(self, old_luy: LearningUnitYear, new_luy: LearningUnitYear):
        """ Copy the prerequisite of a learning unit and its items """
        for prerequisite in old_luy.prerequisite_set.filter(education_group_year=self.instance):
            if not self._check_prerequisite_item_existing_n1(prerequisite):
                continue

            new_prerequisite, _ = Prerequisite.objects.get_or_create(
                learning_unit_year=new_luy,
                education_group_year=self.instance_n1,
                defaults={
                    'main_operator': prerequisite.main_operator
                }
            )
            for item in prerequisite.prerequisiteitem_set.all():
                PrerequisiteItem.objects.get_or_create(
                    position=item.position,
                    group_number=item.group_number,
                    prerequisite=new_prerequisite,
                    defaults={
                        'learning_unit': item.learning_unit
                    }
                )

    def _check_prerequisite_item_existing_n1(self, old_prerequisite: Prerequisite) -> bool:
        """ Check if the prerequisite's items exist in the next academic year.
        In the case, we have to add a warning message and skip the copy.
        """
        result = True
        for item in old_prerequisite.prerequisiteitem_set.all():
            if not item.learning_unit.learningunityear_set.filter(id__in=self._learning_units_id_in_n1_instance):
                self.warnings.append(PrerequisiteItemWarning(old_prerequisite, item, self.instance_n1))
                result = False
        return result

    @cached_property
    def _learning_units_id_in_n_instance(self):
        grps_old = fetch_row_sql([self.instance.id])
        return set(item["child_leaf_id"] for item in grps_old)

    @cached_property
    def _learning_units_id_in_n1_instance(self):
        grps = fetch_row_sql([self.instance_n1.id])
        return set(item["child_leaf_id"] for item in grps)


def _display_education_group_year(egy: EducationGroupYear):
    if egy.is_training() or egy.education_group_type.name in MiniTrainingType.to_postpone():
        return egy.verbose
    return egy.partial_acronym
