##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AcademicAssistant(models.Model):
    PHD_INSCRIPTION_CHOICES = (
        ('YES', _('Yes')),
        ('NO', _('No')),
        ('IN_PROGRESS', _('In progress')))

    person = models.ForeignKey('base.Person')
    supervisor = models.ForeignKey('Reviewer', null=True)
    thesis_title = models.CharField(max_length=255, null=True, blank=True)
    phd_inscription_date = models.DateField(null=True, blank=True)
    confirmation_test_date = models.DateField(null=True, blank=True)
    thesis_date = models.DateField(null=True, blank=True)
    expected_phd_date = models.DateField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    inscription = models.CharField(max_length=12, choices=PHD_INSCRIPTION_CHOICES, default='YES')
    
    def __str__(self):
        return u"%s %s" % (self.person.first_name, self.person.last_name)


def find_by_id(assistant_id):
    return AcademicAssistant.objects.get(id=assistant_id)  


def find_by_person(person):
    return AcademicAssistant.objects.get(person=person)


def is_supervisor(person):
    return AcademicAssistant.objects.filter(supervisor=person).first()
