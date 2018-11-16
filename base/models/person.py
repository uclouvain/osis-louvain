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
from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q
from django.db.models import Value
from django.db.models.functions import Concat, Lower
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version import find_pedagogical_entities_version
from base.models.enums import person_source_type
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin, SerializableModelManager

CENTRAL_MANAGER_GROUP = "central_managers"
FACULTY_MANAGER_GROUP = "faculty_managers"


class PersonAdmin(SerializableModelAdmin):
    list_display = ('get_first_name', 'middle_name', 'last_name', 'username', 'email', 'gender', 'global_id',
                    'changed', 'source', 'employee')
    search_fields = ['first_name', 'middle_name', 'last_name', 'user__username', 'email', 'global_id']
    list_filter = ('gender', 'language')


class EmployeeManager(SerializableModelManager):
    def get_queryset(self):
        return super().get_queryset().filter(employee=True).order_by("last_name", "first_name")


class Person(SerializableModel):
    GENDER_CHOICES = (
        ('F', _('Female')),
        ('M', _('Male')),
        ('U', _('unknown')))

    objects = SerializableModelManager()
    employees = EmployeeManager()

    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    global_id = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=GENDER_CHOICES, default='U')
    first_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    phone_mobile = models.CharField(max_length=30, blank=True, null=True)
    language = models.CharField(max_length=30, null=True, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    birth_date = models.DateField(blank=True, null=True)
    source = models.CharField(max_length=25, blank=True, null=True, choices=person_source_type.CHOICES,
                              default=person_source_type.BASE)
    employee = models.BooleanField(default=False)

    def save(self, **kwargs):
        # When person is created by another application this rule can be applied.
        if hasattr(settings, 'INTERNAL_EMAIL_SUFFIX'):
            if settings.INTERNAL_EMAIL_SUFFIX.strip():
                # It limits the creation of person with external emails. The domain name is case insensitive.
                if self.source and self.source != person_source_type.BASE \
                               and settings.INTERNAL_EMAIL_SUFFIX in str(self.email).lower():
                    raise AttributeError('Invalid email for external person.')

        super(Person, self).save()

    def username(self):
        if self.user is None:
            return None
        return self.user.username

    def get_first_name(self):
        if self.first_name:
            return self.first_name
        elif self.user:
            return self.user.first_name
        else:
            return "-"

    def is_central_manager(self):
        return self.user.groups.filter(name=CENTRAL_MANAGER_GROUP).exists()

    def is_faculty_manager(self):
        return self.user.groups.filter(name=FACULTY_MANAGER_GROUP).exists()

    @property
    def full_name(self):
        return " ".join([self.last_name or "", self.first_name or ""]).strip()

    def __str__(self):
        return self.get_str(self.first_name, self.middle_name, self.last_name)

    @staticmethod
    def get_str(first_name, middle_name, last_name):
        return " ".join([
            ("{},".format(last_name) if last_name else "").upper(),
            first_name or "",
            middle_name or ""
        ]).strip()

    @cached_property
    def linked_entities(self):
        entities_id = set()
        for person_entity in self.personentity_set.all():
            entities_id |= person_entity.descendants

        return entities_id

    class Meta:
        permissions = (
            ("is_administrator", "Is administrator"),
            ("is_institution_administrator", "Is institution administrator "),
            ("can_edit_education_group_administrative_data", "Can edit education group administrative data"),
            ("can_manage_charge_repartition", "Can manage charge repartition"),
            ("can_manage_attribution", "Can manage attribution"),
        )

    def is_linked_to_entity_in_charge_of_learning_unit_year(self, learning_unit_year):
        if learning_unit_year.is_external():
            return self.is_attached_entity(learning_unit_year.externallearningunityear.requesting_entity)

        entities = Entity.objects.filter(
            entitycontaineryear__learning_container_year=learning_unit_year.learning_container_year,
            entitycontaineryear__type=REQUIREMENT_ENTITY
        )

        return self.is_attached_entities(entities)

    def is_attached_entities(self, entities):
        for entity in entities:
            if self.is_attached_entity(entity):
                return True
        return False

    def is_attached_entity(self, entity):
        if not isinstance(entity, Entity):
            raise ImproperlyConfigured("entity must be an instance of Entity.")

        return entity.id in self.linked_entities

    @cached_property
    def find_main_entities_version(self):
        return find_pedagogical_entities_version().filter(entity__in=self.linked_entities)


def find_by_id(person_id):
    try:
        return Person.objects.get(id=person_id)
    except Person.DoesNotExist:
        return None


def find_by_user(user):
    person = Person.objects.filter(user=user).first()
    return person


def get_user_interface_language(user):
    user_language = settings.LANGUAGE_CODE
    person = find_by_user(user)
    if person:
        user_language = person.language
    return user_language


def change_language(user, new_language):
    if new_language in (l[0] for l in settings.LANGUAGES):
        person = find_by_user(user)
        if person:
            person.language = new_language
            person.save()


def find_by_global_id(global_id):
    return Person.objects.filter(global_id=global_id).first() if global_id else None


def find_by_last_name_or_email(query):
    return Person.objects.filter(Q(email__icontains=query) | Q(last_name__icontains=query))


def search_by_email(email):
    return Person.objects.filter(email=email)


def count_by_email(email):
    return search_by_email(email).count()


# FIXME Returns queryset.none() in place of None
# Also reuse search method and filter by employee then
def search_employee(full_name):
    queryset = annotate_with_first_last_names()
    if full_name:
        return queryset.filter(employee=True)\
            .filter(Q(begin_by_first_name__iexact='{}'.format(full_name.lower())) |
                    Q(begin_by_last_name__iexact='{}'.format(full_name.lower())) |
                    Q(first_name__icontains=full_name) |
                    Q(last_name__icontains=full_name))
    return None


def search(full_name):
    queryset = annotate_with_first_last_names()
    if full_name:
        return queryset.filter(Q(begin_by_first_name__iexact='{}'.format(full_name.lower())) |
                               Q(begin_by_last_name__iexact='{}'.format(full_name.lower())) |
                               Q(first_name__icontains=full_name) |
                               Q(last_name__icontains=full_name))
    return None


def annotate_with_first_last_names():
    queryset = Person.objects.annotate(begin_by_first_name=Lower(Concat('first_name', Value(' '), 'last_name')))
    queryset = queryset.annotate(begin_by_last_name=Lower(Concat('last_name', Value(' '), 'first_name')))
    return queryset


def calculate_age(person):
    if person.birth_date is None:
        return None
    today = date.today()
    return today.year - person.birth_date.year - ((today.month, today.day) < (person.birth_date.month,
                                                                              person.birth_date.day))


def find_by_firstname_or_lastname(name):
    return Person.objects.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))


def is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person, raise_exception=False):
    return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)
