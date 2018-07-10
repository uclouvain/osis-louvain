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

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from base.business.learning_units import perms as business_perms
from base.models import learning_unit_year, proposal_learning_unit
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit


class PermissionDecorator:
    """
    This class creates generic decorators to check if the user is allowed to access the data

    Decorators need 3 attributes :
        - permission_method : method to call to validate the permission
        - argument_name : the argument name to get the object to validate
        - argument_instance : the object type to validate
        - permission_denied_msg : if we want to add a message if permission denied

    """
    def __init__(self, permission_method, argument_name, argument_instance, permission_denied_msg=None):
        self.permission_method = permission_method
        self.permission_denied_message = permission_denied_msg or "The user can not access this page"
        self.argument_instance = argument_instance
        self.argument_name = argument_name

    def __call__(self, view_func):
        @login_required
        def wrapped_f(*args, **kwargs):
            # Retrieve objects
            person = get_object_or_404(Person, user=args[0].user)
            obj = get_object_or_404(self.argument_instance, pk=kwargs.get(self.argument_name))

            # Check permission
            if not self.permission_method(obj, person):
                raise PermissionDenied(self.permission_denied_message)

            # Call the view
            return view_func(*args, **kwargs)

        return wrapped_f


def can_delete_learning_unit_year(view_func):
    def f_can_delete_learning_unit_year(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_to_delete_learning_unit_year(learn_unit_year, pers):
            raise PermissionDenied
        return view_func(request, learning_unit_year_id)
    return f_can_delete_learning_unit_year


def can_create_partim(view_func):
    def f_can_create_partim(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_to_create_partim(learn_unit_year, pers):
            raise PermissionDenied
        return view_func(request, learning_unit_year_id)
    return f_can_create_partim


def can_create_modification_proposal(view_func):
    def f_can_perform_modification_proposal(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_to_create_modification_proposal(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year not eligible for proposal or user has not sufficient rights.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_modification_proposal


def can_edit_learning_unit_proposal(view_func):
    def f_can_edit_learning_unit_proposal(request, learning_unit_year_id):
        proposal = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)

        if not business_perms.is_eligible_to_edit_proposal(proposal, pers):
            raise PermissionDenied("User has not sufficient rights to edit proposal.")
        return view_func(request, learning_unit_year_id)
    return f_can_edit_learning_unit_proposal


def can_perform_cancel_proposal(view_func):
    def f_can_perform_cancel_proposal(request, learning_unit_year_id):
        learning_unit_proposal = get_object_or_404(ProposalLearningUnit, learning_unit_year__id=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_for_cancel_of_proposal(learning_unit_proposal, pers):
            raise PermissionDenied("Learning unit proposal cannot be cancelled.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_cancel_proposal


def can_perform_end_date_modification(view_func):
    def f_can_perform_end_date_modification(request, learning_unit_year_id):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_for_modification_end_date(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year date is not editable or user has not sufficient rights.")
        return view_func(request, learning_unit_year_id)
    return f_can_perform_end_date_modification


def can_perform_learning_unit_modification(view_func):
    def f_can_perform_learning_unit_modification(request, learning_unit_year_id, *args, **kwargs):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.is_eligible_for_modification(learn_unit_year, pers):
            raise PermissionDenied("Learning unit year cannot be modified.")
        return view_func(request, learning_unit_year_id, *args, **kwargs)
    return f_can_perform_learning_unit_modification


def can_update_learning_achievement(view_func):
    def f_can_update_learning_achievement(request, learning_unit_year_id, *args, **kwargs):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.can_update_learning_achievement(learn_unit_year, pers):
            raise PermissionDenied("The user is not linked to the learning unit year")
        return view_func(request, learning_unit_year_id, *args, **kwargs)
    return f_can_update_learning_achievement


def can_edit_summary_locked_field(view_func):
    def f_can_update_learning_achievement(request, learning_unit_year_id, *args, **kwargs):
        learn_unit_year = get_object_or_404(learning_unit_year.LearningUnitYear, pk=learning_unit_year_id)
        pers = get_object_or_404(Person, user=request.user)
        if not business_perms.can_edit_summary_locked_field(learn_unit_year, pers):
            raise PermissionDenied("The user cannot edit summary locked field")
        return view_func(request, learning_unit_year_id, *args, **kwargs)
    return f_can_update_learning_achievement
