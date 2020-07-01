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

from base.models.program_manager import ProgramManager
from features.forms.assessments import search_learning_units_form, encode_students_score_form, \
    double_encode_students_score_form, encode_xlsx_score
from features.pages.assessments import pages
from features.pages.common import LoginPage

use_step_matcher("parse")


@given("The program manager is logged")
def step_impl(context: Context):
    context.program_manager = ProgramManager.objects.all().order_by('?')[0]
    page = LoginPage(driver=context.browser, base_url=context.get_url('login')).open()
    page.login(context.program_manager.person.user.username)


@when("Go to score encoding home page")
def step_impl(context: Context):
    pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding')).open()


@when("Search learning units of the program manager offer")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding'))
    search_learning_units_form.fill_form(page, context.program_manager)
    page.submit()


@when("Go encode scores for a learning unit returned")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser, base_url=context.get_url('scores_encoding'))
    random.choice(page.results).encode()


@when("Submit score for one student")
def step_impl(context: Context):
    page = pages.ScoreEncodingFormPage(driver=context.browser)
    scores_encoded = encode_students_score_form.fill_one_student_score(page)
    page.submit()
    context.scores = scores_encoded


@then("Scores should be updated")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    context.test.assertScoresEqual(page.results, context.scores)


@when("Click on encode scores")
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
    context.scores = encode_students_score_form.fill_student_scores(page)
    page.submit()


@when("Clear all scores")
def step_impl(context: Context):
    page = pages.ScoreEncodingFormPage(driver=context.browser)
    context.scores = encode_students_score_form.clear_all_scores(page)
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
    context.scores = encode_xlsx_score.update_xlsx(full_path)


@when("Inject excel file")
def step_impl(context: Context):
    page = pages.ScoreEncodingPage(driver=context.browser)
    filename = page.get_excel_filename()
    full_path = os.path.join(context.download_directory, filename)
    page.inject_excel(full_path)


@when("Solve differences")
def step_impl(context: Context):
    page = pages.DoubleScoreEncodingFormPage(driver=context.browser)
    context.scores = double_encode_students_score_form.choose_final_scores(page)
    page.submit()


@when("Select tab via paper")
def step_impl(context: Context):
    page = pages.LearningUnitsPage(driver=context.browser)
    page.via_paper_link.click()


@when("Download pdf")
def step_impl(context: Context):
    page = pages.LearningUnitsViaPaperTabPage(driver=context.browser)
    row_chosen = random.choice(page.results)
    row_chosen.download_pdf()
    context.filename = "session_%s_%s_%s.pdf" % (
        page.academic_year.text.split("-")[0],
        page.number_session.text,
        row_chosen.code.text
    )


@then("Pdf should be present")
def step_impl(context: Context):
    full_path = os.path.join(context.download_directory, context.filename)
    context.test.assertTrue(os.path.exists(full_path), full_path)
