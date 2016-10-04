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
import copy
import sys
from collections import OrderedDict
from operator import itemgetter
from random import randint, choice
from statistics import mean, stdev
from collections import defaultdict

from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from internship.models import *
from internship.views.internship import calc_dist, set_tabs_name
from internship.views.place import sort_organizations, set_speciality_unique
import time
import datetime
# ****************** Global vars ******************
errors = []  # List of all internship added to hospital error, as tuple (student, speciality, period)
solution = {}  # Dict with the solution => solution[student][period] = SolutionLine
internship_table = {}  # List of all available internship. Organization, speciality, period
internship_table_mi = {}  # List of available internship for "MI"
organizations = {}  # Dict of all organizations
specialities_dict = {}  # Dict of all specialities
distance_students = {}  # Dict of distances between students and hospitals
internship_offer_dic = {}  # Dict of all internship offers
organization_addresses_dic = {}  # Dict of all organization addresses
internship_table_original = {}  # Copy of internship_table, is used to know if an internship is empty

# ****************** Constants ******************
emergency = 15  # Id of the speciality "Urgences"
hospital_error = 999  # Reference of the hospital "erreur"
hospital_to_edit = 888  # Reference of the hospital "a_modifier"
# List of the periods => (name, priority)
periods_dict = {'P1': True, 'P2': True, 'P3': True, 'P4': True, 'P5': True, 'P6': True, 'P7': True, 'P8': True,
                'P9': False, 'P10': False, 'P11': False, 'P12': False}
# The costs used to compute the score of the solution
# First choice = cost 0, second choice = cost 1, etc
# I = impose internship, C = non-consecutive internship and X = hospital error
costs = {1: 0, 2: 1, 3: 2, 4: 3, 'I': 10, 'C': 5, 'X': 1000}


# ******************  Classes ******************
class SolutionsLine:
    def __init__(self, student, organization, speciality, period, choice, type_of_internship='N', cost=0,
                 consecutive_month=0):
        self.student = student
        self.organization = organization
        self.speciality = speciality
        self.period = period
        self.choice = choice
        self.cost = cost
        self.consecutive_month = consecutive_month
        self.type_of_internship = type_of_internship

    def __repr__(self):
        return "[" + str(self.period).zfill(2) + "|H:" + str(self.organization.reference).zfill(3) + "|S:" + str(
            self.speciality.acronym).zfill(2) + "|C:" + str(self.cost).zfill(2) + "(" + str(self.choice) + ")|T:" + str(
            self.type_of_internship) + "]"


class StudentChoice:
    def __init__(self, student, organization, speciality, choice, priority):
        self.student = student
        self.organization = organization
        self.speciality = speciality
        self.choice = choice
        self.priority = priority


# ****************** Utils ******************
def compute_stats(sol):
    """
    Compute the statistics of the solution
    """

    stats = {}
    total_cost = 0
    consecutive_month = 0
    imposed_choices = 0
    erasmus = 0
    hospital_error_count = 0
    mean_array = []
    distance_mean = []
    others_students = set()
    others_specialities = {}
    others_specialities_students = {}

    # Retrieve all specialities
    specialities = InternshipSpeciality.objects.all().select_related()

    # Initialize the others_specialities and others_specialities_students
    for speciality in specialities:
        others_specialities[speciality] = 0
        others_specialities_students[speciality] = set()

    # Total number of internships
    first, second, third, fourth = 0, 0, 0, 0

    # Number of internships for each category
    # n = normal, s = social
    first_n, second_n, third_n, fourth_n = 0, 0, 0, 0
    first_s, second_s, third_s, fourth_s = 0, 0, 0, 0

    # Iterate all students
    for student, periods in sol.items():
        # Cost of the student solution
        cost = periods['score']
        # Add cost of the student to the total cost
        total_cost += cost
        # Add the cost of the student to the mean_array, this array is used
        # to find the standard deviation with command "stdev"
        mean_array.append(cost)
        # Iterate over all periods of the student
        for period, internship in periods.items():
            if period is not 'score':
                if internship is not None:
                    # First choice
                    if internship.choice == "1":
                        # Increment the number of total first choices
                        first += 1
                        # Increment the number of total normal first choices
                        if internship.type_of_internship == "N":
                            first_n += 1
                        # Increment the number of total social first choices
                        if internship.type_of_internship == "S":
                            first_s += 1
                    # Second choice
                    elif internship.choice == "2":
                        second += 1
                        if internship.type_of_internship == "N":
                            second_n += 1
                        if internship.type_of_internship == "S":
                            second_s += 1
                    # Third choice
                    elif internship.choice == "3":
                        third += 1
                        if internship.type_of_internship == "N":
                            third_n += 1
                        if internship.type_of_internship == "S":
                            third_s += 1
                    # Fourth choice
                    elif internship.choice == "4":
                        fourth += 1
                        if internship.type_of_internship == "N":
                            fourth_n += 1
                        if internship.type_of_internship == "S":
                            fourth_s += 1
                    # Erasmus
                    elif internship.choice == 'E':  # Erasmus
                        erasmus += 1
                    # Imposed choice
                    elif internship.choice == 'I':  # Imposed hospital
                        # Retrieve the addresses of the hospital and the student
                        addr_student = InternshipStudentInformation.search(person=student.person)[0]
                        addr_organization = OrganizationAddress.search(organization=internship.organization)[0]
                        # Compute the distance between the student address
                        # and hospital address and append it to the list
                        # We will compute the mean distance with mean method
                        distance_mean.append(compute_distance(addr_student, addr_organization))
                        # Increment total of imposed choices
                        imposed_choices += 1
                        # Add the student to the set "others_students",
                        # we will use this set to find the number of students
                        # with imposed choices
                        others_students.add(student)
                        others_specialities[internship.speciality] += 1
                        others_specialities_students[internship.speciality].add(student)
                    # Hostpital error
                    if int(internship.organization.reference) == hospital_error:
                        hospital_error_count += 1
                    consecutive_month += internship.consecutive_month
    # Total number of students
    number_of_students = len(sol)
    # Total number of internships
    total_internships = number_of_students * 8

    # Get number of students socio
    students_socio = set()
    for speciality, students in get_student_mandatory_choices(True).items():
        for choices in students:
            students_socio.add(choices[0].student.id)
    socio = len(InternshipChoice.objects.filter(priority=True).distinct('student').values('student'))

    total_n_internships = first_n + second_n + third_n + fourth_n + imposed_choices
    total_s_internships = first_s + second_s + third_s + fourth_s

    # Stats : Number of students
    stats['tot_stud'] = len(sol)
    stats['erasmus'] = erasmus
    stats['erasmus_pc'] = round(erasmus / total_internships * 100, 2)
    stats['erasmus_students'] = len(InternshipEnrollment.objects.distinct('student').values('student'))
    stats['erasmus_students_pc'] = round(stats['erasmus_students'] / stats['tot_stud'] * 100, 2)
    stats['socio'] = socio
    stats['socio_pc'] = round(socio / total_internships * 100, 2)
    stats['socio_students'] = len(students_socio)
    stats['socio_students_pc'] = round(stats['socio_students'] / stats['tot_stud'] * 100, 2)

    # Stats: Internships per choice
    stats['first'] = first
    stats['first_pc'] = round(first / total_internships * 100, 2)
    stats['second'] = second
    stats['second_pc'] = round(second / total_internships * 100, 2)
    stats['third'] = third
    stats['third_pc'] = round(third / total_internships * 100, 2)
    stats['fourth'] = fourth
    stats['fourth_pc'] = round(fourth / total_internships * 100, 2)
    stats['others'] = imposed_choices
    stats['others_pc'] = round(imposed_choices / total_internships * 100, 2)
    stats['others_students'] = len(others_students)
    stats['others_specialities'] = others_specialities
    stats['others_specialities_students'] = others_specialities_students

    stats['mean_stud'] = round(mean(mean_array), 2)

    # Compute standard deviation of the score
    if len(mean_array) > 1:
        std_dev_stud = round(stdev(mean_array), 2)
    else:
        std_dev_stud = 0
    stats['std_dev_stud'] = std_dev_stud
    stats['mean_noncons'] = round(consecutive_month / number_of_students, 2)
    stats['sol_cost'] = total_cost
    stats['total_internships'] = total_internships

    if len(distance_mean) == 0:
        distance_mean.append(0)
    stats['distance_mean'] = round(mean(distance_mean), 2)
    stats['hospital_error'] = hospital_error_count

    # Stats: Internships of normal students
    if total_n_internships == 0:
        total_n_internships = 1
    stats['first_n'] = first_n
    stats['second_n'] = second_n
    stats['third_n'] = third_n
    stats['fourth_n'] = fourth_n
    stats['first_n_pc'] = round(first_n / total_n_internships * 100, 2)
    stats['second_n_pc'] = round(second_n / total_n_internships * 100, 2)
    stats['third_n_pc'] = round(third_n / total_n_internships * 100, 2)
    stats['fourth_n_pc'] = round(fourth_n / total_n_internships * 100, 2)
    stats['others_n_pc'] = round(imposed_choices / total_n_internships * 100, 2)

    # Stats: Internships of social students
    if total_s_internships == 0:
        total_s_internships = 1
    stats['first_s'] = first_s
    stats['second_s'] = second_s
    stats['third_s'] = third_s
    stats['fourth_s'] = fourth_s
    stats['first_s_pc'] = round(first_s / total_s_internships * 100, 2)
    stats['second_s_pc'] = round(second_s / total_s_internships * 100, 2)
    stats['third_s_pc'] = round(third_s / total_s_internships * 100, 2)
    stats['fourth_s_pc'] = round(fourth_s / total_s_internships * 100, 2)
    return stats


def shift_array(array):
    """ Shift array at random index """
    position = randint(0, len(array) - 1)
    return array[position:] + array[:position]


def create_solution_line(student, organization, speciality, period, choice, type_of_internship='N', cost=0,
                         consecutive_month=0):
    solution_line = InternshipStudentAffectationStat()
    solution_line.student = student
    solution_line.organization = organization
    solution_line.speciality = speciality
    solution_line.period = period
    solution_line.choice = choice
    solution_line.cost = cost
    solution_line.consecutive_month = consecutive_month
    solution_line.type_of_internship = type_of_internship
    return solution_line


def init_internship_table():
    """
    Initialise the table of internships.
    This object store the number of available places for given organization, speciality, period
    :return: a dict : internshipTable[organization][speciality][period]
    """
    global internship_table_mi, internship_table_original
    # Retrieve all PeriodInternshipPlaces
    period_internship_places = PeriodInternshipPlaces.objects.all().select_related()
    temp_internship_table = {}
    # Put each period_internship_places in the right position
    for pid in period_internship_places:
        organization = pid.internship.organization
        speciality = pid.internship.speciality
        name = pid.period.name
        # If the organization does not exists in temp_internship_table we initialize it
        if organization not in temp_internship_table:
            temp_internship_table[organization] = {}
            internship_table_mi[organization] = {}
            internship_table_original[organization] = {}
        # If the speciality does not exists in temp_internship_table[organization] we initialize it
        if speciality not in temp_internship_table[organization]:
            temp_internship_table[organization][speciality] = {}
            internship_table_original[organization][speciality] = {}
        # Perform strip because the database contains an empty space before the acronym
        if speciality.acronym.strip() == 'MI':
            # The places of the MI are stored in a different map, because we have to divide this number by 3
            internship_table_mi[organization][name] = pid.number_places
        temp_internship_table[organization][speciality][name] = pid.number_places
        # Keep the original number of places for each organization/speciality/period
        internship_table_original[organization][speciality][name] = pid.number_places
    # TODO : Copy original?
    return temp_internship_table


def init_solution():
    """
    Initialize the empty solution, the solution is represented by a dictionary of students.
    Each student will have a dict with 12 periods and each period will have an 'InternshipEnrollment'
    """
    global solution
    # Retrieve all students
    internshipChoices = InternshipChoice.find_by_all_student()
    # For each student create an empty dict
    for internshipChoice in internshipChoices:
        solution[internshipChoice.student] = {}


def init_organizations():
    """
    Retrieve addresses of all organisation and init the hospital "error".
    """
    # Save data directly in global variables
    global organizations, organization_addresses_dic
    organizations[hospital_error] = Organization.objects.filter(reference=hospital_error)[0]
    organizations[hospital_to_edit] = Organization.objects.filter(reference=hospital_to_edit)[0]

    for organization_address in OrganizationAddress.objects.all():
        organization_addresses_dic[organization_address.organization] = organization_address


def init_specialities():
    """
    Retrieve all internship offers and the id of the speciality "emergency"
    """
    # Save data directly in global variables
    global specialities_dict, emergency, internship_offer_dic
    for speciality in InternshipSpeciality.find_all():
        internship_offer_dic[speciality] = InternshipOffer.search(speciality=speciality)
        specialities_dict[speciality.name] = speciality.id
        if speciality.acronym.strip() == 'UR':
            emergency = speciality.id


def is_internship_available(organization, speciality, period):
    """
    Check if an internship is available for given organization, speciality, period.
    An internship is available if we have at least 1 place left
    :param organization: id of the organisation
    :param speciality: id of the speciality
    :param period: id of the period
    :return: True if the internship is available False otherwise
    """
    global internship_table, internship_table_mi
    # We use another structure to check the available places of MI.
    if speciality.acronym.strip() == 'MI':
        return internship_table_mi[organization][period] > 0
    return internship_table[organization][speciality][period] > 0


def decrease_available_places(organization, speciality, period):
    """
    Decrease the number of available places for given organization, speciality, period
    :param organization: id of the organisation
    :param speciality: id of the speciality
    :param period: id of the period
    """
    global internship_table, internship_table_mi
    # We use another structure for "MI"
    if speciality.acronym.strip() == 'MI':
        internship_table_mi[organization][period] -= 1
    internship_table[organization][speciality][period] -= 1


def increase_available_places(organization, speciality, period):
    """
    Decrease the number of available places for given organization, speciality, period
    :param organization: id of the organisation
    :param speciality: id of the speciality
    :param period: id of the period
    """
    global internship_table, internship_table_mi
    # We use another structure for "MI"
    if speciality.acronym.strip() == 'MI':
        internship_table_mi[organization][period] += 1
    internship_table[organization][speciality][period] += 1


def get_available_periods_of_student(student_solution, mandatory):
    """
    Get available periods of students. Return all periods that does not exists in the solution of the student.
    :param student_solution: solution of the student(a dict where the key represent the id of the period and
    the value represents an InternshipEnrollment )
    :param mandatory: Specify the type of periods to check
    :return: the set of available periods of the student
    """
    available_periods = set()
    for period, is_mandatory in periods_dict.items():
        # Check if the student have already an internship assigned for period 'period' and if the period is mandatory
        if period not in student_solution and is_mandatory == mandatory:
            available_periods.add(period)
        pass
    return available_periods


def get_available_periods_of_internship(organization, speciality):
    """
    Get available periods of internship for given organization, speciality.
    The internship is available if it have at least 1 place available
    :param organization: id of the organization
    :param speciality: id of the speciality
    :return: the set of available periods of the internship
    """
    available_periods = set()
    if speciality in internship_table[organization]:
        for period, value in internship_table[organization][speciality].items():
            if is_internship_available(organization, speciality, period):
                available_periods.add(period)
    return available_periods


def get_number_of_period(period):
    return int(period.replace("P", ""))


def get_next_period(period):
    return "P" + str((get_number_of_period(period) + 1))


def get_previous_period(period):
    return "P" + str((get_number_of_period(period) - 1))


def get_double_available_periods_of_student(student_solution, mandatory):
    """
    This method is used to find suitable periods of the student for the speciality 'Emergency'.
    We need to find all consecutive periods of the students that are still free.
    :param student_solution: solution of the student(a dict where the key represent the id of the period and
    the value represents an InternshipEnrollment )
    :param mandatory: Specify the type of periods to check
    :return: the set of available double periods of the student
    """
    available_periods = set()
    for period, is_mandatory in periods_dict.items():
        if mandatory == is_mandatory:
            # Check if period is not present in the solution
            if period not in student_solution:
                next_period = get_next_period(period)
                # Check if period + 1 is not present in the solution and if the types of periods are the same
                if get_number_of_period(period) + 1 <= len(periods_dict) and next_period not in student_solution:
                    if periods_dict[next_period] == mandatory:
                        available_periods.add((period, next_period))
    return available_periods


def is_same(student_solution, organization, period):
    """
    Check if 'studentSolution[period].organization' and 'organization' are the same.
    :param student_solution: solution of the student(a dict where the key represent the id of the period and
    the value represents an InternshipEnrollment )
    :param organization: organisation to compare
    :param period: id of the period
    :return: True if 2 organisation are the same, False otherwise
    """
    if get_number_of_period(period) < 0 or get_number_of_period(period) > len(periods_dict):
        return False
    elif period not in student_solution or student_solution[period].organization != organization:
        return False
    else:
        return True


def is_empty_internship(organization, speciality, period):
    """
    Check if the internship in the "organization" / "speciality" / "period" is empty.
    Empty = non student has this internship.
    :param organization: organization to check
    :param speciality: speciality to check
    :param period: id of the period to check
    :return: True if the internship is empty, false otherwise
    """
    return internship_table[organization][speciality][period] == internship_table_original[organization][speciality][
        period]


def get_solution_cost():
    """
    Compute the total cost of the solution. (Sum of the cost of all students)
    :return: Cost of the solution
    """
    total_cost = 0
    for student, periods in solution.items():
        total_cost += get_student_solution_cost(periods)
    return total_cost


def get_student_solution_cost(data):
    """
    Compute the cost of the student's solution.
    This function is mainly used to compare different solutions in "iterate_choices".
    Student solution = 12 periods of internships
    """
    score = 0
    for period, internship in data.items():
        if internship is not None:
            # Check if "internship.choice" is an int.
            if isinstance(internship.choice, int):
                score = score + costs[internship.choice]
            # Nonconsecutive organization, check if the previous or next organization is same
            if not is_same(data, data[period].organization, get_previous_period(period)):
                if not is_same(data, data[period].organization, get_next_period(period)):
                    score = score + costs['C']
            # Imposed organization
            if data[period].choice == 'I':
                score = score + costs['I']
            # Hospital error
            if data[period].choice == 'X':
                score = score + costs['X']
            # Empty internships
            if is_empty_internship(data[period].organization, data[period].speciality, period):
                score -= 10
    return score


def update_scores(student):
    """
    Update the cost of each internship for given student solution.
    """
    data = solution[student]
    for period, internship in data.items():
        score = 0
        solution[student][period].consecutive_month = 0
        # Check if "internship.choice" is an int.
        if isinstance(internship.choice, int):
            score = score + costs[internship.choice]
        # Nonconsecutive organization, check if the previous or next organization is same
        if not is_same(data, data[period].organization, get_previous_period(period)):
            if not is_same(data, data[period].organization, get_next_period(period)):
                score = score + costs['C']
                solution[student][period].consecutive_month = 1
        # Imposed organization
        if data[period].choice == 'I':
            score = score + costs['I']
        # Hospital error
        if data[period].choice == 'X':
            score = score + costs['X']
        solution[student][period].cost = score


def compute_distance(address_student, address_organization):
    """
    Compute the distance between 2 addresses
    :param address_student:  Student address
    :param address_organization:  Organization Address
    :return: Distance in km between the organization and the student address
    """

    distance = calc_dist(address_student.latitude, address_student.longitude, address_organization.latitude,
                         address_organization.longitude)
    return distance


def get_student_mandatory_choices(priority):
    """
    Return all student's choices of given type.
    :param priority: True if we have to return the choices of priority student,
    false if we have to return the choices of normal students
    :return: A dict of dict : <speciality, <student, [choices]>>.
    """
    specialities = {}
    choices = InternshipChoice.objects.filter(priority=priority).select_related("speciality", "student")

    if len(choices) == 0:
        return {}

    # Build dict with specialities[speciality][student] <- InternshipChoice
    for choice in choices:
        # Init the speciality if does not exists in 'specialities'
        if choice.speciality.id not in specialities:
            specialities[choice.speciality.id] = {}
        # Init the student if does not exists in 'specialities[choice.speciality]'
        if choice.student not in specialities[choice.speciality.id]:
            specialities[choice.speciality.id][choice.student] = []
        specialities[choice.speciality.id][choice.student].append(choice)

    # Remove erasmus choices
    if priority:
        for enrollment in InternshipEnrollment.objects.all():
            if enrollment.internship_offer.speciality.id in specialities:
                if enrollment.student in specialities[enrollment.internship_offer.speciality.id]:
                    del specialities[enrollment.internship_offer.speciality.id][enrollment.student]
    else:
        for choice in InternshipChoice.objects.filter(priority=True).select_related("speciality", "student"):
            if choice.student in specialities[choice.speciality.id]:
                del specialities[choice.speciality.id][choice.student]

    # Convert the dict of students into list of students
    for speciality, students in specialities.items():
        specialities[speciality] = [v for v in students.values()]

    # Remove empty keys
    data = OrderedDict((k, v) for k, v in specialities.items() if v)

    # Sort he dict of student (this optimize the final result)
    global specialities_dict

    all_specialities = InternshipSpeciality.search_order_by_position(mandatory=True)
    orders = []

    for speciality in all_specialities:
        orders.append(speciality.name)

    for key in orders:
        if specialities_dict[key] in data:
            v = data[specialities_dict[key]]
            del data[specialities_dict[key]]
            data[specialities_dict[key]] = v

    return data


def find_nearest_hospital(student, speciality, exclude):
    """
    Find the nearest available hospital.
    The start point is the address of the student and the end point the address of the hospital.
    :param student: Student object
    :param speciality: Speciality of the internship
    :param exclude: Set of all hospital that we already tried for this student
    :return: the nearest available hospital
    """
    # TODO : ???
    # Check if the student has already computed the distances.
    if student not in distance_students:
        internships = internship_offer_dic[speciality]
        addr_student = InternshipStudentInformation.search(person=student.person)[0]
        data = {}
        for internship in internships:
            # Ignore erasmus organizations
            if int(internship.organization.reference) < 500:
                if student not in distance_students:
                    distance_students[student] = {}
                addr_organization = organization_addresses_dic[internship.organization]
                # Compute the distance between 2 addresses and store it in the dict
                if addr_organization.latitude is not None and addr_student.latitude is not None:
                    distance = compute_distance(addr_student, addr_organization)
                    for period, places in internship_table[internship.organization][speciality].items():
                        # Add the false distance to the hospital with non empty internships.
                        # So firstly we will use the empty internships
                        if places != internship_table_original[internship.organization][speciality][period]:
                            distance += 3000

                    data[internship.organization] = distance

        # Sort organizations by distance
        ordered_data = OrderedDict(sorted(data.items(), key=lambda t: t[1]))
        distance_students[student] = ordered_data

    for organization, distance in distance_students[student].items():
        # Return lowest not excluded organization
        if organization not in exclude:
            return organization


def iterate_choices(choices, priority, is_emergency):
    """
    For each choice we generate a solution and compute the score of this solution
    :param is_emergency: True if we iterate emergency choices, False otherwise
    :param choices: List of the choices
    :param priority: True if the student is a social student false otherwise
    :return: List of bests solutions (will contain multiples choices if the score is the same)
    """
    best_solutions = []
    current_score = sys.maxsize
    student = choices[0].student

    # Get all still available periods of the students
    if is_emergency:
        available_periods_of_student = get_double_available_periods_of_student(solution[student], True)
    else:
        available_periods_of_student = get_available_periods_of_student(solution[student], True)
    # Raise exception when user have 0 available periods. If this happen, there is an inconsistency in the data.
    if len(available_periods_of_student) == 0:
        raise Exception('Student' + str(student) + 'has 0 periods available')
    # Iterate over all choices
    for choice in choices:
        # Get all available periods for given organization / speciality
        available_periods_of_internship = get_available_periods_of_internship(choice.organization, choice.speciality)
        # Iterate over all available periods of the student
        for available_period in available_periods_of_student:
            if priority:
                type_of_internship = "S"
            else:
                type_of_internship = "N"
            if is_emergency:
                if available_period[0] in available_periods_of_internship:
                    if available_period[1] in available_periods_of_internship:
                        # Copy the original solution of the student
                        temp_solution = copy.copy(solution[student])
                        # And create the new solution with the 2 new internships
                        temp_solution[available_period[0]] = SolutionsLine(student,
                                                                           choice.organization,
                                                                           choice.speciality,
                                                                           available_period[0],
                                                                           choice.choice,
                                                                           type_of_internship)
                        temp_solution[available_period[1]] = SolutionsLine(student,
                                                                           choice.organization,
                                                                           choice.speciality,
                                                                           available_period[1],
                                                                           choice.choice,
                                                                           type_of_internship)
                        # Compute the score of the new solution
                        temp_score = get_student_solution_cost(temp_solution)
                        # In order to optimise the solution, we prefer to start with an odd period,
                        # if it not the case we add 15 points to the solution.
                        # This operation helps to better usage of available places
                        if available_period[0] in ['P2', 'P4', 'P6', 'P8', 'P10', 'P12']:
                            temp_score += 15
                        # Compute the score of the new solution
                        temp_solution[available_period[0]].cost = temp_score
                        temp_solution[available_period[1]].cost = temp_score
                        # Check if the new solution is better than old
                        if temp_score < current_score:
                            current_score = temp_score
                            del best_solutions[:]  # Clean the list
                            best_solutions.append(
                                (temp_solution[available_period[0]], temp_solution[available_period[1]]))
                        elif temp_score == current_score:
                            best_solutions.append(
                                (temp_solution[available_period[0]], temp_solution[available_period[1]]))
            else:
                # Check if the internship have an available_period
                if available_period in available_periods_of_internship:
                    # Copy the original solution of the student
                    temp_solution = copy.copy(solution[student])
                    # And create the new solution with the new internship
                    temp_solution[available_period] = SolutionsLine(student,
                                                                    choice.organization,
                                                                    choice.speciality,
                                                                    available_period,
                                                                    choice.choice,
                                                                    type_of_internship)
                    # Compute the score of the new solution
                    temp_score = get_student_solution_cost(temp_solution)
                    temp_solution[available_period].cost = temp_score
                    # Check if the new solution is better than old
                    if temp_score < current_score:
                        current_score = temp_score
                        del best_solutions[:]  # Clean the list
                        best_solutions.append(temp_solution[available_period])
                    elif temp_score == current_score:
                        best_solutions.append(temp_solution[available_period])
    return best_solutions


def get_best_choice(choices, priority):
    """
    This method iterate over the choices of the student,
    if no choice is available a new organization is imposed to the student.
    If many choices have the same score we will chose the choice witch have more available places.
    :param choices: List of the choices of the student
    :param priority: True if the student is a social student, false otherwise
    :return: Best choice
    """
    is_emergency = False
    if choices[0].speciality.acronym.strip() == "UR":
        is_emergency = True

    # Iterate over all choices
    best_solutions = iterate_choices(choices, priority, is_emergency)

    # All 4 choices are unavailable
    if len(best_solutions) == 0:
        # If the student's internship is marked as a social internship
        if priority:
            # Add directly the hospital error
            imposed_choice = [StudentChoice(choices[0].student,
                                            organizations[hospital_error],
                                            choices[0].speciality,
                                            'X',
                                            choices[0].priority)]
            best_solutions = iterate_choices(imposed_choice, priority, is_emergency)
        else:
            # If the student is a normal student, we will try to find the nearest available hospital
            # In the exclude set we will store all hospital that we already tried to use
            exclude = set()
            while True:
                organization = find_nearest_hospital(choices[0].student, choices[0].speciality, exclude)
                # If we tried all hospital and none is available, we impose the hospital "error"
                if organization is None:
                    organization = organizations[hospital_error]
                    imposed_choice = [StudentChoice(choices[0].student,
                                                    organization,
                                                    choices[0].speciality,
                                                    'X',
                                                    choices[0].priority)]
                else:
                    imposed_choice = [StudentChoice(choices[0].student,
                                                    organization,
                                                    choices[0].speciality,
                                                    'I',
                                                    choices[0].priority)]

                best_solutions = iterate_choices(imposed_choice, priority, is_emergency)
                if len(best_solutions) > 0 or organization is None:
                    break
                else:
                    exclude.add(organization)
    # If only one solution exists, we return it directly
    if len(best_solutions) == 1:
        return best_solutions[0]
    # Otherwise check which solution has more available places
    elif len(best_solutions) > 1:
        max_places = -sys.maxsize - 1
        best_solutions_filtered = []
        for sol in best_solutions:
            if is_emergency:
                c0 = sol[0]
                c1 = sol[1]
                available_places = internship_table[c0.organization][c0.speciality][c0.period]
                available_places += internship_table[c1.organization][c1.speciality][c1.period]
            else:
                available_places = internship_table[sol.organization][sol.speciality][sol.period]
            if available_places > max_places:
                max_places = available_places
                # Clean the list
                del best_solutions_filtered[:]
                best_solutions_filtered.append(sol)
            elif available_places == max_places:
                best_solutions_filtered.append(sol)
        return choice(best_solutions_filtered)


def fill_erasmus_choices():
    """
    Fill the solution with all erasmus internships
    :return:
    """
    # Retrieve all students
    erasmus_enrollments = InternshipEnrollment.objects.all().select_related("student", "period", "internship_offer")
    for enrol in erasmus_enrollments:
        # Check if the internship is available
        if is_internship_available(enrol.place, enrol.internship_offer.speciality, enrol.period.name):
            solution[enrol.student][enrol.period.name] = SolutionsLine(enrol.student,
                                                                       enrol.internship_offer.organization,
                                                                       enrol.internship_offer.speciality,
                                                                       enrol.period.name,
                                                                       "E",
                                                                       "E")
            # Decrease the number of available places
            decrease_available_places(enrol.place, enrol.internship_offer.speciality, enrol.period.name)


def fill_emergency_choices(priority):
    """
    Fill the solution with emergency choices.
    :param priority: True if the student is a social student, false otherwise
    """
    data = get_student_mandatory_choices(priority)
    if emergency in data:
        # Start with "Emergency"
        emergency_students = data.pop(emergency)
        # Shift the students
        shifted_students = shift_array(emergency_students)
        # Iterate over each choice
        for choices in shifted_students:
            # Get the best choice
            try:
                choice = get_best_choice(choices, priority)
            except Exception as error:
                # Ignore the error and continue
                continue
            if choice is not None:
                choice0 = choice[0]
                choice1 = choice[1]
                # Add choice to the solution
                solution[choice0.student][choice0.period] = choice0
                solution[choice1.student][choice1.period] = choice1
                # Decrease the available places
                decrease_available_places(choice0.organization, choice0.speciality, choice0.period)
                decrease_available_places(choice1.organization, choice1.speciality, choice1.period)
                # Update the score of the solution
                update_scores(choice0.student)


def fill_normal_choices(priority):
    """
    Fill the solution with the choices of all specialities except emergency
    :param priority: True if the student is a social student, false otherwise
    """
    global errors
    data = get_student_mandatory_choices(priority)
    # Remove emergency from the dict
    if emergency in data:
        data.pop(emergency)
    # Then do others specialities
    for speciality, students in data.items():
        # Shift the students
        shifted_students = shift_array(students)
        for choices in shifted_students:
            # Get the best choice
            try:
                choice = get_best_choice(choices, priority)
            except Exception as error:
                # Ignore the error and continue
                continue
            if choice is not None:
                # Add choice to the solution
                solution[choice.student][choice.period] = choice
                # Decrease the available places
                decrease_available_places(choice.organization, choice.speciality, choice.period)
                # Update the score of the solution
                update_scores(choice.student)
                # Add hospital error to list "errors"
                if choice.choice == 'X':
                    errors.append((choice.student, choice.speciality, choice.period, choices, priority))


def swap_empty_internships():
    """
    Try to eliminate the empty internships by finding the internship that can be swapped.
    """
    empty_internships = []
    # Find all empty internships
    for organization, specialities in internship_table.items():
        # Do this only for standard organizations
        if int(organization.reference) < 500:
            for speciality, periods in specialities.items():
                for period, places in periods.items():
                    # Check if the internship is empty
                    if places > 0 and places == internship_table_original[organization][speciality][period]:
                        # Ignore the "MI" speciality
                        if speciality.acronym.strip() != "MI":
                            # Add the internship to list of empty internships
                            empty_internships.append((organization, speciality, period, places))
                            # Find all choices of student in the "Organization" and "speciality"
                            choices = InternshipChoice.search(organization=organization, speciality=speciality)
                            # Iterate over all choices of students
                            for choice in choices:
                                if period in solution[choice.student]:
                                    student_sol = solution[choice.student][period]
                                    # We can swap only non priority students
                                    if choice.priority is False and student_sol.speciality == speciality:
                                        # Check if we can increase the number of the available students
                                        if int(internship_table[student_sol.organization][student_sol.speciality][
                                                   period]) + 1 < \
                                                internship_table_original[student_sol.organization][
                                                    student_sol.speciality][
                                                    period]:
                                            # Increase the number of places of old internship
                                            increase_available_places(student_sol.organization, speciality, period)
                                            # Replace the internship
                                            solution[choice.student][period] = SolutionsLine(choice.student,
                                                                                             organization,
                                                                                             speciality,
                                                                                             period,
                                                                                             choice.choice,
                                                                                             "N")
                                            # Decrease new internship
                                            decrease_available_places(organization, speciality, period)
                                            break


def swap_errors():
    """
    Try to swap eliminate the errors by swapping 2 internships in the student solution
    """
    global errors, solution, internship_table
    # Iterate all errors
    for student, speciality, period, choices, priority in errors:
        # Get available periods of the speciality
        available_periods = set()
        for organization, specialities in internship_table.items():
            if int(organization.reference) < 500:
                # Check if the organization has the speciality
                if speciality in specialities:
                    for p, places in specialities[speciality].items():
                        # Check if the period is available
                        if is_internship_available(organization, speciality, p):
                            # Add period the available periods list
                            available_periods.add(p)

        specialities_to_swap = []
        for available_period in available_periods:
            specialities_to_swap.append((solution[student][available_period].speciality, available_period))

        # Find if the specialities that take the available periods of the speciality
        internships_to_swap = []
        for organization, specialities in internship_table.items():
            if int(organization.reference) < 500:
                for sp, p in specialities_to_swap:
                    if sp in specialities and sp.acronym.strip() != "UR":
                        if is_internship_available(organization, sp, period):
                            internships_to_swap.append((p, sp, organization))

        if len(internships_to_swap) > 0:
            p, sp, organization = internships_to_swap[0]

            if priority:
                type_of_internship = "S"
            else:
                type_of_internship = "N"

            # Increase original internship (hospital error)
            increase_available_places(organizations[hospital_error], speciality, period)
            # Replace internship with error by new internship (other speciality)
            solution[student][period] = SolutionsLine(student, organization, sp, period, "I", type_of_internship)
            # Decrease new internship
            decrease_available_places(organization, sp, period)
            # Increase the places of old internship (internship with the speciality who replaces internship with error)
            increase_available_places(solution[student][p].organization, sp, p)
            # Remove old internship
            del solution[student][p]

            # Find new internship
            choice = get_best_choice(choices, priority)
            if choice is not None:
                # Add choice to the solution
                solution[choice.student][choice.period] = choice
                # Decrease the available places
                decrease_available_places(choice.organization, choice.speciality, choice.period)
                # Update the score of the solution
                update_scores(choice.student)


def generate_solution():
    """
    Generate the new solution and save it in the database
    """
    global errors, solution, internship_table, internship_table_mi, organizations, specialities_dict, \
        distance_students, internship_offer_dic, organization_addresses_dic, internship_table_original

    # Clean all variables on at begging of each iteration
    errors = []
    solution = {}
    internship_table = {}
    internship_table_mi = {}
    organizations = {}
    specialities_dict = {}
    distance_students = {}
    internship_offer_dic = {}  #
    organization_addresses_dic = {}
    internship_table_original = {}

    init_solution()
    internship_table = init_internship_table()
    init_organizations()
    init_specialities()
    fill_erasmus_choices()
    fill_emergency_choices(True)
    fill_emergency_choices(False)
    fill_normal_choices(True)
    fill_normal_choices(False)
    swap_errors()
    # swap_empty_internships()


def save_solution():
    """
    Save the solution in the database
    :return:
    """
    global solution, internship_table
    # Remove old result from the database
    InternshipStudentAffectationStat.objects.all().delete()
    periods = Period.search().order_by('id')

    for student, internships in solution.items():
        for period, internship in internships.items():
            internship.period = periods[get_number_of_period(internship.period) - 1]
            sol_line = create_solution_line(internship.student,
                                            internship.organization,
                                            internship.speciality,
                                            internship.period,
                                            internship.choice,
                                            internship.type_of_internship,
                                            internship.cost,
                                            internship.consecutive_month)
            sol_line.save()


def load_solution(data):
    """ Create the solution and internship_table from db data """
    # Initialise the table of internships.
    period_internship_places = PeriodInternshipPlaces.objects.order_by("period_id").select_related()
    # This object store the number of available places for given organization, speciality, period
    temp_internship_table = defaultdict(dict)
    for pid in period_internship_places:
        organization = pid.internship.organization
        acronym = pid.internship.speciality.acronym
        period_name = pid.period.name
        if acronym not in temp_internship_table[organization]:
            temp_internship_table[organization][acronym] = OrderedDict()
        temp_internship_table[organization][acronym][period_name] = {}
        temp_internship_table[organization][acronym][period_name]['before'] = pid.number_places
        temp_internship_table[organization][acronym][period_name]['after'] = pid.number_places

    sol = {}
    keys = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12']
    for item in data:
        # Initialize 12 empty period of each student
        if item.student not in sol:
            sol[item.student] = OrderedDict()
            sol[item.student] = {key: None for key in keys}
            # Sort the periods by name P1, P2, ...
            sol[item.student] = OrderedDict(sorted(sol[item.student].items(), key=lambda t: int(t[0][1:])))
            sol[item.student]['score'] = 0
        # Put the internship in the solution
        sol[item.student][item.period.name] = item
        # store the cost of each student
        sol[item.student]['score'] += item.cost
        # Update the number of available places for given organization, speciality, period
        temp_internship_table[item.organization][item.speciality.acronym][item.period.name]['after'] -= 1
        # Update the % of takes places
        temp_internship_table[item.organization][item.speciality.acronym][item.period.name]['pc'] = \
            temp_internship_table[item.organization][item.speciality.acronym][item.period.name]['after'] / \
            temp_internship_table[item.organization][item.speciality.acronym][item.period.name]['before'] * 100
    # Sort all student by the score (descending order)
    sorted_internship_table = []
    for organization, specialities in temp_internship_table.items():
        for speciality, periods in specialities.items():
            sorted_internship_table.append((int(organization.reference), speciality, periods))
    sorted_internship_table.sort(key=itemgetter(0))

    return sol, sorted_internship_table


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_affectation_statistics_generate(request):
    """ Generate new solution, save it in the database, redirect back to the page 'internship_affectation_statistics'"""
    if request.method == 'POST':
        if request.POST['executions'] != "":
            cost = sys.maxsize
            for i in range(0, int(request.POST['executions'])):
                generate_solution()
                new_cost = get_solution_cost()
                if new_cost < cost:
                    save_solution()
                    cost = new_cost
        return HttpResponseRedirect(reverse('internship_affectation_statistics'))


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_affectation_statistics(request):
    init_organizations()
    init_specialities()
    sol, table, stats, internship_errors = None, None, None, None
    data = InternshipStudentAffectationStat.objects.all().select_related("student", "organization", "speciality",
                                                                         "period")
    visible = False
    if len(data) > 0:
        visible = data[0].visible
        sol, table = load_solution(data)
        stats = compute_stats(sol)
        # Mange sort of the students
        sol = OrderedDict(sorted(sol.items(), key=lambda t: t[0].person.last_name))
        # Mange sort of the organizations
        table.sort(key=itemgetter(0))
        internship_errors = InternshipStudentAffectationStat.objects.filter(organization=organizations[hospital_error])
    return render(request, "internship_affectation_statics.html",
                  {'section': 'internship',
                   'recap_sol': sol,
                   'stats': stats,
                   'organizations': table,
                   'errors': internship_errors,
                   'visible': visible})


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def internship_affectation_sumup(request):
    all_speciality = list(InternshipSpeciality.search(mandatory=True))
    all_speciality=set_speciality_unique(all_speciality)
    set_tabs_name(all_speciality)
    periods = Period.search()
    organizations = Organization.search()
    organizations = sort_organizations(organizations)
    offers = InternshipOffer.search()
    informations = []
    for organization in organizations:
        for offer in offers:
            if offer.organization.reference == organization.reference:
                informations.append(offer)

    for x in range (0,len(informations)):
        if informations[x] != 0:
            if informations[x].speciality.acronym == "MI":
                informations[x+1] = 0
                informations[x+2] = 0

    informations = [x for x in informations if x != 0]

    all_affectations = list(InternshipStudentAffectationStat.search())
    affectations = {}
    for speciality in all_speciality:
        temp_affectations = {}
        for period in periods:
            temp_temp_affectations = []
            for aff in all_affectations:
                if aff.speciality.acronym==speciality.acronym and aff.period==period:
                    temp_temp_affectations.append(aff)
            temp_affectations[period.name] = temp_temp_affectations
        affectations[speciality.name] = temp_affectations

    return render(request, "internship_affectation_sumup.html",
                  {'section': 'internship',
                   'specialities': all_speciality,
                   'periods': periods,
                   'organizations': informations,
                   'affectations': affectations,
                   })


@login_required
@permission_required('internship.is_internship_manager', raise_exception=True)
def display_affectations(request):
    affectations = InternshipStudentAffectationStat.search()
    if affectations:
        # Get the value of the first affectation in the DB
        affectation_visible = affectations[0].visible
    # For each affectation in the DB invert the selectable flag of the first affectation

    for affectation in affectations:
        edit_affectation = InternshipStudentAffectationStat.find_by_id(affectation.id)
        edit_affectation.visible = not affectation_visible
        edit_affectation.save()
    return HttpResponseRedirect(reverse('internships_home'))
