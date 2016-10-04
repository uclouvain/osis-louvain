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
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from internship.models import InternshipEnrollment, InternshipOffer, InternshipChoice, \
    Organization, OrganizationAddress, Period, \
    InternshipSpeciality, InternshipStudentInformation
from base import models as mdl
from collections import OrderedDict
from math import sin, cos, radians, degrees, acos
from operator import itemgetter


def calc_dist(lat_a, long_a, lat_b, long_b):
    """
        Function to compute the distance between two points.
        Params:
            lat_a : the latitude of the first adress
            long_a : the longitude of the first adress
            lat_b : the latitude of the second adress
            long_b : the longitude of the second adress
        Transform the params in radians then compute the sin and cos
        then transform it in miles or kilometers.
        Based on :
            https://gmigdos.wordpress.com/2010/03/31/python-calculate-the-distance-between-2-points-given-their-coordinates/
    """
    if lat_a == lat_b and long_a == long_b:
        # If there is the same adress, there is a chance to have a bug/crash
        # So it return 100 meters of distance
        return 0.1
    else:
        lat_a = radians(float(lat_a))
        lat_b = radians(float(lat_b))
        long_a = float(long_a)
        long_b = float(long_b)
        long_diff = radians(long_a - long_b)
        distance = (sin(lat_a) * sin(lat_b) +
                    cos(lat_a) * cos(lat_b) * cos(long_diff))
        # For distance in miles use this
        # return (degrees(acos(distance)) * 69.09)
        # For distance in kilometers use this
        return (degrees(acos(distance)) * 69.09)/0.621371


def work_dist(student, organizations):
    """
        Function to get the distances between the student and all organization in the DB, sorted asc
        Params:
            student : the student we want to get the latitude and longitude of
            organizations : the organizations in the DB, to compute their latitude/longitude with the student's
    """
    # Find the student's informations
    student_informations = InternshipStudentInformation.search(person__last_name=student.person.last_name, person__first_name=student.person.first_name)

    distance_student_organization = {}
    # For each organization in the list find the informations
    for organization in organizations :
        organization_informations = OrganizationAddress.search(organization = organization)
        # If the latitude is not a fake number, compute the distance between the student and the organization
        if organization_informations[0].latitude != 999 :
            distance = calc_dist(student_informations[0].latitude, student_informations[0].longitude,
                                 organization_informations[0].latitude, organization_informations[0].longitude)
            distance_student_organization[int(organization.reference)] = distance

    # Sort the distance
    distance_student_organization = sorted(distance_student_organization.items(), key=itemgetter(1))
    return distance_student_organization


def get_number_choices(internships):
    """
        Set new variables for the param, the number of the first and other choice for one internship
        Params :
            internships : the internships we want to compute the number of choices
    """
    for internship in internships:
        number_first_choice = len(InternshipChoice.search(organization = internship.organization,
                                                            speciality__acronym = internship.speciality.acronym,
                                                           choice=1))
        number_other_choice = len(InternshipChoice.search_other_choices(organization = internship.organization,
                                                            speciality__acronym = internship.speciality.acronym))
        internship.number_first_choice = number_first_choice
        internship.number_other_choice = number_other_choice

def set_tabs_name(specialities, student=None):
    """
        Set tab name for the html page base on the speciality
        and eventually the size of the choice of a student for a speciality
        (check if the student have done the correct the number of choice for this speciality)
        Params :
            specialities : the specialities we want to create the tab name
            student : default there is no student, if yes, used to get the number of choice
                        for a speciality for this student
    """
    for speciality in specialities:
        if student :
            size = len(InternshipChoice.search(speciality=speciality, student=student))
            speciality.size = size
        tab = speciality.name.replace(" ", "")
        speciality.tab = tab

def get_selectable(internships):
    """
        Function to check if the internships are selectable.
        Return the status of the first internship.
        If there is no internship, return True
    """
    if len(internships) > 0:
        return internships[0].selectable
    else:
        return True

def get_all_specialities(internships):
    """
        Function to create the list of the specialities, delete dpulicated and order alphabetical.
        Param:
            internships : the interships we want to get the speciality
    """
    tab = []
    for internship in internships:
        tab.append(internship.speciality)

    tab = list(OrderedDict.fromkeys(tab))
    return tab


def get_all_organizations(internships):
    """
        Function to create the options for the organizations selection list, delete duplicated
        Param:
            internships : the interships we want to get the organization
    """
    tab = []
    for internship in internships:
        tab.append(internship.organization)
    tab = list(set(tab))
    return tab


def rebuild_the_lists(preference_list, speciality_list, organization_list, internship_choice_tab=None):
    """
        Look over each value of the preference list
        If the value is 0, the student doesn't choice this organization or speciality
        So their value is 0
        Params :
            preference_list, speciality_list, organization_list, internship_choice_tab :
            The list to check the choices
    """
    index = 0
    for r in preference_list:
        if r == "0":
            speciality_list[index] = 0
            organization_list[index] = 0
            if internship_choice_tab:
                internship_choice_tab[index] = 0
        index += 1


def delete_dublons_keep_order(seq):
    """
        Function to delete the dublons of any list and keep the order of the list.
        Param:
            seq : the list where there is dublons
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def sort_internships(sort_internships):
    """
        Function to sort internships by the organization's reference.
        Params :
            sort_internships : the list of internships to be sorted
        Extract the ref of the organization, sort based in integer (the ref are in string),
        delete the dublons recreat the list of internship base of the organization reference
    """
    tab = []
    number_ref = []
    for sort_internship in sort_internships:
        if sort_internship is not None:
            number_ref.append(sort_internship.organization.reference)
    number_ref=sorted(number_ref, key=int)
    number_ref=delete_dublons_keep_order(number_ref)
    for i in number_ref:
        internships = InternshipOffer.search(organization__reference=i)
        for internship in internships:
            tab.append(internship)
    return tab


def set_student_choices_list(query,student_choice):
    """
        Function to set the list of the student's choices
        Params :
            query : the list of all internships
            student_choice : the list of the internships choose by the student
        Check if the internships and the choice are the same,
        if yes put the param of the max enrollments and if there are selectable.
        Then delete the internships in the list of the list of all internships
        (because it's all ready in the choices list wich it display first)
    """
    index = 0
    for choice in student_choice:
        for internship in query:
            if internship.organization == choice.organization and \
                            internship.speciality == choice.speciality:
                choice.maximum_enrollments = internship.maximum_enrollments
                choice.selectable = internship.selectable
                query[index] = 0
            index += 1
        query = [x for x in query if x != 0]
        index = 0
    query = [x for x in query if x != 0]
    return query


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships(request):
    # First get the value of the option's value for the sort
    if request.method == 'GET':
        organization_sort_value = request.GET.get('organization_sort')
        if request.GET.get('speciality_sort') != '0':
            speciality_sort_value = request.GET.get('speciality_sort')
        else :
            speciality_sort_value = None
    # Then select Internship Offer depending of the option
    if organization_sort_value and organization_sort_value != "0":
        query = InternshipOffer.search(organization__name = organization_sort_value)
    else:
        query = InternshipOffer.find_internships()

    # Sort the internships by the organization's reference
    query = sort_internships(query)

    # Get The number of differents choices for the internships
    get_number_choices(query)

    all_internships = InternshipOffer.find_internships()
    all_organizations = get_all_organizations(all_internships)
    all_specialities = get_all_specialities(all_internships)
    set_tabs_name(all_specialities)
    all_non_mandatory_speciality = InternshipSpeciality.find_non_mandatory()
    if speciality_sort_value:
        all_non_mandatory_internships = InternshipOffer.find_non_mandatory_internships(speciality__name=speciality_sort_value)
    else:
        all_non_mandatory_internships = InternshipOffer.find_non_mandatory_internships(speciality__mandatory=0)
    get_number_choices(all_non_mandatory_internships)

    return render(request, "internships.html", {'section': 'internship',
                                                'all_internships': query,
                                                'all_non_mandatory_internships': all_non_mandatory_internships,
                                                'all_organizations': all_organizations,
                                                'all_speciality': all_specialities,
                                                'organization_sort_value': organization_sort_value,
                                                'speciality_sort_value': speciality_sort_value,
                                                'non_mandatory_speciality': all_non_mandatory_speciality,
                                                })


@login_required
@permission_required('internship.can_access_internship', raise_exception=True)
def internships_stud(request):
    # Set the number of non mandatory internship and the sort array depending
    size_non_mandatory = 5
    speciality_sort_value = [None] * size_non_mandatory

    # Check if there is a speciality selected in a tab of non mandatory internship
    if request.method == 'GET':
        for x in range(1,size_non_mandatory):
            if request.GET.get("speciality_sort"+str(x)) != '0':
                speciality_sort_value[x] = request.GET.get("speciality_sort"+str(x))
            else :
                speciality_sort_value[x] = None

    # Get the student base on the user
    student = mdl.student.find_by(person_username=request.user)
    # Get in descending order the student's choices in first lines
    student_choice = InternshipChoice.find_by_student_desc(student)

    # Select all Internship Offer
    query = InternshipOffer.find_internships()

    # Sort the internships by the organization's reference
    query = sort_internships(query)

    # Change the query into a list
    query = list(query)
    # Delete the internships in query when they are in the student's selection then rebuild the query
    # Put datas wich need to be save in the student's choice list
    query = set_student_choices_list(query, student_choice)
    # Insert the student choice into the global query, at first position,
    for choice in student_choice:
        query.insert(0, choice)

    # Get The number of differents choices for the internships
    get_number_choices(query)

    all_internships = InternshipOffer.find_internships()
    all_speciality = get_all_specialities(all_internships)
    selectable = get_selectable(all_internships)
    set_tabs_name(all_speciality, student)

    # Set all non mandatory speciality for the dropdown list
    all_non_mandatory_speciality = InternshipSpeciality.find_non_mandatory()
    # Create an array of the number of non mandatory internship and put all the internship of the speciality selected in
    all_non_mandatory_internships = [None] * size_non_mandatory
    all_non_mandatory_selected_internships = [None] * size_non_mandatory
    for x in range(0,size_non_mandatory):
        if speciality_sort_value[x]:
            all_non_mandatory_internships[x] = InternshipOffer.find_non_mandatory_internships(speciality__name=speciality_sort_value[x])
            get_number_choices(all_non_mandatory_internships[x])
            set_tabs_name(all_non_mandatory_internships[x])
        else:
            all_non_mandatory_internships[x] = None
        all_non_mandatory_selected_internships[x]=InternshipChoice.search(internship_choice=x+1)

    return render(request, "internships_stud.html", {'section': 'internship',
                                                     'all_internships': query,
                                                     'non_mandatory_speciality': all_non_mandatory_speciality,
                                                     'all_non_mandatory_internships': all_non_mandatory_internships,
                                                     'all_non_mandatory_selected_internships': all_non_mandatory_selected_internships,
                                                     'speciality_sort_value': speciality_sort_value,
                                                     'all_speciality': all_speciality,
                                                     'selectable': selectable,
                                                     })


@login_required
@permission_required('internship.can_access_internship', raise_exception=True)
def internships_save(request):
    # Check if the internships are selectable, if yes students can save their choices
    all_internships = InternshipOffer.search()
    selectable = get_selectable(all_internships)

    if selectable :
        # Get the student
        student = mdl.student.find_by(person_username=request.user)
        # Delete all the student's choices for mandatory internships present in the DB
        InternshipChoice.objects.filter(student=student, internship_choice=0).delete()

        #Build the list of the organizations and specialities get by the POST request
        organization_list = list()
        speciality_list = list()
        if request.POST.get('organization'):
            organization_list = request.POST.getlist('organization')
        if request.POST.get('speciality'):
            speciality_list = request.POST.getlist('speciality')
        if request.POST.getlist('is_choice'):
            internship_choice_tab = request.POST.getlist('is_choice')
            internship_choice_tab_del = list(set(internship_choice_tab))
            for choice_tab in internship_choice_tab_del:
                InternshipChoice.objects.filter(student=student, internship_choice=choice_tab).delete()

        all_specialities = get_all_specialities(all_internships)
        set_tabs_name(all_specialities)
        # Create an array with all the tab name of the speciality
        preference_list_tab = []
        for speciality in all_specialities:
            preference_list_tab.append('preference'+speciality.tab)

        # Create a list, for each element of the previous tab,
        # check if this element(speciality) is in the post request
        # If yes, add all the preference of the speciality in the list
        preference_list = list()
        for pref_tab in preference_list_tab:
            if request.POST.get(pref_tab):
                for pref in request.POST.getlist(pref_tab) :
                    preference_list.append(pref)

        rebuild_the_lists(preference_list, speciality_list, organization_list, internship_choice_tab)
        # Rebuild the lists deleting the null value
        organization_list = [x for x in organization_list if x != 0]
        speciality_list = [x for x in speciality_list if x != 0]
        preference_list = [x for x in preference_list if x != '0']
        internship_choice_tab = [x for x in internship_choice_tab if x != 0]

        if len(speciality_list) > 0:
            # Check if the student sent correctly send 4 choice.
            # If not, the choices are set to 0
            old_spec=speciality_list[0]
            new_spec=""
            index = 0
            cumul = 0
            for p in speciality_list:
                new_spec = p
                index += 1
                if old_spec == new_spec:
                    cumul += 1
                    old_spec = new_spec
                else :
                    if cumul < 4:
                        cumul += 1
                        for i in range(index-cumul,index-1):
                            preference_list[i] = 0
                        cumul = 1
                    else :
                        cumul = 1
                    old_spec = new_spec
            if index < 4:
                for i in range(index-cumul,index):
                    preference_list[i] = 0
            else :
                if cumul != 4 :
                    for i in range(index-cumul,index):
                        if i < len(preference_list):
                            preference_list[i] = 0

        rebuild_the_lists(preference_list, speciality_list, organization_list, internship_choice_tab)
        # Rebuild the lists deleting the null value
        organization_list = [x for x in organization_list if x != 0]
        speciality_list = [x for x in speciality_list if x != 0]
        preference_list = [x for x in preference_list if x != '0']
        internship_choice_tab = [x for x in internship_choice_tab if x != 0]

        index = preference_list.__len__()

        # Save the new student's choices
        for x in range(0, index):
            new_choice = InternshipChoice()
            new_choice.student = student[0]
            organization = Organization.search(reference=organization_list[x])
            new_choice.organization = organization[0]
            speciality = InternshipSpeciality.search(name=speciality_list[x])
            new_choice.speciality = speciality[0]
            new_choice.choice = preference_list[x]
            new_choice.internship_choice = internship_choice_tab[x]
            new_choice.priority = False
            new_choice.save()

    return HttpResponseRedirect(reverse('internships_stud'))


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def student_choice(request, id):
    # Get the internship by its id
    internship = InternshipOffer.find_intership_by_id(id)
    # Get the students who have choosen this internship
    students = InternshipChoice.search(organization=internship.organization,
                                       speciality=internship.speciality)
    number_choices = [None]*5

    # Get the choices' number for this internship
    for index in range(1, 5):
        number_choices[index] = len(InternshipChoice.search(organization=internship.organization,
                                                            speciality=internship.speciality,
                                                            choice=index))

    return render(request, "internship_detail.html", {'section': 'internship',
                                                      'internship': internship,
                                                      'students': students,
                                                      'number_choices': number_choices, })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_block(request):
    internships = InternshipOffer.search()
    if internships:
        #Get the value of the first internship in the DB
        internship_selectable = internships[0].selectable
    # For each internship in the DB invert the selectable flag of the first internship
    # Explanation : when there is new internship(s) in the DB, there are selectable by default
    # So when then inversion of the flag is done, there are some incoherences with flag True and False.
    # With that way, all the internships will have the same flag
    for internship in internships:
        edit_internship = InternshipOffer.find_intership_by_id(internship.id)
        edit_internship.selectable = not internship_selectable
        edit_internship.save()

    return HttpResponseRedirect(reverse('internships_home'))


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internships_modification_student(request, registration_id):
    # Get the student base on the user
    student = mdl.student.find_by(registration_id=registration_id, full_registration = True)
    # Get in descending order the student's choices in first lines
    student_choice = InternshipChoice.find_by_student_desc(student)
    student_enrollment = InternshipEnrollment.search(student = student)

    # Select all Internship Offer
    query = InternshipOffer.find_internships()
    # Change the query into a list
    query = list(query)

    # Delete the internships in query when they are in the student's selection then rebuild the query
    # Put datas wich need to be save in the student's choice list
    index = 0
    for choice in student_choice:
        for internship in query:
            if internship.organization == choice.organization and \
                            internship.speciality == choice.speciality:
                choice.maximum_enrollments = internship.maximum_enrollments
                choice.selectable = internship.selectable
                query[index] = 0
            index += 1
        query = [x for x in query if x != 0]
        index = 0
    query = [x for x in query if x != 0]

    # Insert the student choice into the global query, at first position
    for choice in student_choice :
        query.insert(0,choice)

    # Get The number of differents choices for the internships
    get_number_choices(query)

    all_internships = InternshipOffer.find_internships()
    all_speciality = get_all_specialities(all_internships)
    set_tabs_name(all_speciality, student)

    periods = Period.search()

    return render(request, "internship_modification_student.html", {'section': 'internship',
                                                                    'all_internships': query,
                                                                    'all_speciality': all_speciality,
                                                                    'periods': periods,
                                                                    'registration_id': registration_id,
                                                                    'student': student[0],
                                                                    'student_enrollment': student_enrollment,
                                                                    })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_save_modification_student(request) :
    # Get the student
    registration_id = request.POST.getlist('registration_id')
    student = mdl.student.find_by(registration_id=registration_id[0], full_registration = True)
    # Delete all the student's choices present in the DB
    InternshipChoice.objects.filter(student=student).delete()
    InternshipEnrollment.objects.filter(student=student).delete()

    #Build the list of the organizations and specialities get by the POST request
    organization_list = list()
    speciality_list = list()
    periods_list = list()
    fixthis_list = list()

    if request.POST.get('organization'):
        organization_list = request.POST.getlist('organization')
    if request.POST.get('speciality'):
        speciality_list = request.POST.getlist('speciality')
    if request.POST.get('periods_s'):
        periods_list = request.POST.getlist('periods_s')
    if request.POST.get('fixthis'):
        fixthis_list = request.POST.getlist('fixthis')

    all_internships = InternshipOffer.find_internships()
    all_specialities = get_all_specialities(all_internships)
    set_tabs_name(all_specialities)

    # Create an array with all the tab name of the speciality
    preference_list_tab = []
    for speciality in all_specialities:
        preference_list_tab.append('preference'+speciality.tab)

    # Create a list, for each element of the previous tab,
    # check if this element(speciality) is in the post request
    # If yes, add all the preference of the speciality in the list
    preference_list = list()
    for pref_tab in preference_list_tab:
        if request.POST.get(pref_tab):
            for pref in request.POST.getlist(pref_tab) :
                preference_list.append(pref)

    # If the fix checkbox is checked, the list receive '0', '1' as data
    # Delete the '0' value (the value before the '1', wich is required)
    index = 0
    for value in fixthis_list:
        if value == '1'and fixthis_list[index-1]=='0':
            del fixthis_list[index-1]
        index += 1

    rebuild_the_lists(preference_list, speciality_list, organization_list)

    # Create the list of all preference and the internships fixed
    final_preference_list = list()
    final_fixthis_list = list()
    index = 0
    for p in preference_list:
        if p != '0':
            final_preference_list.append(p)
            final_fixthis_list.append(fixthis_list[index])
        index += 1

    # Rebuild the lists deleting the null value
    organization_list = [x for x in organization_list if x != 0]
    speciality_list = [x for x in speciality_list if x != 0]
    preference_list = [x for x in preference_list if x != '0']

    # Save the new choices
    index = final_preference_list.__len__()
    for x in range(0, index):
        new_choice = InternshipChoice()
        new_choice.student = student[0]
        organization = Organization.search(reference=organization_list[x])
        new_choice.organization = organization[0]
        speciality = InternshipSpeciality.search(name=speciality_list[x])
        new_choice.speciality = speciality[0]
        new_choice.choice = final_preference_list[x]
        if final_fixthis_list[x] == '1':
            new_choice.priority = True
        else :
            new_choice.priority = False
        new_choice.save()

    # Save in the enrollement if the internships are fixed and a period is selected
    index = periods_list.__len__()
    for x in range(0, index):
        if periods_list[x] != '0':
            new_enrollment = InternshipEnrollment()
            tab_period = periods_list[x].split('\\n')
            period = Period.search(name=tab_period[0])
            organization = Organization.search(reference=tab_period[1])
            speciality = InternshipSpeciality.search(name=tab_period[2])
            internship = InternshipOffer.search(speciality__name = speciality[0], organization__reference = organization[0].reference)
            new_enrollment.student = student[0]
            new_enrollment.internship_offer = internship[0]
            new_enrollment.place = organization[0]
            new_enrollment.period = period[0]
            new_enrollment.save()

    redirect_url = reverse('internships_modification_student', args=[registration_id[0]])
    return HttpResponseRedirect(redirect_url)
