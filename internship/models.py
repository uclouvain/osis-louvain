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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _
import urllib.request
import unicodedata
from xml.dom import minidom
import logging


class InternshipOffer(models.Model):
    organization        = models.ForeignKey('internship.Organization')
    speciality          = models.ForeignKey('internship.InternshipSpeciality',null=True)
    title = models.CharField(max_length=255)
    maximum_enrollments = models.IntegerField()
    internship_master   = models.ForeignKey('internship.InternshipMaster', null=True)
    selectable          = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @staticmethod
    def find_internships():
        return InternshipOffer.objects.filter(speciality__mandatory=1)\
            .select_related("organization", "speciality").order_by('speciality__acronym', 'speciality__name', 'organization__reference')

    @staticmethod
    def find_non_mandatory_internships(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipOffer.objects.filter(**kwargs).filter(speciality__mandatory=0) \
            .select_related("organization", "speciality").order_by('speciality__acronym', 'speciality__name', 'organization__reference')
        return queryset

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipOffer.objects.filter(**kwargs) \
            .select_related("organization", "speciality").order_by('speciality__acronym', 'speciality__name', 'organization__reference')
        return queryset

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

    class Meta:
        permissions = (
            ("is_internship_manager", "Is Internship Manager"),
            ("can_access_internship","Can access internships"),
        )


class InternshipEnrollment(models.Model):
    student = models.ForeignKey('base.student')
    internship_offer = models.ForeignKey(InternshipOffer)
    place = models.ForeignKey('internship.Organization')
    period = models.ForeignKey('internship.Period')

    def __str__(self):
        return u"%s" % self.learning_unit_enrollment.student

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipEnrollment.objects.filter(**kwargs).select_related("student","internship_offer", "place", "period")
        return queryset


class InternshipMaster(models.Model):
    first_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    civility = models.CharField(max_length=50, blank=True, null=True)
    sexe = models.CharField(max_length=50, blank=True, null=True)
    speciality = models.CharField(max_length=50, blank=True, null=True)
    organization = models.ForeignKey('internship.Organization', null=True)
    birth_date = models.DateField(blank=True, null=True)
    email_professionnal = models.CharField(max_length=255, blank=True, null=True)
    email_private = models.CharField(max_length=255, blank=True, null=True)
    phone_professionnal = models.CharField(max_length=50, blank=True, null=True)
    phone_private = models.CharField(max_length=50, blank=True, null=True)
    cremec = models.CharField(max_length=50, blank=True, null=True)
    date_start_activity = models.DateField(blank=True, null=True)
    date_end_activity = models.DateField(blank=True, null=True)

    @staticmethod
    def find_masters():
        return InternshipMaster.objects.all().select_related("organization").order_by("last_name", "first_name")

    def __str__(self):
        return u"%s %s" % (self.civility, self.last_name)

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipMaster.objects.filter(**kwargs).select_related("organization").order_by("last_name", "first_name")
        return queryset


class InternshipChoice(models.Model):
    student             = models.ForeignKey('base.Student')
    organization        = models.ForeignKey('internship.Organization')
    speciality          = models.ForeignKey('internship.InternshipSpeciality',null=True)
    choice              = models.IntegerField()
    internship_choice   = models.IntegerField(default=0)
    priority            = models.BooleanField()

    @staticmethod
    def find_by_all_student():
        all = InternshipChoice.objects.all().distinct('student').select_related("student","organization","speciality")
        return all

    @staticmethod
    def find_by_student(s_student):
        internships = InternshipChoice.objects.filter(student = s_student).select_related("student","organization","speciality").order_by('choice')
        return internships

    @staticmethod
    def find_by_student_desc(s_student):
        internships = InternshipChoice.objects.filter(student = s_student).select_related("student","organization","speciality").order_by('-choice')
        return internships

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipChoice.objects.filter(**kwargs).select_related("student","organization","speciality").order_by('choice')
        return queryset

    @staticmethod
    def search_other_choices(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipChoice.objects.filter(**kwargs).select_related("student","organization","speciality").order_by('choice')
        queryset = queryset.exclude(choice=1)
        return queryset


class Period(models.Model):
    name = models.CharField(max_length=255)
    date_start = models.DateField(blank=False)
    date_end = models.DateField(blank=False)

    def __str__(self):
        return u"%s" % (self.name)

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = Period.objects.filter(**kwargs).select_related().order_by("date_start")
        return queryset

    @staticmethod
    def find_by_id(period_id):
        return Period.objects.get(pk=period_id)


class PeriodInternshipPlaces(models.Model):
    period = models.ForeignKey('internship.Period')
    internship = models.ForeignKey('internship.InternshipOffer')
    number_places = models.IntegerField(blank=None, null=False)

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = PeriodInternshipPlaces.objects.filter(**kwargs).select_related("period", "internship")
        return queryset

    @staticmethod
    def find_by_id(id):
        return PeriodInternshipPlaces.objects.get(pk=id)


class InternshipSpeciality(models.Model):
    learning_unit = models.ForeignKey('base.LearningUnit')
    name = models.CharField(max_length=125, blank=False, null=False)
    acronym = models.CharField(max_length=125, blank=False, null=False)
    mandatory = models.BooleanField(default=False)
    order_postion = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipSpeciality.objects.filter(**kwargs).select_related("learning_unit").order_by('acronym', 'name')
        return queryset

    @staticmethod
    def search_order_by_position(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipSpeciality.objects.filter(**kwargs).select_related("learning_unit").order_by('order_postion')
        return queryset

    @staticmethod
    def find_all():
        return InternshipSpeciality.objects.all().select_related("learning_unit").order_by('acronym', 'name')

    @staticmethod
    def find_by_id(speciality_id):
        return InternshipSpeciality.objects.get(pk=speciality_id)

    @staticmethod
    def find_non_mandatory():
        return InternshipSpeciality.objects.filter(mandatory=False).select_related("learning_unit").order_by('acronym', 'name')


class Organization(models.Model):
    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=15, blank=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    reference = models.CharField(max_length=30, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True, default="service partner")

    def __str__(self):
        return self.name

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = Organization.objects.filter(**kwargs).select_related()
        return queryset

    @staticmethod
    def find_by_id(organization_id):
        return Organization.objects.get(pk=organization_id)

    def save(self, *args, **kwargs):
        self.acronym = self.name[:14]
        super(Organization, self).save(*args, **kwargs)


class OrganizationAddress(models.Model):
    organization = models.ForeignKey('Organization')
    label = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    country = models.CharField(max_length=255)

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = OrganizationAddress.objects.filter(**kwargs).select_related("organization")
        return queryset

    @staticmethod
    def find_by_id(organization_address_id):
        return OrganizationAddress.objects.get(pk=organization_address_id)

    def save(self, *args, **kwargs):
        has_organization = False
        try:
            has_organization = (self.organization is not None)
        except Exception:
            self.organization = Organization.objects.latest('id')

        self.label = "Addr"+self.organization.name[:14]
        super(OrganizationAddress, self).save(*args, **kwargs)

    def geocode(addr):
        lat_long = [None]*2
        # Transform the address for a good url and delete all accents
        addr = addr.replace('\n','')
        addr = addr.replace(" ", "+")
        addr = addr.replace("'", "\'")
        addr = addr.replace("n°", "")
        addr = addr.replace("n °", "")
        addr = addr.replace("Œ", "Oe")
        addr = addr.encode('utf8','replace').decode('utf8')
        addr = OrganizationAddress.strip_accents(addr)
        # get the complete url
        url = ''.join(['https://maps.googleapis.com/maps/api/geocode/xml?address=', addr, '&key=AIzaSyCWeZdraxzqRTMxXxbXY3bncaD6Ijq_EvE'])
        logging.info(url)

        # using urllib get the xml
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')

        # Parse the xml to have the latitude and longitude of the address
        xmldoc = minidom.parseString(data)
        status = xmldoc.getElementsByTagName('status')[0].firstChild.data
        if status == "OK":
            lat = xmldoc.getElementsByTagName('location')
            for l in lat:
                c = l.getElementsByTagName('lat')[0].firstChild.data
                d = l.getElementsByTagName('lng')[0].firstChild.data
                lat_long[0] = c
                lat_long[1] = d
        # return the value
        return lat_long

    def strip_accents(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                       if unicodedata.category(c) != 'Mn')

    def find_latitude_longitude(infos):
        #for each data in the infos, check if the lat exist
        for data in infos:
            if data.latitude is None :
                #if it exist, compile the address with the location / postal / city / country
                address = data.location + " " + data.postal_code + " " \
                          + data.city + " " + data.country
                #Compute the geolocalisation
                address_lat_long = OrganizationAddress.geocode(address)
                #if the geolac is fing put the data, if not put fake data
                if address_lat_long[0]:
                    data.latitude = address_lat_long[0]
                    data.longitude = address_lat_long[1]
                else :
                    address = data.location + " " + data.postal_code + " " \
                              + data.country
                    #Compute the geolocalisation
                    address_lat_long = OrganizationAddress.geocode(address)
                    #if the geolac is fing put the data, if not put fake data
                    if address_lat_long[0]:
                        data.latitude = address_lat_long[0]
                        data.longitude = address_lat_long[1]
                    else :
                        data.latitude = 999
                        data.longitude = 999
                #save the data
                data.save()


class InternshipStudentInformation(models.Model):
    person = models.ForeignKey('base.Person')
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_mobile = models.CharField(max_length=100, blank=True, null=True)

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipStudentInformation.objects.filter(**kwargs).select_related("person")
        return queryset

    @staticmethod
    def find_all():
        return InternshipStudentInformation.objects.all().select_related("person").order_by('person__last_name', 'person__first_name')

    @staticmethod
    def find_by_person(person):
        try:
            return InternshipStudentInformation.objects.get(person=person).select_related("person")
        except ObjectDoesNotExist:
            return None


class InternshipStudentAffectationStat(models.Model):
    student = models.ForeignKey('base.Student')
    organization = models.ForeignKey('internship.Organization')
    speciality = models.ForeignKey('internship.InternshipSpeciality')
    period = models.ForeignKey('internship.Period')
    choice = models.CharField(max_length=1, blank=False, null=False, default='0')
    cost = models.IntegerField(blank=False, null=False)
    consecutive_month = models.BooleanField(default=False, null=False)
    type_of_internship = models.CharField(max_length=1, blank=False, null=False, default='N')

    @staticmethod
    def search(**kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        queryset = InternshipStudentAffectationStat.objects.filter(**kwargs)\
            .select_related("student__person", "organization", "speciality", "period")\
            .order_by("student__person__last_name","student__person__first_name", "period__date_start")
        return queryset

    @staticmethod
    def find_by_id(affectation_id):
        return InternshipStudentAffectationStat.objects.get(pk=affectation_id)
