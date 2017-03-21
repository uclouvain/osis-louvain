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
from internship import models as mdl_internship


NUMBER_INTERNSHIPS = 4


class StudentWrapper:
    def __init__(self, student):
        self.student = student
        self.choices = []
        self.assignments = dict()
        self.internship_assigned = []
        self.specialities_by_internship = dict()
        self.priority = False
        self.enrollments = dict()
        self.cost = 0
        self.information = None

    def add_choice(self, choice):
        self.choices.append(choice)
        self.choices.sort(key=lambda a_choice: a_choice.choice, reverse=False)
        self.__update_specialities_by_internship(choice)
        self.__update_priority(choice)

    def set_information(self, information):
        self.information = information

    def get_contest(self):
        if self.information:
            return self.information.contest
        return None

    def add_enrollment(self, enrollment):
        key = enrollment.internship_choice
        self.enrollments[key] = self.enrollments.get(key, [])
        self.enrollments[key].append(enrollment)

    def has_priority(self):
        return self.priority

    def __update_priority(self, choice):
        if choice.priority:
            self.priority = True

    def __update_specialities_by_internship(self, choice):
        self.specialities_by_internship[choice.internship_choice] = choice.speciality

    def assign(self, period, organization, speciality, internship_choice, preference):
        period_name = period.name
        cost = self.__get_cost(internship_choice, preference)
        self.cost += cost
        self.assignments[period_name] = \
            mdl_internship.internship_student_affectation_stat.\
            InternshipStudentAffectationStat(period=period, organization=organization, speciality=speciality,
                                             student=self.student, choice=preference, cost=cost)
        self.internship_assigned.append(internship_choice)

    def assign_specific(self, assignment):
        self.cost += assignment.cost
        period_name = assignment.period.name
        self.assignments[period_name] = assignment
        self.internship_assigned.append(0)

    def has_internship_assigned(self, internship):
        return internship in self.internship_assigned

    def has_all_internships_assigned(self):
        return len(self.internship_assigned) == NUMBER_INTERNSHIPS

    def has_period_assigned(self, period_name):
        return period_name in self.assignments

    def get_assignments(self):
        return self.assignments.values()

    def get_internships_periods(self, internship, internship_choice):
        enrollments = self.enrollments.get(internship_choice, [])
        periods = filter(lambda enrollment: enrollment.internship_offer == internship, enrollments)
        periods = map(lambda enrollment: enrollment.period.name, periods)
        return list(periods)

    def selected_specialities(self):
        return list(set([choice.speciality for choice in self.choices]))

    def fill_assignments(self, periods, default_organization, cost=0):
        if not self.choices:
            return
        periods_not_assigned = filter(lambda p: p.name not in self.assignments, periods)
        for period in periods_not_assigned:
            internship, speciality = self.get_internship_with_speciality_not_assigned()
            self.assign(period, default_organization, speciality, internship, cost)

    def get_internship_with_speciality_not_assigned(self):
        internships_with_speciality_not_assigned = \
            filter(lambda intern_spec: self.has_internship_assigned(intern_spec[0]) is False,
                   self.specialities_by_internship.items())
        return next(internships_with_speciality_not_assigned, (0, self.choices[0].speciality))

    def get_choices_for_internship(self, internship):
        return filter(lambda choice: choice.internship_choice == internship, self.choices)

    def get_speciality_of_internship(self, internship):
        return self.specialities_by_internship.get(internship, None)

    def get_last_internship_assigned(self):
        if not self.internship_assigned:
            return 0
        return max(self.internship_assigned)

    @staticmethod
    def __get_cost(internship_choice, preference):
        if internship_choice == 0:
            return 10
        elif internship_choice == 5:
            return 5
        elif internship_choice == 6:
            return 10
        else:
            return preference - 1

    def reinitialize(self):
        self.assignments = dict()
        self.internship_assigned = []
        self.cost = 0


