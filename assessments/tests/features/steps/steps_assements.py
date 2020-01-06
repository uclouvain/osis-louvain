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
import os
import random

from behave import *
from behave.runner import Context
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from openpyxl import load_workbook

from assessments.tests.features import pages
from assessments.views import upload_xls_utils
from base.models.enums import exam_enrollment_justification_type
from base.models.program_manager import ProgramManager
from features.steps.utils.pages import LoginPage

use_step_matcher("parse")


@given("The program manager is logged")
def step_impl(context: Context):
    context.program_manager = ProgramManager.objects.all().order_by('?')[0]
    perm = Permission.objects.filter(codename="can_access_scoreencoding").first()
    context.program_manager.person.user.user_permissions.add(perm)
    page = LoginPage(driver=context.browser, base_url=context.get_url('login')).open()
    page.login(context.program_manager.person.user.username)


@when("Go to score encoding home page")
def step_impl(context: Context):
    pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding')).open()


@when("Select user offer")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding'))
    page.training_select = context.program_manager.offer_year.id
    page.submit()


@when("Click on encode")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding'))
    page.results[0].encode()


@when("Fill score for one student")
def step_impl(context: Context):
    page = pages.ScoreEncodingFormPage(driver=context.browser)
    page.results[0].score = str(12)
    page.submit()
    context.scores = [str(12)]


@then("Modification should be visible")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    for result, score in zip(page.results, context.scores):
        if score.isdecimal():
            context.test.assertEqual(result.score.text, score)
            context.test.assertEqual(result.justification.text, "-")
        elif score in upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES:
            context.test.assertEqual(result.score.text, "-")
            justification_value = get_enum_value(
                exam_enrollment_justification_type.JUSTIFICATION_TYPES,
                upload_xls_utils.AUTHORIZED_JUSTIFICATION_ALIASES[score]
            )
            context.test.assertEqual(
                result.justification.text,
                _(justification_value)
            )


@when("Click on encode bis")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    page.encode()


@when("Click on double encode")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    page.double_encode()


@when("Fill all scores")
def step_impl(context: Context):
    page = pages.ScoreEncodingFormPage(driver=context.browser)
    results = page.results
    context.scores = [str(random.randint(0, 20)) for i in range(20)]
    for result, score in zip(results, context.scores):
        result.score = score
    page.submit()


@when("Clear all scores")
def step_impl(context: Context):
    page = pages.ScoreEncodingFormPage(driver=context.browser)
    results = page.results
    context.scores = ["" for i in range(20)]
    for result, score in zip(results, context.scores):
        result.score = score
    page.submit()


@when("Download excel")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    page.download_excel()


@then("Excel should be present")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    filename = page.get_excel_filename()
    full_path = os.path.join(context.download_directory, filename)
    context.test.assertTrue(os.path.exists(full_path), full_path)


@when("Fill excel file")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    filename = page.get_excel_filename()
    full_path = os.path.join(context.download_directory, filename)
    context.scores = update_xlsx(full_path)


@when("Inject excel file")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    filename = page.get_excel_filename()
    full_path = os.path.join(context.download_directory, filename)
    page.inject_excel(full_path)


@when("Solve differences")
def step_impl(context: Context):
    page = pages.DoubleScoreEncodingFormPage(driver=context.browser)
    validations = [random.randint(1, 2) for i in range(20)]
    for result, validation in zip(page.results, validations):
        if result.score_1.text != result.score_2.text:
            result.validate(validation)
    context.scores = [result.score_final.text for result in page.results]
    page.submit()


@when("Select tab via paper")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser)
    page.via_paper_link.click()


@when("Download pdf")
def step_impl(context: Context):
    page = pages.LearningUnitsViaPaperTabPage(driver=context.browser)
    page.results[0].download_pdf()
    context.filename = "session_%s_%s_%s.pdf" % (
        page.academic_year.text.split("-")[0],
        page.number_session.text,
        page.results[0].code.text
    )


@then("Pdf should be present")
def step_impl(context: Context):
    full_path = os.path.join(context.download_directory, context.filename)
    context.test.assertTrue(os.path.exists(full_path), full_path)


@when("suspend")
def step_impl(context: Context):
    import time
    time.sleep(10)


def update_xlsx(filename):
    wb = load_workbook(filename)

    sheet = wb.active
    scores = []

    current_row = 13
    while sheet['E{}'.format(current_row)].value:
        score_or_justification = bool(random.getrandbits(1))
        selected_column = 'I' if score_or_justification else 'J'

        if score_or_justification:
            value = str(random.randint(0, 20))
        else:
            value = random.choice(('A', 'T'))

        sheet['{}{}'.format(selected_column, current_row)] = value
        scores.append(value)
        current_row += 1

    wb.save(filename=filename)
    return scores


def get_enum_value(enum, key):
    return next(
        (v for k, v in enum if k == key),
        None
    )
