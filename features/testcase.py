# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from behave_django.testcase import BehaviorDrivenTestCase
from django.utils.translation import gettext_lazy as _

from assessments.views import upload_xls_utils
from base.forms.utils import choice_field
from base.models import tutor
from base.models.enums import exam_enrollment_justification_type
from base.models.learning_unit_year import LearningUnitYear
from features.pages import learning_unit
from features.pages.learning_unit.pages import SearchLearningUnitPage


class OsisTestCase(BehaviorDrivenTestCase):
    def _fixture_teardown(self):
        pass

    def _flush_db(self):
        super()._fixture_teardown()

    def assertScoresEqual(self, page_results: list, scores_expected: list):
        for result, score in zip(page_results, scores_expected):
            if score.isdecimal():
                self.assertEqual(result.score.text, score)
                self.assertEqual(result.justification.text, "-")

            elif score in upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES:
                self.assertEqual(
                    result.score.text,
                    "-"
                )
                justification_value = get_enum_value(
                    exam_enrollment_justification_type.JUSTIFICATION_TYPES,
                    upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES[score]
                )
                self.assertEqual(
                    result.justification.text,
                    _(justification_value)
                )

    def assertLearningUnitResultsMatchCriteria(self, page_results: list, search_criteria: dict):
        acronym = search_criteria.get("acronym", "")
        requirement_entity = search_criteria.get("requirement_entity", "")
        container_type = search_criteria.get("container_type", "")

        for result in page_results:
            self.assertIn(acronym, result.acronym.text)
            self.assertIn(requirement_entity, result.requirement_entity.text)
            self.assertIn(container_type, result.type.text)

    def assertLearningUnitHasBeenUpdated(self, page: learning_unit.pages.LearningUnitPage, form_data: dict):
        status = _("Active") if form_data["actif"] else _("Inactive")
        session_derogation = form_data["session_derogation"] \
            if form_data["session_derogation"] != choice_field.BLANK_CHOICE_DISPLAY else '-'
        quadrimester = form_data["quadrimester"] \
            if form_data["quadrimester"] != choice_field.BLANK_CHOICE_DISPLAY else '-'
        credits = form_data.get("credits", "")
        periodicity = form_data.get("periodicity", "") \
            if form_data.get("periodicity", "") != choice_field.BLANK_CHOICE_DISPLAY else '-'

        self.assertEqual(page.status.text, status)
        self.assertEqual(page.session_derogation.text, session_derogation)
        self.assertEqual(page.quadrimester.text, quadrimester)
        self.assertIn(periodicity, page.periodicity.text)
        self.assertIn(str(credits), page.credits.text)


def get_enum_value(enum, key):
    return next(
        (v for k, v in enum if k == key),
        None
    )


def assert_tutor_match(
        results: SearchLearningUnitPage.LearningUnitElement,
        tutor_obj: tutor.Tutor,
        assertions
):
    if not tutor_obj:
        return None
    learning_unit_acronyms_present_in_page = set([result.acronym.text for result in results])
    if not learning_unit_acronyms_present_in_page:
        return None
    expected_luys = LearningUnitYear.objects.filter(
        learning_container_year__attributionnew__tutor=tutor_obj
    )
    assertions.assertEqual(
        {luy.acronym for luy in expected_luys},
        learning_unit_acronyms_present_in_page
    )
