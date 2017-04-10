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
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from base import models as mdl
from internship import models as mdl_internship
from internship.forms.form_student_information import StudentInformationForm

from django.utils.translation import ugettext_lazy as _

from internship.models.cohort import Cohort
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
        choices = mdl_internship.internship_choice.find_by_student(student)
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
        choices = mdl_internship.internship_choice.find_by_student(student)
        sl.number_choices = len(choices)
        if len(choices) == number_selection:
            nbr_student[0] += 1
        else :
            nbr_student[1] += 1
    return nbr_student


def get_students():
    import collections
    from django.db import connection

    from internship.models.internship_student_information import InternshipStudentInformation
    from internship.models.internship_choice import InternshipChoice
    from base.models.student import Student

    connection.queries_log = collections.deque(maxlen=9000)
    print("before queries", len(connection.queries))
    qs_student_info = InternshipStudentInformation.objects.prefetch_related('person').all() \
        .order_by('person__last_name', 'person__first_name')

    person_ids = set(qs_student_info.values_list('person_id', flat=True))
    qs_student = Student.objects.prefetch_related('person').filter(person_id__in=person_ids)

    # select isi.id, person.id, person.first_name, person.last_name
    # from internship_internshipstudentinformation isi,
    #     base_person person,
    #     base_student student
    # where isi.person_id = person.id and student.person_id = person.id
    # order by person.first_name, person.last_name

    student_ids = qs_student.values_list('id', flat=True)

    choices = InternshipChoice.objects.filter(student_id__in=student_ids, internship_choice__gt=0) \
        .values_list('student_id', 'internship_choice') # .distinct('internship_choice')

    print(choices)
    # print(student_ids)

    students = [(student, False) for student in qs_student]

    print("after queries", len(connection.queries))

    return students


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_student_resume(request, cohort_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    students_with_status = get_students_with_status(cohort)
    student_with_internships = mdl_internship.internship_choice.get_number_students(cohort)
    students_can_have_internships = mdl_internship.internship_student_information.get_number_students(cohort)
    student_without_internship = students_can_have_internships - student_with_internships
    number_students_ok = len([x for x in students_with_status if x[1]])
    number_students_not_ok = len([x for x in students_with_status if x[1] is False])
    number_generalists = mdl_internship.internship_student_information.get_number_of_generalists(cohort)
    number_specialists = students_can_have_internships - number_generalists
    context = {
        'search_name': None,
        'search_firstname': None,
        'students': students_with_status,
        'students_ok': number_students_ok,
        'students_not_ok': number_students_not_ok,
        'student_with_internships': student_with_internships,
        'students_can_have_internships': students_can_have_internships,
        'student_without_internship': student_without_internship,
        "number_generalists": number_generalists,
        "number_specialists": number_specialists,
        'cohort': cohort,
    }
    return render(request, "student_search.html", context)


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_student_read(request, cohort_id, student_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)

    student_to_read = mdl.student.find_by_id(student_id)

    if not request.user.has_perm('internship.is_internship_manager'):
        person_who_read = mdl.person.find_by_user(request.user)
        student_who_read = mdl.student.find_by_person(person_who_read)
        if not student_who_read or not student_to_read or student_who_read.pk != student_to_read.pk:
            raise PermissionDenied(request)

    if not student_to_read:
        return render(request, "student_resume.html", {'errors': ['student_not_exists']})
    information = mdl_internship.internship_student_information.search(person = student_to_read.person).first()
    internship_choices = mdl_internship.internship_choice.get_internship_choices_made(cohort=cohort, student=student_to_read).order_by('choice')
    all_speciality = mdl_internship.internship_speciality.search(mandatory=True, cohort=cohort)
    internships = mdl_internship.internship.Internship.objects.filter(cohort=cohort, pk__gte=1)

    affectations = mdl_internship.internship_student_affectation_stat.search(student=student_to_read).\
        order_by("period__date_start")
    periods = mdl_internship.period.search().order_by("date_start")
    organizations = mdl_internship.organization.search()
    set_organization_address(organizations)

    # Set the adress of the affactation
    for affectation in affectations:
        for organization in organizations:
            if affectation.organization == organization:
                affectation.organization.address = ""
                for o in organization.address:
                    affectation.organization.address = o

    internship_offers = mdl_internship.internship_offer.find_internships()
    #Check if there is a internship offers in data base. If not, the internships
    #can be block, but there is no effect
    if len(internship_offers) > 0:
        if internship_offers[0].selectable:
            selectable = True
        else:
            selectable = False
    else:
        selectable = True

    return render(request, "student_resume.html",
                           {'student': student_to_read,
                            'information': information,
                            'internship_choices': internship_choices,
                            'specialities': all_speciality,
                            'selectable': selectable,
                            'affectations': affectations,
                            'periods': periods,
                            'cohort': cohort,
                            'internships': internships
                            })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_student_information_modification(request, cohort_id, student_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    student = mdl.student.find_by_id(student_id)
    information = mdl_internship.internship_student_information.search(person=student.person, cohort=cohort).first()
    form = StudentInformationForm()
    return render(request, "student_information_modification.html",
                           {'student': student,
                            'information': information,
                            'cohort': cohort,
                            "form": form})


@login_required
@require_POST
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_save_information_modification(request, cohort_id, student_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    student = mdl.student.find_by_id(student_id)
    information = mdl_internship.internship_student_information.find_by_person(student.person)
    if not information:
        information = mdl_internship.internship_student_information.InternshipStudentInformation()
        information.person = student.person

    if information.cohort == None:
        information.cohort = cohort

    form = StudentInformationForm(request.POST, instance=information)
    if form.is_valid():
        information.email = form.cleaned_data.get('email')
        information.phone_mobile = form.cleaned_data.get('phone_mobile')
        information.location = form.cleaned_data.get('location')
        information.postal_code = form.cleaned_data.get('postal_code')
        information.city = form.cleaned_data.get('city')
        information.country = form.cleaned_data.get('country')
        information.contest = form.cleaned_data.get('contest')
        information.latitude = None
        information.longitude = None
        information.save()

    redirect_url = reverse('internships_student_read', args=[cohort_id, student_id])
    return HttpResponseRedirect(redirect_url)


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_student_affectation_modification(request, cohort_id, student_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    informations = mdl_internship.internship_student_affectation_stat.search(student__pk = student_id)
    internship_choice = mdl_internship.internship_choice.search(student__pk = student_id)
    if not internship_choice:
        student = mdl.student.find_by_id(student_id)
        information = mdl_internship.internship_choice.InternshipChoice()
        information.student = student
    else:
        information = internship_choice.first()
    organizations = mdl_internship.organization.search(cohort=cohort)
    organizations = sort_organizations(organizations)

    specialities = mdl_internship.internship_speciality.find_all(cohort=cohort)
    for speciality in specialities :
        number=[int(s) for s in speciality.name.split() if s.isdigit()]
        if number:
            speciality.acronym =speciality.acronym + " " +str(number[0])
    periods = mdl_internship.period.search(cohort=cohort)
    return render(request, "student_affectation_modification.html",
                  {'information':         information,
                   'informations':         informations,
                   'organizations':        organizations,
                   'specialities':         specialities,
                   'periods':              periods,
                   'cohort':               cohort
                   })



@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_save_affectation_modification(request, cohort_id, student_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    student = mdl.student.find_by_id(student_id)
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
            organization = mdl_internship.organization.search(cohort=cohort, reference=organization_list[x])[0]
            speciality = mdl_internship.internship_speciality.search(cohort=cohort, name=speciality_list[x])[0]
            period = mdl_internship.period.search(cohort=cohort, name=period_list[x])[0]
            check_internship_present = mdl_internship.internship_offer.search(cohort=cohort, organization=organization, speciality=speciality)
            if len(check_internship_present) == 0:
                check_error_present = True
                messages.add_message(request, messages.ERROR, _('%s : %s-%s (%s)=> error') % (speciality.name, organization.reference, organization.name, period.name))

    if not check_error_present:
        mdl_internship.internship_student_affectation_stat.search(student=student).delete()
        index = len(period_list)
        for x in range(0, index):
            if organization_list[x] != "0":
                organization = mdl_internship.organization.search(cohort=cohort, reference=organization_list[x])[0]
                speciality = mdl_internship.internship_speciality.search(cohort=cohort, name=speciality_list[x])[0]
                period = mdl_internship.period.search(cohort=cohort, name=period_list[x])[0]
                student_choices = mdl_internship.internship_choice.search(student=student, speciality=speciality)
                affectation_modif = mdl_internship.internship_student_affectation_stat.InternshipStudentAffectationStat()

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
        redirect_url = reverse('internships_student_read', kwargs={"cohort_id":cohort.id, "student_id":student.id})
    else:
        redirect_url = reverse('internship_student_affectation_modification', kwargs={"cohort_id":cohort.id, "student_id":student.id})
    return HttpResponseRedirect(redirect_url)


def get_students_with_status(cohort):
    students_status = []
    students_informations = mdl_internship.internship_student_information.find_all(cohort)
    for student_info in students_informations:
        person = student_info.person
        student = mdl.student.find_by_person(person)
        student_status = get_student_status(student, cohort)
        students_status.append((student, student_status))
    return students_status


def get_student_status(student, cohort):
    internship_ids = mdl_internship.internship.Internship.objects.filter(cohort=cohort, pk__gte=1).values_list("pk", flat=True)
    internship_choices_values = mdl_internship.internship_choice.get_internship_choices_made(cohort=cohort, student=student).values_list("internship_id", flat=True)
    return len(list(set(internship_ids) - set(internship_choices_values))) == 0
