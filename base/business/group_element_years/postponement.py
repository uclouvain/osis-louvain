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
from django.utils.translation import ugettext as _

from base.business.education_groups.postponement import duplicate_education_group_year
from base.business.utils.model import update_related_object
from base.models.academic_year import starting_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import MiniTrainingType


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
        self.instance_n1 = self.get_instance_n1(self.instance)

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

        if next_instance.groupelementyear_set.exists():
            raise NotPostponeError(_("The content has already been postponed."))

        return next_instance

    @transaction.atomic
    def postpone(self, instance=None):
        """
        We'll postpone first the group_element_years of the root,
        after that, we'll postponement recursively all the child branches and child leafs.
        """
        if not instance:
            instance = self.instance
            next_instance = self.instance_n1
        else:
            next_instance = self.get_instance_n1(instance)

        for gr in instance.groupelementyear_set.all():
            new_gr = update_related_object(gr, "parent", next_instance)
            if new_gr.child_leaf:
                self._postpone_child_leaf(gr, new_gr)
            else:
                self._postpone_child_branch(gr, new_gr)

            self.result.append(new_gr)

        return next_instance

    @staticmethod
    def _postpone_child_leaf(old_gr, new_gr):
        """
        During the postponement of the learning units, we will take the next learning unit year
        but if it does not exist for N+1, we will attach the current instance .
        """
        old_luy = old_gr.child_leaf
        new_luy = old_luy.get_learning_unit_next_year() or old_luy
        new_gr.child_leaf = new_luy
        return new_gr.save()

    def _postpone_child_branch(self, old_gr, new_gr):
        """
        Unlike child leaf, the child branch must also be postponed (recursively)
        """
        old_egy = old_gr.child_branch
        new_egy = old_egy.next_year()

        if not new_egy:
            new_egy = duplicate_education_group_year(old_egy, self.next_academic_year)
            self.postpone(old_egy)

        new_gr.child_branch = new_egy
        return new_gr.save()
