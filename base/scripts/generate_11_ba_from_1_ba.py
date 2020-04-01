# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import logging
import uuid
from copy import deepcopy

from django.conf import settings

from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.enums import duration_unit

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def run(*args):
    """
    Script can be runned with this command :
        python manage.py runscript generate_11_ba_from_1_ba --script-args "ABCD1BA"
    :param args: The acronym of the 1BA from which we will create the 11BA.
    """
    existing_acronym = args[0]
    generate_11_ba_from_1_ba(existing_acronym)


def generate_11_ba_from_1_ba(existing_acronym):
    """
    Script used to create 11BA from 1BA.
    :param existing_acronym: The acronym of the 1BA from which we will create the 11BA.
    """

    if '1BA' not in existing_acronym:
        logger.error(
            'This script is used to create 11BA from 1BA. Provided acronym must contain "1BA". Script will stop now.'
        )
        quit()

    new_acronym = existing_acronym.replace("1", "11")
    logger.info(
        "Starting script to create {} from {}.".format(new_acronym, existing_acronym)
    )

    try:
        source_eg = EducationGroup.objects.filter(educationgroupyear__acronym=existing_acronym).distinct().get()
    except EducationGroup.DoesNotExist:
        logger.error(
            "There is no education group with acronym {}. Script will stop now.".format(
                existing_acronym
            )
        )
        quit()

    number_of_existing_egy = EducationGroupYear.objects.filter(acronym=new_acronym).count()
    if number_of_existing_egy:
        logger.error(
            "{} education group year(s) with acronym {} already exist. Script will stop now.".format(
                number_of_existing_egy,
                new_acronym
            )
        )
        quit()

    logger.info("Found 1 source education_group : {}".format(source_eg))
    new_eg = deepcopy(source_eg)
    new_eg.pk = None
    new_eg.uuid = uuid.uuid4()
    new_eg.external_id = None
    new_eg.save()
    logger.info("Education group {} created from {}\n".format(new_eg, source_eg))

    source_egys = EducationGroupYear.objects.filter(acronym=existing_acronym)
    logger.info("Found {} source education_group_years :\n {}\n".format(
        source_egys.count(),
        "\n ".join([str(egy) for egy in source_egys]))
    )

    for egy in source_egys:
        logger.info("Starting to create education_group_year from source {} [ {} ]".format(egy.pk, egy))
        new_egy = deepcopy(egy)
        new_egy.pk = None
        new_egy.uuid = uuid.uuid4()
        new_egy.external_id = None

        new_egy.education_group = new_eg
        new_egy.acronym = new_acronym
        new_egy.partial_acronym = None
        new_egy.credits = None
        new_egy.duration = 2
        new_egy.duration_unit = duration_unit.DurationUnits.QUADRIMESTER.value
        new_egy.internship = None
        new_egy.joint_diploma = False
        new_egy.diploma_printing_title = ''

        #  Lowercase first letter of title ONLY in french (english title keeps the first letter uppercase)
        new_egy.title = "{} {}".format("Première année de", _lower_case_first_letter(egy.title))
        new_egy.title_english = "{} {}".format("First year of the", egy.title_english)

        new_egy.save()
        logger.info(
            "Education_group_year {} [ {} ] created from {} [ {} ]\n".format(new_egy.pk, new_egy, egy.pk, egy)
        )

    logger.info(
        "Script terminated successfully."
    )


def _lower_case_first_letter(string):
    return string[0].lower() + string[1:]
