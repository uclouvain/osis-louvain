############################################################################
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
############################################################################
from django.db import Error, transaction
from django.utils.translation import gettext as _

from base.business.education_groups.postponement import duplicate_education_group_year
from base.business.utils.model import update_related_object
from base.models.academic_year import starting_academic_year
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import MiniTrainingType
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite import Prerequisite
from base.models.prerequisite_item import PrerequisiteItem


class CopyWarning(Warning):
    pass


class ReuseOldLearningUnitYearWarning(CopyWarning):
    def __init__(self, obj: LearningUnitYear, academic_year):
        self.learning_unit_year = obj
        self.academic_year = academic_year

    def __str__(self):
        return _("The learning unit %(learning_unit_year)s does not exist in %(academic_year)s.") % {
            "learning_unit_year": self.learning_unit_year.acronym,
            "academic_year": self.academic_year
        }


class PrerequisiteItemWarning(CopyWarning):
    def __init__(self, prerequisite: Prerequisite, item: PrerequisiteItem, academic_year):
        self.prerequisite = prerequisite
        self.item = item
        self.academic_year = academic_year

    def __str__(self):
        return _("The postponed learning unit %(learning_unit)s has a "
                 "prerequisite %(item)s which does not exist in %(academic_year)s.") % {
                   "learning_unit": self.prerequisite.learning_unit_year.acronym,
                   "item": self.item.learning_unit.acronym,
                   "academic_year": self.academic_year
               }


class EducationGroupEndYearWarning(CopyWarning):
    def __init__(self, obj: EducationGroupYear, academic_year):
        self.education_group_year = obj
        self.academic_year = academic_year

    def __str__(self):
        return _("%(education_group_year)s is closed in %(end_year)s, there is no more link to this "
                 "element in %(academic_year)s.") % {
                   "education_group_year": self.education_group_year.acronym,
                   "end_year": self.education_group_year.education_group.end_year,
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
        self.next_academic_year = self.current_year.next()

        self.check_instance()

        self.result = []
        self.warnings = []
        self.instance_n1 = self.get_instance_n1(self.instance)

        self.postponed_luy = []

    def check_instance(self):
        if self.instance.is_training():
            pass
        elif self.instance.education_group_type.name in MiniTrainingType.to_postpone():
            pass
        else:
            raise NotPostponeError(_('You are not allowed to copy the content of this kind of education group.'))

        if self.instance.academic_year.year < self.current_year.year:
            raise NotPostponeError(_("You are not allowed to postpone this training in the past."))
        if self.instance.academic_year.year > self.current_year.year:
            raise NotPostponeError(_("You are not allowed to postpone this training in the future."))

        end_year = self.instance.education_group.end_year
        if end_year and end_year < self.next_academic_year.year:
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
        after that, we'll postponement recursively all the child branches and child leafs.
        """

        for gr in instance.groupelementyear_set.select_related('child_branch__academic_year',
                                                               'child_branch__education_group'):
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
            new_gr = update_related_object(gr, "parent", next_instance)

        if new_gr.child_leaf:
            return self._postpone_child_leaf(gr, new_gr)
        return self._postpone_child_branch(gr, new_gr)

    def _post_postponement(self):
        # Postpone the prerequisite only at the end to be sure to have all learning units and education groups
        for old_luy, new_luy in self.postponed_luy:
            self._postpone_prerequisite(old_luy, new_luy)

    def _postpone_child_leaf(self, old_gr, new_gr):
        """
        During the postponement of the learning units, we will take the next learning unit year
        but if it does not exist for N+1, we will attach the current instance.
        """
        old_luy = old_gr.child_leaf
        new_luy = old_luy.get_learning_unit_next_year()
        if not new_luy:
            new_luy = old_luy
            self.warnings.append(ReuseOldLearningUnitYearWarning(old_luy, self.next_academic_year))

        else:
            # postponed_luy will be used for prerequisites. But if we use the old learning unit, we do not need it.
            self.postponed_luy.append((old_luy, new_luy))

        new_gr.child_leaf = new_luy
        new_gr.save()
        return new_gr

    def _postpone_child_branch(self, old_gr: GroupElementYear, new_gr: GroupElementYear) -> GroupElementYear:
        """
        Unlike child leaf, the child branch must be postponed (recursively)
        """
        old_egy = old_gr.child_branch
        new_egy = old_egy.next_year()

        if new_egy:
            # In the case of technical group, we have to postpone the content even if the group already
            # exists in N+1
            relationship = AuthorizedRelationship.objects.filter(
                parent_type=new_gr.parent.education_group_type,
                child_type=new_egy.education_group_type
            ).first()
            if relationship and relationship.min_count_authorized > 0 and not new_egy.groupelementyear_set.all():
                # We postpone data only if the mandatory group is empty.
                self._postpone(old_egy, new_egy)

        else:
            # If the education group does not exists for the next year, we have to postpone.
            new_egy = self._duplication_education_group_year(old_egy)

        if new_egy:
            new_gr.child_branch = new_egy
            new_gr.save()

        return new_gr

    def _duplication_education_group_year(self, old_egy: EducationGroupYear):
        if old_egy.education_group_type.category != Categories.GROUP.name:
            if old_egy.education_group.end_year and old_egy.education_group.end_year < self.next_academic_year.year:
                self.warnings.append(EducationGroupEndYearWarning(old_egy, self.next_academic_year))
                return None

        new_egy = duplicate_education_group_year(old_egy, self.next_academic_year)

        # Copy its children
        self._postpone(old_egy, new_egy)

        return new_egy

    def _check_if_already_postponed(self, education_group_year):
        """
        Determine if the content has already been postponed.

        First we have to check the progeny of the education group (! recursive search )
        After verify if all nodes have an authorized relationship with a min count to 1 or a learning unit.
        """
        for gr in education_group_year.groupelementyear_set.all():
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
            if not item.learning_unit.learningunityear_set.filter(academic_year=self.next_academic_year):
                self.warnings.append(PrerequisiteItemWarning(old_prerequisite, item, self.next_academic_year))
                result = False
        return result
