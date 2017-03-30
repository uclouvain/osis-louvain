##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from dissertation.models.dissertation_role import get_promoteur_by_dissertation
from dissertation.utils.emails_dissert import *
from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from base.models import offer_year, student
from . import proposition_dissertation
from . import offer_proposition
from . import dissertation_location


class DissertationAdmin(SerializableModelAdmin):
    list_display = ('uuid', 'title', 'author', 'status', 'active', 'proposition_dissertation', 'modification_date')
    raw_id_fields = ('author', 'offer_year_start', 'proposition_dissertation', 'location')
    search_fields = ('uuid', 'title', 'author__person__last_name', 'author__person__first_name',
                     'proposition_dissertation__title', 'proposition_dissertation__author__person__last_name',
                     'proposition_dissertation__author__person__first_name')

STATUS_CHOICES = (
    ('DRAFT', _('draft')),
    ('DIR_SUBMIT', _('submitted_to_director')),
    ('DIR_OK', _('accepted_by_director')),
    ('DIR_KO', _('refused_by_director')),
    ('COM_SUBMIT', _('submitted_to_commission')),
    ('COM_OK', _('accepted_by_commission')),
    ('COM_KO', _('refused_by_commission')),
    ('EVA_SUBMIT', _('submitted_to_first_year_evaluation')),
    ('EVA_OK', _('accepted_by_first_year_evaluation')),
    ('EVA_KO', _('refused_by_first_year_evaluation')),
    ('TO_RECEIVE', _('to_be_received')),
    ('TO_DEFEND', _('to_be_defended')),
    ('DEFENDED', _('defended')),
    ('ENDED', _('ended')),
    ('ENDED_WIN', _('ended_win')),
    ('ENDED_LOS', _('ended_los')),
)

DEFEND_PERIODE_CHOICES = (
    ('UNDEFINED', _('undefined')),
    ('JANUARY', _('january')),
    ('JUNE', _('june')),
    ('SEPTEMBER', _('september')),
)


class Dissertation(SerializableModel):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(student.Student)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='DRAFT')
    defend_periode = models.CharField(max_length=12, choices=DEFEND_PERIODE_CHOICES, blank=True, null=True)
    defend_year = models.IntegerField(blank=True, null=True)
    offer_year_start = models.ForeignKey(offer_year.OfferYear)
    proposition_dissertation = models.ForeignKey(proposition_dissertation.PropositionDissertation)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    modification_date = models.DateTimeField(auto_now=True)
    location = models.ForeignKey(dissertation_location.DissertationLocation, blank=True, null=True)

    def __str__(self):
        return self.title

    def deactivate(self):
        self.active = False
        self.save()

    def set_status(self, status):
        self.status = status
        self.save()

    def go_forward(self):

        next_status = get_next_status(self, "go_forward")
        if self.status == 'TO_RECEIVE' and next_status == 'TO_DEFEND':
            send_mail_dissert_acknowledgement(self)
        if (self.status == 'DRAFT' or self.status == 'DIR_KO')and next_status == 'DIR_SUBMIT':
            send_mail_to_teacher_new_dissert(self)
        self.set_status(next_status)

    def accept(self):
        next_status = get_next_status(self, "accept")
        if self.status == 'DIR_SUBMIT':
            send_mail_dissert_accepted_by_teacher(self)
        if self.status == 'COM_SUBMIT':
            send_mail_dissert_accepted_by_com(self)
        self.set_status(next_status)

    def refuse(self):
        next_status = get_next_status(self, "refuse")
        if self.status == 'DIR_SUBMIT':
            send_mail_dissert_refused_by_teacher(self)
        if self.status == 'COM_SUBMIT':
            send_mail_dissert_refused_by_com_to_student(self)
            send_mail_dissert_refused_by_com_to_teacher(self)
        self.set_status(next_status)

    class Meta:
        ordering = ["author__person__last_name", "author__person__middle_name", "author__person__first_name", "title"]


def search(terms=None, active=True):
    queryset = Dissertation.objects.all()
    if terms:
        queryset = queryset.filter(
            Q(author__person__first_name__icontains=terms) |
            Q(author__person__middle_name__icontains=terms) |
            Q(author__person__last_name__icontains=terms) |
            Q(description__icontains=terms) |
            Q(proposition_dissertation__title__icontains=terms) |
            Q(proposition_dissertation__author__person__first_name__icontains=terms) |
            Q(proposition_dissertation__author__person__middle_name__icontains=terms) |
            Q(proposition_dissertation__author__person__last_name__icontains=terms) |
            Q(status__icontains=terms) |
            Q(title__icontains=terms)
        ).filter(active=active).distinct()
    return queryset


def search_by_proposition_author(terms=None, active=True, proposition_author=None):
    return search(terms=terms, active=active).filter(proposition_dissertation__author=proposition_author)


def search_by_offer(offers):
    return Dissertation.objects.filter(offer_year_start__offer__in=offers)


def search_by_offer_and_status(offers, status):
    return search_by_offer(offers).filter(status=status)


def count_by_proposition(prop_dissert):
    return Dissertation.objects.filter(active=True) \
        .filter(proposition_dissertation=prop_dissert) \
        .exclude(status='DRAFT') \
        .count()


def get_next_status(dissert, operation):
    if operation == "go_forward":
        if dissert.status == 'DRAFT' or dissert.status == 'DIR_KO':
            return 'DIR_SUBMIT'

        elif dissert.status == 'TO_RECEIVE':
            return 'TO_DEFEND'

        elif dissert.status == 'TO_DEFEND':
            return 'DEFENDED'
        else:
            return dissert.status

    elif operation == "accept":

        offer_prop = offer_proposition.get_by_offer(dissert.offer_year_start.offer)

        if offer_prop.validation_commission_exists and dissert.status == 'DIR_SUBMIT':

            return 'COM_SUBMIT'

        elif offer_prop.evaluation_first_year and (dissert.status == 'DIR_SUBMIT' or
                                                   dissert.status == 'COM_SUBMIT' or
                                                   dissert.status == 'COM_KO'):
            return 'EVA_SUBMIT'

        elif dissert.status == 'EVA_SUBMIT' or dissert.status == 'EVA_KO':
            return 'TO_RECEIVE'

        elif dissert.status == 'DEFENDED':
            return 'ENDED_WIN'

        else:
            return 'TO_RECEIVE'

    elif operation == "refuse":
        if dissert.status == 'DIR_SUBMIT':
            return 'DIR_KO'

        elif dissert.status == 'COM_SUBMIT':
            return 'COM_KO'

        elif dissert.status == 'EVA_SUBMIT':
            return 'EVA_KO'

        elif dissert.status == 'DEFENDED':
            return 'ENDED_LOS'
        else:
            return dissert.status

    else:
        return dissert.status


def find_by_id(dissertation_id):
    return Dissertation.objects.get(pk=dissertation_id)
