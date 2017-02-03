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
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl
from internship.models.internship_choice import InternshipChoice
from internship.models.internship_offer import InternshipOffer
from internship.models.internship_speciality import InternshipSpeciality
from internship.models.internship_student_affectation_stat import InternshipStudentAffectationStat
from internship.models.internship_student_information import InternshipStudentInformation
from internship.models.organization import Organization

from django.utils.translation import ugettext_lazy as _

from internship.models.period import Period
from internship.views.place import set_organization_address, sort_organizations

def set_number_choices(student_informations):
    """
        Function to set the variable number_choices for the student in the list
        to check if he has the right number of choice.
        Param :
            student_informations : the list of students present in InternshipStudentInformation
    """
    for si in student_informations:
        student = mdl.student.find_by_person(si.person)
        choices = InternshipChoice.find_by_student(student)
        si.number_choices = len(choices)
        if student:
            si.registration_id = student.registration_id


def get_number_ok_student(students_list, number_selection):
    """
        Function to get the number of student who have the right number of choice and who haven't
        Params:
            students_list : the list of student present in InternshipChoice
            number_selection : the correct number of choices
        Return of array with two elements :
            the first is the number of the student with the right number of choices
            the second is the number of the student with the wrong number of choices
    """
    students_list = list(students_list)
    nbr_student = [0]*2
    # Set the number of the student who have their all selection of internships
    # who have a partial selection
    # who have no selection
    for sl in students_list:
        student = mdl.student.find_by_person(sl.student.person)
        choices = InternshipChoice.find_by_student(student)
        sl.number_choices = len(choices)
        if len(choices) == number_selection:
            nbr_student[0] += 1
        else :
            nbr_student[1] += 1
    return nbr_student


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_student_resume(request):
    # Get all stundents and the mandatory specialities
    students_list = InternshipChoice.find_by_all_student()
    specialities = InternshipSpeciality.search(mandatory=True)
    student_informations = list(InternshipStudentInformation.find_all())

    set_number_choices(student_informations)

    # Get the required number selection (4 for each speciality)
    # Get the number of student who have al least 4 corrects choice of internship
    # Get the number of student who can choose their internships
    number_selection = 4 * len (specialities)
    student_with_internships = len(students_list)
    students_can_have_internships = len(InternshipStudentInformation.find_all())

    students_ok = get_number_ok_student(students_list, number_selection)

    student_without_internship = students_can_have_internships - student_with_internships
    return render(request, "student_search.html", {'search_name': None,
                                                    'search_firstname': None,
                                                   'students': student_informations,
                                                   'number_selection': number_selection,
                                                   'students_ok': students_ok[0],
                                                   'students_not_ok': students_ok[1],
                                                   'student_with_internships': student_with_internships,
                                                   'students_can_have_internships': students_can_have_internships,
                                                   'student_without_internship': student_without_internship,
                                                   })


@login_required
@permission_required('internship.can_access_internship', raise_exception=True)
def internships_student_read(request, registration_id):
    student_to_read = mdl.student.find_by_registration_id(registration_id)
    if not request.user.has_perm('internship.is_internship_manager'):
        person_who_read = mdl.person.find_by_user(request.user)
        student_who_read = mdl.student.find_by_person(person_who_read)
        if not student_who_read or not student_to_read or student_who_read.pk != student_to_read.pk:
            raise PermissionDenied(request)
    if not student_to_read:
        return render(request, "student_resume.html", {'errors': ['student_not_exists']})
    information = InternshipStudentInformation.search(person = student_to_read.person)
    internship_choice = InternshipChoice.find_by_student(student_to_read)
    all_speciality = InternshipSpeciality.search(mandatory=True)

    affectations = InternshipStudentAffectationStat.search(student=student_to_read).order_by("period__date_start")
    periods = Period.search().order_by("date_start")
    organizations = Organization.search()
    set_organization_address(organizations)

    # Set the adress of the affactation
    for affectation in affectations:
        for organization in organizations:
            if affectation.organization == organization:
                affectation.organization.address = ""
                for o in organization.address:
                    affectation.organization.address = o

    internships = InternshipOffer.find_internships()
    #Check if there is a internship offers in data base. If not, the internships
    #can be block, but there is no effect
    if len(internships) > 0:
        if internships[0].selectable:
            selectable = True
        else:
            selectable = False
    else:
        selectable = True

    return render(request, "student_resume.html",
                           {'student': student_to_read,
                            'information': information[0],
                            'internship_choice': internship_choice,
                            'specialities': all_speciality,
                            'selectable': selectable,
                            'affectations': affectations,
                            'periods': periods,
                            })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_student_information_modification(request, registration_id):
    student = mdl.student.find_by(registration_id=registration_id)
    information = InternshipStudentInformation.search(person = student[0].person)
    student = student[0]
    return render(request, "student_information_modification.html",
                           {'student': student,
                            'information': information[0], })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_save_information_modification(request, registration_id):
    student = mdl.student.find_by(registration_id=registration_id)
    information = InternshipStudentInformation.search(person = student[0].person)
    if not information:
        information = InternshipStudentInformation()
        information.person = student[0].person
    else:
        information = information[0]
    information.email = request.POST.get('student_email')
    information.phone_mobile = request.POST.get('student_phone')
    information.location = request.POST.get('student_location')
    information.postal_code = request.POST.get('student_postal_code')
    information.city = request.POST.get('student_city')
    information.country = request.POST.get('student_country')
    information.latitude = None
    information.longitude = None
    information.save()

    redirect_url = reverse('internships_student_read', args=[registration_id])
    return HttpResponseRedirect(redirect_url)


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_student_affectation_modification(request, student_id):
    informations = InternshipStudentAffectationStat.search(student__pk = student_id)
    internship_choice = InternshipChoice.search(student__pk = student_id)
    if not internship_choice:
        student = mdl.student.find_by_id(student_id)
        information = InternshipChoice()
        information.student = student
    else:
        information = internship_choice.first()
    organizations = Organization.search()
    organizations = sort_organizations(organizations)

    specialities = InternshipSpeciality.find_all()
    for speciality in specialities :
        number=[int(s) for s in speciality.name.split() if s.isdigit()]
        if number:
            speciality.acronym =speciality.acronym + " " +str(number[0])
    periods = Period.search()
    return render(request, "student_affectation_modification.html",
                  {'information':         information,
                   'informations':         informations,
                   'organizations':        organizations,
                   'specialities':         specialities,
                   'periods':              periods,
                   })



@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_save_affectation_modification(request, registration_id):
    student = mdl.student.find_by(registration_id=registration_id)[0]
    if request.POST.get('period'):
        period_list = request.POST.getlist('period')
    if request.POST.get('organization'):
        organization_list = request.POST.getlist('organization')
    if request.POST.get('speciality'):
        speciality_list = request.POST.getlist('speciality')

    check_error_present = False
    index = len(period_list)
    for x in range(0, index):
        if organization_list[x] != "0":
            organization = Organization.search(reference=organization_list[x])[0]
            speciality = InternshipSpeciality.search(name=speciality_list[x])[0]
            period = Period.search(name=period_list[x])[0]
            check_internship_present = InternshipOffer.search(organization=organization, speciality=speciality)
            if len(check_internship_present) == 0:
                check_error_present = True
                messages.add_message(request, messages.ERROR, _('%s : %s-%s (%s)=> error') % (speciality.name, organization.reference, organization.name, period.name))

    if not check_error_present:
        InternshipStudentAffectationStat.search(student=student).delete()
        index = len(period_list)
        for x in range(0, index):
            if organization_list[x] != "0":
                organization = Organization.search(reference=organization_list[x])[0]
                speciality = InternshipSpeciality.search(name=speciality_list[x])[0]
                period = Period.search(name=period_list[x])[0]
                student_choices = InternshipChoice.search(student=student, speciality=speciality)
                affectation_modif = InternshipStudentAffectationStat()

                affectation_modif.student = student
                affectation_modif.organization = organization
                affectation_modif.speciality = speciality
                affectation_modif.period = period
                check_choice = False
                for student_choice in student_choices:
                    if student_choice.organization == organization:
                        affectation_modif.choice = student_choice.choice
                        check_choice = True
                        if student_choice.choice == 1:
                            affectation_modif.cost = 0
                        elif student_choice.choice == 2:
                            affectation_modif.cost = 1
                        elif student_choice.choice == 3:
                            affectation_modif.cost = 2
                        elif student_choice.choice == 4:
                            affectation_modif.cost = 3
                if not check_choice:
                    affectation_modif.choice = "I"
                    affectation_modif.cost = 10

                affectation_modif.save()
        redirect_url = reverse('internships_student_read', args=[student.registration_id])
    else:
        redirect_url = reverse('internship_student_affectation_modification', args=[student.id])
    return HttpResponseRedirect(redirect_url)


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_student_all(request):
    student_informations = list(InternshipStudentInformation.find_all())
    set_number_choices(student_informations)
    return render(request, "student_internships_all.html",
                  {'students':         student_informations,
                   })
