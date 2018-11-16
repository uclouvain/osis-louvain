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
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import XLS_DESCRIPTION, XLS_FILENAME
from base.business.xls import get_name_or_username
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from osis_common.document import xls_build
from osis_common.document.xls_build import prepare_xls_parameters_list


def generate_xls_teaching_material(user, learning_units):
    """ Generate a XLS file with all filtered learning_units where the course material is required """

    titles = [
        str(_('code')).title(),
        str(_('Title')),
        str(_('Req. Entity')).title(),
        str(_('bibliography')).title(),
        str(_('teaching materials')).title(),
        str(_('online resources')).title(),
    ]

    file_parameters = {
        xls_build.DESCRIPTION: XLS_DESCRIPTION,
        xls_build.FILENAME: XLS_FILENAME,
        xls_build.USER: get_name_or_username(user),
        xls_build.HEADER_TITLES: titles,
        xls_build.WS_TITLE: _("Teaching material"),
    }

    working_sheets_data = _filter_required_teaching_material(learning_units)
    return xls_build.generate_xls(prepare_xls_parameters_list(working_sheets_data, file_parameters))


def _filter_required_teaching_material(learning_units):
    """ Apply a filter to return a list with only the learning units with at least one teaching material """
    result = []
    for learning_unit in learning_units:
        # Only learning_units with a required teaching material will be display
        if not learning_unit.teachingmaterial_set.filter(mandatory=True):
            continue

        # Fetch data in CMS
        bibliography = TranslatedText.objects.filter(
            text_label__label='bibliography',
            entity=LEARNING_UNIT_YEAR,
            reference=learning_unit.pk).first()

        online_resources = TranslatedText.objects.filter(
            text_label__label='online_resources',
            entity=LEARNING_UNIT_YEAR,
            reference=learning_unit.pk).first()

        result.append((
            learning_unit.acronym,
            learning_unit.complete_title,
            learning_unit.requirement_entity,
            # Let a white space, the empty string is converted in None.
            getattr(bibliography, "text", " "),
            ", ".join(learning_unit.teachingmaterial_set.filter(mandatory=True).values_list('title', flat=True)),
            getattr(online_resources, "text", " "),
        ))

    if not result:
        raise ObjectDoesNotExist

    return result
