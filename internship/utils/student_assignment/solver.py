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
import random

from internship import models as mdl_internship
from internship.utils.student_assignment.internship_wrapper import InternshipWrapper
from internship.utils.student_assignment.student_wrapper import StudentWrapper

MAX_PREFERENCE = 4
AUTHORIZED_PERIODS = ["P9", "P10", "P11", "P12"]
NUMBER_INTERNSHIPS = len(AUTHORIZED_PERIODS)
MAX_NUMBER_INTERNSHIPS = 6
REFERENCE_DEFAULT_ORGANIZATION = 999
REFERENCE_PERSONAL_ORGANIZATION = 601
AUTHORIZED_SS_SPECIALITIES = ["CHC", "DE", "GE", "GOC", "MI", "MP", "NA", "OP", "OR", "CO", "PEC", "PS", "PA", "URC",
                              "CU"]

UNAUTHORIZED_SPECIALITIES = ["SP", "SE"]


def affect_student(times=1):
    current_student_affectations = list(_load_current_students_affectations())
    solver = init_solver(current_student_affectations)
    best_assignments, best_cost = launch_solver(solver)
    for x in range(1, times):
        solver.reinitialize()
        solver.update_places(current_student_affectations)
        assignments, cost = launch_solver(solver)
        if cost < best_cost:
            best_assignments = assignments
            best_cost = cost
    save_assignments_to_db(best_assignments)


def init_solver(current_students_affectations):
    solver = Solver()

    solver.set_periods(_load_periods())
    solver.default_organization = _load_default_organization()
    solver.set_students(_load_students_and_choices())
    solver.set_offers(_load_internship_and_places())
    solver.update_places(current_students_affectations)

    return solver


def launch_solver(solver):
    solver.solve()
    return solver.get_solution()


def save_assignments_to_db(assignments):
    for affectation in assignments:
        affectation.save()


class Solver:
    """
        Solver to assign internships to students.
        It works by assigning first the priority students, then the generalists students and finally the specialists
        ones.
        For each group of students the solver must assign them 4 internships.
        For priority students, it try first to assign one of the four choices submitted for the internship 1 by order of
        preference. Then it does the same for all the others internships (2, 3, 4, 5 and 6) until 4 internships are
        assigned to the student. If we have exhausted all the choices of the students, we assign the "hôpital erreur" to
        the student for each internship not assigned.
        For generalists and specialists students, it works differently, we first try to assign all the four choices,
        if all choices cannot be assigned, we try to assign an internship of the same speciality of the choices. Also,
        when all choices are exhausted, we try to assign all possible offers to fill the internships not assigned.
        If with that, there is still internships not assigned, we assign at most one "stage personnel" to generalists
        and two to specialists. Then we assign "hôpital erreur".
    """
    def __init__(self):
        self.students_by_registration_id = dict()
        self.offers_by_organization_speciality = dict()
        self.offers_by_speciality = dict()
        self.periods = []
        self.default_organization = None
        self.personal_offer = None
        self.priority_students = []
        self.generalists_students = []
        self.specialists_students = []
        self.students_priority_lefts_to_assign = []
        self.generalists_students_lefts_to_assign = []
        self.specialists_students_lefts_to_assign = []

    def set_students(self, student_wrappers):
        self.students_by_registration_id = student_wrappers
        self.__classify_students(student_wrappers)

    def __classify_students(self, student_wrappers):
        for student_wrapper in student_wrappers.values():
            if student_wrapper.has_priority():
                self.priority_students.append(student_wrapper)
                self.students_priority_lefts_to_assign.append(student_wrapper)
            elif is_generalist(student_wrapper):
                self.generalists_students.append(student_wrapper)
                self.generalists_students_lefts_to_assign.append(student_wrapper)
            else:
                self.specialists_students.append(student_wrapper)
                self.specialists_students_lefts_to_assign.append(student_wrapper)

    def set_offers(self, internship_wrappers):
        self.offers_by_organization_speciality = internship_wrappers
        self.__init_offers_by_speciality(internship_wrappers)

    def __init_offers_by_speciality(self, offers):
        for offer in offers.values():
            if offer.internship.organization.reference == str(REFERENCE_PERSONAL_ORGANIZATION):
                self.personal_offer = offer
            speciality = offer.internship.speciality
            current_offers_for_speciality = self.offers_by_speciality.get(speciality.id, [])
            current_offers_for_speciality.append(offer)
            self.offers_by_speciality[speciality.id] = current_offers_for_speciality

    def set_periods(self, periods):
        self.periods = periods

    def update_places(self, student_affectations):
        for affectation in student_affectations:
            offer = self.get_offer(affectation.organization.id, affectation.speciality.id)
            student_wrapper = self.get_student(affectation.student.registration_id)
            if not offer or not student_wrapper:
                continue
            offer.occupy(affectation.period.name)
            student_wrapper.assign_specific(affectation)

    def get_student(self, registration_id):
        return self.students_by_registration_id.get(registration_id, None)

    def get_offer(self, organization_id, speciality_id):
        return self.offers_by_organization_speciality.get((organization_id, speciality_id), None)

    def get_solution(self):
        assignments = []
        cost = 0
        for student_wrapper in self.students_by_registration_id.values():
            for affectation in student_wrapper.get_assignments():
                assignments.append(affectation)
                cost += affectation.cost
        return assignments, cost

    def solve(self):
        self.__assign_choices(self.students_priority_lefts_to_assign)
        self.__assign_choices(self.generalists_students_lefts_to_assign)
        self.__assign_choices(self.specialists_students_lefts_to_assign)

    def __assign_choices(self, students_list):
        min_internship = 1
        max_internship = NUMBER_INTERNSHIPS
        for internship in range(min_internship, max_internship+1):
            students_to_assign = []
            random.shuffle(students_list)
            for student_wrapper in students_list:
                if student_wrapper.has_all_internships_assigned():
                    continue
                self.__assign_first_possible_offer(student_wrapper)
                students_to_assign.append(student_wrapper)
            students_list = students_to_assign
        return students_list

    def __assign_first_possible_offer(self, student_wrapper):
        last_internship_assigned = student_wrapper.get_last_internship_assigned()
        for internship in range(last_internship_assigned + 1, MAX_NUMBER_INTERNSHIPS+1):
            if self.__assign_choices_or_speciality_of_choices(student_wrapper, internship):
                return
        if not student_wrapper.has_priority() and self.__assign_first_possible_offer_to_student(student_wrapper):
            return
        self.__fill_student_assignment(student_wrapper)

    def __assign_choices_or_speciality_of_choices(self, student_wrapper, internship):
        if self.__assign_student_choices_for_internship(student_wrapper, internship):
            return True
        speciality = student_wrapper.get_speciality_of_internship(internship)
        if not speciality or student_wrapper.has_priority():
            return False
        if self.__assign_first_possible_offer_from_speciality_to_student(student_wrapper, speciality, internship):
            return True

    def __assign_student_choices_for_internship(self, student_wrapper, internship):
        internship_choices = student_wrapper.get_choices_for_internship(internship)
        for choice in internship_choices:
            preference = choice.choice
            internship_wrapper = self.get_offer(choice.organization.id, choice.speciality.id)
            if not internship_wrapper:
                continue
            if _assign_offer_to_student(internship_wrapper, internship, preference, student_wrapper):
                return True
        return False

    def __assign_first_possible_offer_from_speciality_to_student(self, student_wrapper, speciality, internship=0):
        offers = self.offers_by_speciality.get(speciality, [])
        offers_not_full = filter(lambda possible_offer: possible_offer.is_not_full(), offers)
        offers_permitted = filter(lambda o: is_permitted_offer(student_wrapper, o), offers_not_full)
        for offer in offers_permitted:
            _assign_offer_to_student(offer, internship, 0, student_wrapper)
        return False

    def __assign_first_possible_offer_to_student(self, student_wrapper):
        if self.__assign_speciality(student_wrapper):
            return True
        elif self.__assign_personal_offer(student_wrapper, 0):
            return True
        elif not is_generalist(student_wrapper) and self.__assign_personal_offer(student_wrapper, 1):
            return True
        return False

    def __assign_speciality(self, student_wrapper):
        specialities = self.offers_by_speciality.keys()
        for speciality in specialities:
            if self.__assign_first_possible_offer_from_speciality_to_student(student_wrapper, speciality):
                return True
        return False

    def __assign_personal_offer(self, student_wrapper, limit_personal_offer):
        if get_number_personal_offers(student_wrapper) <= limit_personal_offer:
            _assign_offer_to_student(self.personal_offer, 0, 0, student_wrapper)
            return True
        return False

    def __fill_student_assignment(self, student_wrapper):
        student_wrapper.fill_assignments(self.periods, self.default_organization)

    def reinitialize(self):
        self.generalists_students_lefts_to_assign = self.generalists_students[:]
        self.specialists_students_lefts_to_assign =  self.specialists_students[:]
        self.students_priority_lefts_to_assign = self.priority_students[:]
        for student_wrapper in self.specialists_students:
            student_wrapper.reinitialize()
        for student_wrapper in self.generalists_students:
            student_wrapper.reinitialize()
        for student_wrapper in self.priority_students:
            student_wrapper.reinitialize()
        for internship_wrapper in self.offers_by_organization_speciality.values():
            internship_wrapper.reinitialize()


def _get_valid_period(internship_wrapper, student_wrapper, internship):
    free_periods_name = internship_wrapper.get_free_periods()
    random.shuffle(free_periods_name)
    student_periods_possible = \
        filter(lambda period: student_wrapper.has_period_assigned(period) is False,
               free_periods_name)
    enrollments_periods = student_wrapper.get_internships_periods(internship_wrapper.internship, internship)
    if enrollments_periods:
        student_periods_possible = filter(lambda x: x in enrollments_periods, student_periods_possible)
    return next(student_periods_possible, None)


def is_permitted_offer(student_wrapper, internship_wrapper):
    if internship_wrapper.internship.speciality.acronym in UNAUTHORIZED_SPECIALITIES:
        return False
    if not is_generalist(student_wrapper):
        return True
    if internship_wrapper.internship.speciality.acronym not in AUTHORIZED_SS_SPECIALITIES:
        return False
    return True


def get_number_personal_offers(student_wrapper):
    assignments = student_wrapper.assignments
    number_personal_offers = 0
    for student_affectation in assignments.values():
        if student_affectation.organization.reference == str(REFERENCE_PERSONAL_ORGANIZATION):
            number_personal_offers += 1
    return number_personal_offers


def is_generalist(student_wrapper):
    return student_wrapper.get_contest() in ["SS", "GENERALIST"]


def _occupy_offer(free_period_name, internship_wrapper, student_wrapper, internship_choice, choice):
    period_places = internship_wrapper.occupy(free_period_name)
    student_wrapper.assign(period_places.period, period_places.internship.organization,
                           period_places.internship.speciality, internship_choice, choice)


def _assign_offer_to_student(internship_wrapper, internship, preference, student_wrapper):
    free_period_name = _get_valid_period(internship_wrapper, student_wrapper, internship)
    if not free_period_name:
        return False
    _occupy_offer(free_period_name, internship_wrapper, student_wrapper, internship, preference)
    return True


def _load_internship_and_places():
    offers_by_organization_speciality = dict()
    internships_periods_places = mdl_internship.period_internship_places.PeriodInternshipPlaces.objects.all()
    for period_places in filter_internships_period_places(internships_periods_places):
        internship = period_places.internship
        key = (internship.organization.id, internship.speciality.id)
        offers_by_organization_speciality[key] = offers_by_organization_speciality.get(key, InternshipWrapper(internship))
        offers_by_organization_speciality[key].set_period_places(period_places)
    return offers_by_organization_speciality


def filter_internships_period_places(internships_periods_places):
    return filter(lambda int_per_places: int_per_places.period.name.strip() in AUTHORIZED_PERIODS,
                  internships_periods_places)


def _load_students_and_choices():
    students_information_by_person_id = _load_student_information()
    students_by_registration_id = dict()
    student_choices = mdl_internship.internship_choice.get_non_mandatory_internship_choices()
    for choice in student_choices:
        student = choice.student
        key = student.registration_id
        students_by_registration_id[key] = students_by_registration_id.get(key, StudentWrapper(student))

        student_information = students_information_by_person_id.get(student.person.id, None)
        students_by_registration_id[key].set_information(student_information)

        students_by_registration_id[key].add_choice(choice)
    _load_student_enrollment(students_by_registration_id)
    return students_by_registration_id


def _load_student_information():
    students_information_by_person_id = dict()
    all_student_information = mdl_internship.internship_student_information.find_all()
    for student_information in all_student_information:
        students_information_by_person_id[student_information.person.id] = student_information
    return students_information_by_person_id


def _load_student_enrollment(students_by_registration_id):
    enrollments = mdl_internship.internship_enrollment.find_for_non_mandatory_internship()
    for enrollment in enrollments:
        student_wrapper = students_by_registration_id.get(enrollment.student.registration_id, None)
        if student_wrapper:
            student_wrapper.add_enrollment(enrollment)


def _load_current_students_affectations():
    student_affectations = \
        mdl_internship.internship_student_affectation_stat.find_non_mandatory_affectations()
    return filter(lambda stud_affectation: stud_affectation.period.name in AUTHORIZED_PERIODS,
                  student_affectations)


def _load_periods():
    periods = mdl_internship.period.Period.objects.all()
    return list(filter(lambda period: period.name.strip() in AUTHORIZED_PERIODS, periods))


def _load_default_organization():
    return mdl_internship.organization.Organization.objects.get(reference=REFERENCE_DEFAULT_ORGANIZATION)
