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
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class PersonAdmin(admin.ModelAdmin):
    list_display = ('first_name' , 'middle_name', 'last_name', 'username', 'email', 'gender', 'birth_date', 'global_id',
                    'national_id', 'changed')
    search_fields = ['first_name', 'middle_name', 'last_name', 'user__username', 'email']
    fieldsets = ((None, {'fields': ('user', 'global_id', 'national_id', 'gender', 'birth_date', 'first_name',
                                    'middle_name', 'last_name', 'email', 'phone', 'phone_mobile', 'language')}),)
    raw_id_fields = ('user',)


class Person(models.Model):
    GENDER_CHOICES = (
        ('F', _('female')),
        ('M', _('male')),
        ('U', _('unknown')))

    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    global_id = models.CharField(max_length=10, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=GENDER_CHOICES, default='U')
    national_id = models.CharField(max_length=25, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    phone_mobile = models.CharField(max_length=30, blank=True, null=True)
    language = models.CharField(max_length=30, null=True, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    birth_date = models.DateField(blank=True, null=True)

    def username(self):
        if self.user is None:
            return None
        return self.user.username

    def __str__(self):
        first_name = ""
        middle_name = ""
        last_name = ""
        if self.first_name :
            first_name = self.first_name
        if self.middle_name :
            middle_name = self.middle_name
        if self.last_name :
            last_name = self.last_name + ","

        return u"%s %s %s" % (last_name.upper(), first_name, middle_name)


def find_by_id(person_id):
    return Person.objects.get(id=person_id)


def find_by_user(user):
    person = Person.objects.filter(user=user).first()
    return person


def change_language(user, new_language):
    if new_language:
        person = Person.objects.get(user=user)
        person.language = new_language
        person.save()


def find_by_global_id(global_id):
    return Person.objects.filter(global_id=global_id).first()
