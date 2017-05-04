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
from django import forms
from django.forms import ModelForm
from base import models as mdl
from dissertation.models.adviser import Adviser
from dissertation.models.dissertation import Dissertation
from dissertation.models.offer_proposition import OfferProposition
from dissertation.models.proposition_dissertation import PropositionDissertation
from dissertation.models.proposition_role import PropositionRole
from dissertation.models.dissertation_role import DissertationRole
from dissertation.models.dissertation_update import DissertationUpdate


class AdviserForm(ModelForm):
    class Meta:
        model = Adviser
        fields = ('available_by_email', 'available_by_phone', 'available_at_office', 'comment')


class AddAdviserForm(ModelForm):
    class Meta:
        model = Adviser
        fields = ('person',)


class DissertationForm(ModelForm):
    class Meta:
        model = Dissertation
        fields = ('title', 'author', 'offer_year_start', 'proposition_dissertation', 'description')


class PropositionDissertationForm(ModelForm):
    class Meta:
        model = PropositionDissertation
        fields = ('author', 'visibility', 'title', 'description', 'type', 'level', 'collaboration',
                  'max_number_student')
        widgets = {'author': forms.HiddenInput()}


class PropositionRoleForm(ModelForm):
    class Meta:
        model = PropositionRole
        fields = ('proposition_dissertation', 'status', 'adviser')
        widgets = {'proposition_dissertation': forms.HiddenInput()}


class ManagerAddAdviserPreForm(ModelForm):
    class Meta:
        model = mdl.person.Person
        fields = ('email', )


class ManagerAddAdviserPerson(ModelForm):
    class Meta:
        model = mdl.person.Person
        fields = ('email', 'last_name', 'first_name', 'phone', 'phone_mobile')


class ManagerAddAdviserForm(ModelForm):
    class Meta:
        model = Adviser
        fields = ('person', 'available_by_email', 'available_by_phone', 'available_at_office', 'comment')


class ManagerAdviserForm(ModelForm):
    class Meta:
        model = Adviser
        fields = ('available_by_email', 'available_by_phone', 'available_at_office', 'comment')


class ManagerDissertationForm(ModelForm):
    class Meta:
        model = Dissertation
        fields = ('title', 'author', 'offer_year_start', 'proposition_dissertation', 'description',
                  'defend_year', 'defend_periode', 'location')


class ManagerDissertationEditForm(ModelForm):
    class Meta:
        model = Dissertation
        fields = ('title', 'author', 'offer_year_start', 'proposition_dissertation', 'description', 'defend_year',
                  'defend_periode', 'location')


class ManagerDissertationRoleForm(ModelForm):
    class Meta:
        model = DissertationRole
        fields = ('dissertation', 'status', 'adviser')
        widgets = {'dissertation': forms.HiddenInput()}


class ManagerOfferPropositionForm(ModelForm):
    class Meta:
        model = OfferProposition
        fields = ('offer', 'acronym', 'adviser_can_suggest_reader', 'validation_commission_exists',
                  'student_can_manage_readers', 'evaluation_first_year', 'start_visibility_proposition',
                  'end_visibility_proposition', 'start_visibility_dissertation', 'end_visibility_dissertation',
                  'start_jury_visibility', 'end_jury_visibility', 'start_edit_title', 'end_edit_title')
        widgets = {'offer': forms.HiddenInput(), 'acronym': forms.HiddenInput()}


class ManagerPropositionDissertationForm(ModelForm):
    class Meta:
        model = PropositionDissertation
        fields = ('author', 'visibility', 'title', 'description', 'type', 'level', 'collaboration',
                  'max_number_student')


class ManagerPropositionDissertationEditForm(ModelForm):
    class Meta:
        model = PropositionDissertation
        fields = (
            'visibility', 'title', 'description', 'type', 'level', 'collaboration', 'max_number_student')


class ManagerPropositionRoleForm(ModelForm):
    class Meta:
        model = PropositionRole
        fields = ('proposition_dissertation', 'status', 'adviser')
        widgets = {'proposition_dissertation': forms.HiddenInput()}


class ManagerDissertationUpdateForm(ModelForm):
    class Meta:
        model = DissertationUpdate
        fields = ('justification',)
