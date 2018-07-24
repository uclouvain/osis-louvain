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
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

from base.models.entity import Entity
from base.models.enums import offer_year_entity_type
from base.models.person import Person
from base.models.program_manager import is_program_manager
from base.models import person_entity
from osis_common.document import xls_build
from base.business.xls import get_name_or_username, convert_boolean


# List of key that a user can modify
DATE_FORMAT = '%d-%m-%Y'
DATE_TIME_FORMAT = '%d-%m-%Y %H:%M'
DESC = "desc"
WORKSHEET_TITLE = 'education_groups'
XLS_FILENAME = 'education_groups_filename'
XLS_DESCRIPTION = "list_education_groups"
EDUCATION_GROUP_TITLES = [str(_('academic_year_small')), str(_('code')), str(_('title')), str(_('type')),
                          str(_('entity')), str(_('code'))]
ORDER_COL = 'order_col'
ORDER_DIRECTION = 'order_direction'
#

WORKSHEET_TITLE_ADMINISTRATIVE = 'trainings'
XLS_FILENAME_ADMINISTRATIVE = 'training_administrative_data'
XLS_DESCRIPTION_ADMINISTRATIVE = "List of trainings, with administrative data"
EDUCATION_GROUP_TITLES_ADMINISTRATIVE = [
    str(_('management_entity')),
    str(_('TRAINING')),
    str(_('type')),
    str(_('academic_year_small')),
    str(_('Begining of course registration')),
    str(_('Ending of course registration')),

    "{} 1".format(str(_('Begining of exam registration'))),
    "{} 1".format(str(_('Ending of exam registration'))),
    "{} 1".format(str(_('marks_presentation'))),
    "{} 1".format(str(_('dissertation_presentation'))),
    "{} 1".format(str(_('DELIBERATION'))),
    "{} 1".format(str(_('scores_diffusion'))),

    "{} 2".format(str(_('Begining of exam registration'))),
    "{} 2".format(str(_('Ending of exam registration'))),
    "{} 2".format(str(_('marks_presentation'))),
    "{} 2".format(str(_('dissertation_presentation'))),
    "{} 2".format(str(_('DELIBERATION'))),
    "{} 2".format(str(_('scores_diffusion'))),

    "{} 3".format(str(_('Begining of exam registration'))),
    "{} 3".format(str(_('Ending of exam registration'))),
    "{} 3".format(str(_('marks_presentation'))),
    "{} 3".format(str(_('dissertation_presentation'))),
    "{} 3".format(str(_('DELIBERATION'))),
    "{} 3".format(str(_('scores_diffusion'))),

    str(_('Weighting')),
    str(_('Default learning unit enrollment')),

    str(_('chair_of_the_exam_board')),
    str(_('exam_board_secretary')),
    str(_('Exam board signatory')),
    str(_('signatory_qualification'))
]

SIGNATORIES = 'signatories'
SECRETARIES = 'secretaries'
PRESIDENTS = 'presidents'
NUMBER_SESSIONS = 3


def can_user_edit_administrative_data(a_user, an_education_group_year):
    """
    Edition of administrative data is allowed for user which have permission AND
            if CENTRAL_MANAGER: Check attached entities [person_entity]
            else Check if user is program manager of education group
    """
    if not a_user.has_perm("base.can_edit_education_group_administrative_data"):
        return False

    person = Person.objects.get(user=a_user)
    if person.is_central_manager() and _is_management_entity_linked_to_user(person, an_education_group_year):
        return True

    return is_program_manager(a_user, education_group=an_education_group_year.education_group)


def _is_management_entity_linked_to_user(person, an_education_group_year):
    entities = Entity.objects.filter(offeryearentity__education_group_year=an_education_group_year,
                                     offeryearentity__type=offer_year_entity_type.ENTITY_MANAGEMENT)

    return person_entity.is_attached_entities(person, entities)


def assert_category_of_education_group_year(education_group_year, authorized_categories):
    if education_group_year.education_group_type.category not in authorized_categories:
        raise PermissionDenied("Education group category is not correct.")


def create_xls(user, found_education_groups_param, filters, order_data):
    found_education_groups = ordering_data(found_education_groups_param, order_data)
    working_sheets_data = prepare_xls_content(found_education_groups)
    parameters = {xls_build.DESCRIPTION: XLS_DESCRIPTION,
                  xls_build.USER: get_name_or_username(user),
                  xls_build.FILENAME: XLS_FILENAME,
                  xls_build.HEADER_TITLES: EDUCATION_GROUP_TITLES,
                  xls_build.WS_TITLE: WORKSHEET_TITLE}

    return xls_build.generate_xls(xls_build.prepare_xls_parameters_list(working_sheets_data, parameters), filters)


def prepare_xls_content(found_education_groups):
    return [extract_xls_data_from_education_group(eg) for eg in found_education_groups]


def extract_xls_data_from_education_group(an_education_group):
    return [
        an_education_group.academic_year.name,
        an_education_group.acronym,
        an_education_group.title,
        an_education_group.education_group_type,
        an_education_group.management_entity_version.acronym,
        an_education_group.partial_acronym
    ]


def ordering_data(object_list, order_data):
    order_col = order_data.get(ORDER_COL)
    order_direction = order_data.get(ORDER_DIRECTION)
    reverse_direction = order_direction == DESC

    return sorted(list(object_list), key=lambda t: _get_field_value(t, order_col), reverse=reverse_direction)


def _get_field_value(instance, field):
    field_path = field.split('.')
    attr = instance
    for elem in field_path:
        try:
            attr = getattr(attr, elem) or ''
        except AttributeError:
            return None
    return attr


def create_xls_administrative_data(user, found_education_groups_param, filters, order_data):
    found_education_groups = ordering_data(found_education_groups_param, order_data)
    working_sheets_data = prepare_xls_content_administrative(found_education_groups)
    parameters = {xls_build.DESCRIPTION: XLS_DESCRIPTION_ADMINISTRATIVE,
                  xls_build.USER: get_name_or_username(user),
                  xls_build.FILENAME: XLS_FILENAME_ADMINISTRATIVE,
                  xls_build.HEADER_TITLES: EDUCATION_GROUP_TITLES_ADMINISTRATIVE,
                  xls_build.WS_TITLE: WORKSHEET_TITLE_ADMINISTRATIVE}

    return xls_build.generate_xls(xls_build.prepare_xls_parameters_list(working_sheets_data, parameters), filters)


def prepare_xls_content_administrative(found_education_groups):
    return [extract_xls_administrative_data_from_education_group(eg) for eg in found_education_groups]


def extract_xls_administrative_data_from_education_group(an_education_group):
    data = [
        an_education_group.management_entity_version.acronym,
        an_education_group.acronym,
        an_education_group.education_group_type,
        an_education_group.academic_year.name,
        _get_date(an_education_group.administrative_data, 'course_enrollment.dates.start_date',
                  DATE_FORMAT),
        _get_date(an_education_group.administrative_data, 'course_enrollment.dates.end_date',
                  DATE_FORMAT)]
    for session_number in range(NUMBER_SESSIONS):
        data.extend(_get_dates_by_session(an_education_group.administrative_data, session_number+1))
    data.extend([
        convert_boolean(an_education_group.weighting),
        convert_boolean(an_education_group.default_learning_unit_enrollment),
        names(an_education_group.administrative_data[PRESIDENTS]),
        names(an_education_group.administrative_data[SECRETARIES]),
        names(an_education_group.administrative_data[SIGNATORIES]),
        qualification(an_education_group.administrative_data[SIGNATORIES])]
    )
    return data


def names(representatives):
    return ', '.join([str(mandatory.person) for mandatory in representatives])


def qualification(signatories):
    return ', '.join([signatory.mandate.qualification for signatory in signatories if signatory.mandate.qualification])


def _get_date(administrative_data, keys_attribute, date_form):
    key1, key2, attribute = keys_attribute.split(".")

    if administrative_data[key1].get(key2):
        attr = getattr(administrative_data[key1].get(key2), attribute) or None
        if attr:
            return attr.strftime(date_form)
    return '-'


def _get_dates_by_session(administrative_data, session_number):
    session_name = "session{}".format(session_number)
    return (
        _get_date(administrative_data, "{}.{}.{}".format('exam_enrollments', session_name, 'start_date'), DATE_FORMAT),
        _get_date(administrative_data, "{}.{}.{}".format('exam_enrollments', session_name, 'end_date'), DATE_FORMAT),
        _get_date(administrative_data, "{}.{}.{}".format('scores_exam_submission', session_name, 'start_date'),
                  DATE_TIME_FORMAT),
        _get_date(administrative_data, "{}.{}.{}".format('dissertation_submission', session_name, 'start_date'),
                  DATE_FORMAT),
        _get_date(administrative_data, "{}.{}.{}".format('deliberation', session_name, 'start_date'), DATE_TIME_FORMAT),
        _get_date(administrative_data, "{}.{}.{}".format('scores_exam_diffusion', session_name, 'start_date'),
                  DATE_TIME_FORMAT)
    )
