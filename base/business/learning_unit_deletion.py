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
from assistant.models import tutoring_learning_unit_year
from base.models import entity_container_year
from base.models import learning_unit_enrollment, learning_unit_component, learning_class_year, \
    learning_unit_year as learn_unit_year_model

from base.models import person_entity
from base.models.enums import learning_container_year_types
from base.models.enums import learning_unit_year_subtypes
from django.utils.translation import ugettext_lazy as _

FACULTY_MANAGER_GROUP="faculty_managers"
CENTRAL_MANAGER_GROUP="central_managers"


def check_learning_unit_deletion(learning_unit):
    msg = {}

    for learning_unit_year in learn_unit_year_model.search(learning_unit=learning_unit).order_by('academic_year__year'):
        msg.update(check_learning_unit_year_deletion(learning_unit_year))

    return msg


def check_learning_unit_year_deletion(learning_unit_year):
    msg = {}

    enrollment_count = len(learning_unit_enrollment.find_by_learning_unit_year(learning_unit_year))
    if enrollment_count > 0:
        msg[learning_unit_year] = _("There is %(count)d enrollments in %(subtype)s %(acronym)s for the year %(year)s") \
                                  % {'subtype': _str_partim_or_full(learning_unit_year),
                                     'acronym': learning_unit_year.acronym,
                                     'year': learning_unit_year.academic_year,
                                     'count': enrollment_count}

    if learning_unit_year.subtype == learning_unit_year_subtypes.FULL and learning_unit_year.learning_container_year:
        msg.update(_check_related_partims_deletion(learning_unit_year.learning_container_year))

    for component in learning_unit_component.find_by_learning_unit_year(learning_unit_year):
        msg.update(_check_learning_unit_component_deletion(component))

    for group_element_year in learning_unit_year.find_list_group_element_year():
        msg.update(_check_group_element_year_deletion(group_element_year))

    for tutoring in tutoring_learning_unit_year.find_learning_unit_year(learning_unit_year=learning_unit_year):
        msg.update(_check_tutoring_learning_unit_year(tutoring))

    next_year = learning_unit_year.get_learning_unit_next_year()
    if next_year:
        msg.update(check_learning_unit_year_deletion(next_year))

    return msg


def _check_tutoring_learning_unit_year(tutoring):
    msg = {}

    if tutoring.mandate:
        msg[tutoring] = _(
            "%(subtype)s %(acronym)s is assigned to the assistant %(assistant)s for the year %(year)s") % {
                            'subtype': _str_partim_or_full(tutoring.learning_unit_year),
                            'acronym': tutoring.learning_unit_year.acronym,
                            'assistant': tutoring.mandate.assistant,
                            'year': tutoring.learning_unit_year.academic_year}

    return msg


def _check_group_element_year_deletion(group_element_year):
    msg = {}

    if group_element_year.parent:
        msg[group_element_year] = _(
            '%(subtype)s %(acronym)s is included in the group %(group)s of the program %(program)s for the year %(year)s') \
                                  % {'subtype': _str_partim_or_full(group_element_year.child_leaf),
                                     'acronym': group_element_year.child_leaf.acronym,
                                     'group': group_element_year.parent.acronym,
                                     'program': group_element_year.parent.education_group_type,
                                     'year': group_element_year.child_leaf.academic_year}

    return msg


def _check_learning_unit_component_deletion(l_unit_component):
    msg = {}

    for attribution_charge in l_unit_component.learning_component_year.get_attributions_charge():
        attribution = attribution_charge.attribution

        msg[attribution] = _("%(subtype)s %(acronym)s is assigned to %(tutor)s for the year %(year)s") % {
            'subtype': _str_partim_or_full(l_unit_component.learning_unit_year),
            'acronym': l_unit_component.learning_unit_year.acronym,
            'tutor': attribution.tutor,
            'year': l_unit_component.learning_unit_year.academic_year}

    return msg


def _check_related_partims_deletion(learning_container_year):
    msg = {}

    for partim in learning_container_year.get_partims_related():
        msg.update(check_learning_unit_year_deletion(partim))

    return msg


def can_delete_learning_unit_year(person, learning_unit_year):
    # Check person_entity linked
    requirement_entity_version = entity_container_year.find_requirement_entity(learning_unit_year.learning_container_year)
    entities_linked = person_entity.find_entities_by_person(person)
    if not requirement_entity_version or requirement_entity_version.entity not in entities_linked:
        return False
    return _can_delete_learning_unit_year_according_type(person.user, learning_unit_year)


def _can_delete_learning_unit_year_according_type(user, learning_unit_year):
    # Faculty manager can only delete other type than COURSE/INTERNSHIP/DISSERTATION
    if not user.groups.filter(name=CENTRAL_MANAGER_GROUP).exists() and \
            user.groups.filter(name=FACULTY_MANAGER_GROUP).exists():
        container_type = learning_unit_year.learning_container_year.container_type
        subtype = learning_unit_year.subtype

        return not(container_type == learning_container_year_types.COURSE and subtype == learning_unit_year_subtypes.FULL) \
               and container_type not in [learning_container_year_types.DISSERTATION, learning_container_year_types.INTERNSHIP]
    return True


def delete_learning_unit(learning_unit):
    msg = []

    first_learning_unit_year_to_delete = learn_unit_year_model.search(learning_unit=learning_unit) \
        .order_by('academic_year__year').first()
    if first_learning_unit_year_to_delete:
        msg.extend(delete_from_given_learning_unit_year(first_learning_unit_year_to_delete))

    learning_unit.delete()

    return msg


def delete_from_given_learning_unit_year(learning_unit_year):
    msg = []

    next_year = learning_unit_year.get_learning_unit_next_year()
    if next_year:
        msg.extend(delete_from_given_learning_unit_year(next_year))

    if learning_unit_year.learning_container_year and learning_unit_year.subtype == learning_unit_year_subtypes.FULL:
        msg.extend(_delete_learning_container_year(learning_unit_year.learning_container_year))

    for component in learning_unit_component.find_by_learning_unit_year(learning_unit_year):
        msg.extend(_delete_learning_unit_component(component))

    learning_unit_year.delete()

    msg.append(_("%(subtype)s %(acronym)s has been deleted for the year %(year)s")
               % {'subtype': _str_partim_or_full(learning_unit_year),
                  'acronym': learning_unit_year.acronym,
                  'year': learning_unit_year.academic_year})

    learning_unit_year.learning_unit.end_year = learning_unit_year.academic_year.year - 1

    return msg


def _delete_learning_container_year(learning_unit_container):
    msg = []

    for partim in learning_unit_container.get_partims_related():
        msg.extend(delete_from_given_learning_unit_year(partim))
    learning_unit_container.delete()

    return msg


def _delete_learning_unit_component(l_unit_component):
    msg = []

    msg.extend(_delete_learning_component_year(l_unit_component.learning_component_year))
    l_unit_component.delete()
    return msg


def _delete_learning_component_year(learning_component_year):
    msg = []

    for l_class_year in learning_class_year.find_by_learning_component_year(learning_component_year):
        l_class_year.delete()
        msg.append(_("The class %(acronym)s has been deleted for the year %(year)s")
                   % {'acronym': l_class_year,
                      'year': learning_component_year.learning_container_year.academic_year})
    learning_component_year.delete()

    return msg


def _str_partim_or_full(learning_unit_year):
    return _('The partim') if learning_unit_year.subtype == learning_unit_year_subtypes.PARTIM else _(
        'The learning unit')
