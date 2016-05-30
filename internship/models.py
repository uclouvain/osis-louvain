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


class InternshipOffer(models.Model):
    organization        = models.ForeignKey('internship.Organization')
    learning_unit_year = models.ForeignKey('base.LearningUnitYear')
    title = models.CharField(max_length=255)
    maximum_enrollments = models.IntegerField()

    def __str__(self):
        return self.title

    @staticmethod
    def find_internships():
        return InternshipOffer.objects.all()

    @staticmethod
    def find_interships_by_learning_unit_organization(learning_unit_year, organization):
        internships = InternshipOffer.objects.filter(learning_unit_year__title=learning_unit_year)\
                                            .filter(organization__name=organization)
        return internships

    @staticmethod
    def find_interships_by_learning_unit(learning_unit_year):
        internships = InternshipOffer.objects.filter(learning_unit_year__title=learning_unit_year)
        return internships

    @staticmethod
    def find_interships_by_organization(organization):
        internships = InternshipOffer.objects.filter(organization__name=organization)
        return internships

    @staticmethod
    def find_intership_by_id(id):
        internship = InternshipOffer.objects.all()
        for i in internship:
            if int(i.id) == int(id):
                return i

        internship = InternshipChoice.objects.all()
        for i in internship:
            if int(i.id) == int(id):
                return i

class InternshipEnrollment(models.Model):
    learning_unit_enrollment = models.ForeignKey('base.LearningUnitEnrollment')
    internship_offer = models.ForeignKey(InternshipOffer)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return u"%s" % self.learning_unit_enrollment.student


class InternshipMaster(models.Model):
    CIVILITY_CHOICE = (('PROFESSOR',_('Professor')),
                       ('DOCTOR',_('Doctor')))
    TYPE_CHOICE = (('SPECIALIST',_('Specialist')),
                   ('GENERALIST',_('Generalist')))
    SPECIALITY_CHOICE = (('INTERNAL_MEDICINE',_('Internal Medicine')),
                        ('SURGERY',_('Surgery')),
                        ('GYNEC_OBSTETRICS',_('Gynec-Obstetrics')),
                        ('PEDIATRICS',_('Pediatrics')),
                        ('EMERGENCY',_('Emergency')),
                        ('GERIATRICS',_('Geriatrics')))

    organization     = models.ForeignKey('internship.Organization')
    internship_offer = models.ForeignKey(InternshipOffer)
    person = models.ForeignKey('base.Person')
    reference = models.CharField(max_length=30, blank=True, null=True)
    civility = models.CharField(max_length=20, blank=True, null=True, choices=CIVILITY_CHOICE)
    type_mastery = models.CharField(max_length=20, blank=True, null=True, choices=TYPE_CHOICE)
    speciality = models.CharField(max_length=20, blank=True, null=True, choices=SPECIALITY_CHOICE)

    @staticmethod
    def find_masters():
        return InternshipMaster.objects.all()

    def __str__(self):
        return u"%s - %s" % (self.person, self.reference)

    @staticmethod
    def find_masters_by_speciality_and_organization(speciality, organization):
        masters = InternshipMaster.objects.filter(speciality=speciality)\
                                            .filter(organization__name=organization)
        return masters

    @staticmethod
    def find_masters_by_speciality(speciality):
        masters = InternshipMaster.objects.filter(speciality=speciality)
        return masters

    @staticmethod
    def find_masters_by_organization(organization):
        masters = InternshipMaster.objects.filter(organization__name=organization)
        return masters


class InternshipChoice(models.Model):
    student             = models.ForeignKey('base.Student')
    organization        = models.ForeignKey('internship.Organization')
    learning_unit_year  = models.ForeignKey('base.LearningUnitYear')
    choice              = models.IntegerField()

    @staticmethod
    def find_by_student(s_student):
        internships = InternshipChoice.objects.filter(student = s_student).order_by('choice')
        return internships

    @staticmethod
    def find_by_student_desc(s_student):
        internships = InternshipChoice.objects.filter(student = s_student).order_by('-choice')
        return internships

    @staticmethod
    def find_by(s_organization=None, s_learning_unit_year=None, s_organization_ref=None, s_choice=None):
        has_criteria = False
        queryset = InternshipChoice.objects

        if s_organization:
            queryset = queryset.filter(organization=s_organization)
            has_criteria = True

        if s_learning_unit_year:
            queryset = queryset.filter(learning_unit_year=s_learning_unit_year)
            has_criteria = True

        if s_organization_ref:
            queryset = queryset.filter(organization__reference=s_organization_ref).order_by('choice')
            has_criteria = True

        if s_choice:
            if s_choice == 1 :
                queryset = queryset.filter(choice=s_choice)
            else :
                queryset = queryset.exclude(choice=1)
            has_criteria = True
        if has_criteria:
            return queryset
        else:
            return None


class Organization(models.Model):
    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=15)
    website = models.URLField(max_length=255, blank=True, null=True)
    reference = models.CharField(max_length=30, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.name

    @staticmethod
    def find_by_id(organization_id):
        return Organization.objects.get(pk=organization_id)

    @staticmethod
    def search(acronym=None, name=None, reference=None):
        has_criteria = False
        queryset = Organization.objects

        if acronym:
            queryset = queryset.filter(acronym=acronym)
            has_criteria = True

        if name:
            queryset = queryset.filter(name=name)
            has_criteria = True

        if reference:
            queryset = queryset.filter(reference=reference)
            has_criteria = True

        if has_criteria:
            return queryset
        else:
            return None

    @staticmethod
    def find_all_order_by_reference():
        return Organization.objects.all().order_by('reference')


    @staticmethod
    def find_by_type(type=None, order_by=None):
        if order_by:
            queryset = Organization.objects.filter(type=type).order_by(*order_by)
        else:
            queryset = Organization.objects.filter(type=type)

        return queryset

class OrganizationAddress(models.Model):
    organization = models.ForeignKey('Organization')
    label = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)

    @staticmethod
    def find_by_organization(organization):
        return OrganizationAddress.objects.filter(organization=organization).order_by('label')


    @staticmethod
    def find_by_id(organization_address_id):
        return OrganizationAddress.objects.get(pk=organization_address_id)
