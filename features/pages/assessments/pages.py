############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
import pypom
from selenium.webdriver.common.by import By

from features.fields import fields


class LearningUnitsPage(pypom.Page):
    training_select = fields.SelectField(By.ID, "slt_offer_list_selection")
    via_paper_link = fields.ButtonField(By.ID, "lnk_via_paper")
    _results_selector = (By.CLASS_NAME, "result")

    _submit_btn = fields.ButtonField(By.ID, "bt_submit_offer_search")

    def submit(self):
        self._submit_btn.click()

    @property
    def results(self):
        return [self.LearningUnitElement(self, el) for el in self.find_elements(*self._results_selector)]

    class LearningUnitElement(pypom.Region):
        _code_selector = (By.CSS_SELECTOR, "[headers=code]")
        _title_selector = (By.CSS_SELECTOR, "[headers=title]")
        _responsible_selector = (By.CSS_SELECTOR, "[headers=responsible]")
        _progress_selector = (By.CSS_SELECTOR, "[headers=progress]")
        _encode_selector = (By.CSS_SELECTOR, "[headers=encode]>a")

        _pdf_download = (By.CSS_SELECTOR, "[headers=download_action]>a")

        def encode(self):
            self.find_element(*self._encode_selector).click()

        def download_pdf(self):
            self.find_element(*self._pdf_download).click()


class LearningUnitsViaPaperTabPage(pypom.Page):
    academic_year = fields.CharField(By.ID, "academic_year")
    number_session = fields.CharField(By.ID, "number_session")
    training_select = fields.SelectField(By.ID, "slt_offer_list_selection")
    _results_selector = (By.CLASS_NAME, "result_paper")

    _submit_btn = fields.ButtonField(By.ID, "bt_submit_offer_search")

    def submit(self):
        self._submit_btn.click()

    @property
    def results(self):
        return [self.LearningUnitElement(self, el) for el in self.find_elements(*self._results_selector)]

    class LearningUnitElement(pypom.Region):
        code = fields.CharField(By.CSS_SELECTOR, "[headers=code]")
        _title_selector = (By.CSS_SELECTOR, "[headers=title]")
        _responsible_selector = (By.CSS_SELECTOR, "[headers=responsible]")
        _progress_selector = (By.CSS_SELECTOR, "[headers=progress]")

        _pdf_download = (By.CSS_SELECTOR, "[headers=download_action]>a")

        def download_pdf(self):
            self.find_element(*self._pdf_download).click()


class ScoreEncodingFormPage(pypom.Page):
    _results_selector = (By.CLASS_NAME, "result")
    _submit_btn = fields.ButtonField(By.CSS_SELECTOR, "button[type=submit]")

    def submit(self):
        self._submit_btn.click()

    @property
    def results(self):
        return [self.ScoreElement(self, el) for el in self.find_elements(*self._results_selector)]

    class ScoreElement(pypom.Region):
        score = fields.InputField(By.CSS_SELECTOR, "[headers=score]>input[type=text]")

        _status_selector = (By.CSS_SELECTOR, "[headers=code]")
        _program_selector = (By.CSS_SELECTOR, "[headers=program]")
        _registration_number_selector = (By.CSS_SELECTOR, "[headers=registration_number]")
        _lastname_selector = (By.CSS_SELECTOR, "[headers=lastname]")
        _firstname_selector = (By.CSS_SELECTOR, "[headers=firstname]")
        _score_selector = (By.CSS_SELECTOR, "[headers=score]")
        _justification_selector = (By.CSS_SELECTOR, "[headers=justification]")
        _deadline_selector = (By.CSS_SELECTOR, "[headers=deadline]")

        @property
        def lastname(self):
            return self.find_element(*self._lastname_selector).text


class DoubleScoreEncodingFormPage(pypom.Page):
    _results_selector = (By.CLASS_NAME, "result")
    _submit_btn = fields.ButtonField(By.ID, "bt_submit_online_double_encoding_validation")

    def submit(self):
        self._submit_btn.click()

    @property
    def results(self):
        return [self.ScoreElement(self, el) for el in self.find_elements(*self._results_selector)]

    class ScoreElement(pypom.Region):
        _program_selector = (By.CSS_SELECTOR, "[headers=program]")
        _registration_number_selector = (By.CSS_SELECTOR, "[headers=registration_number]")
        _lastname_selector = (By.CSS_SELECTOR, "[headers=lastname]")
        _firstname_selector = (By.CSS_SELECTOR, "[headers=firstname]")

        score_1 = fields.InputField(By.CSS_SELECTOR, "[headers=score_1]>input")
        justification_1 = fields.CharField(By.CSS_SELECTOR, "[headers=justification_1]>div")
        _validate_button_1 = fields.ButtonField(By.CSS_SELECTOR, "[headers=justification_1]>button")

        score_2 = fields.InputField(By.CSS_SELECTOR, "[headers=score_2]>input")
        justification_2 = fields.CharField(By.CSS_SELECTOR, "[headers=justification_2]>div")
        _validate_button_2 = fields.ButtonField(By.CSS_SELECTOR, "[headers=justification_2]>button")

        score_final = fields.CharField(By.CSS_SELECTOR, "[headers=score_final]>div")
        justification_final = fields.CharField(By.CSS_SELECTOR, "[headers=justification_final]>div")

        def validate(self, n):
            if n == 1:
                self._validate_button_1.click()
            else:
                self._validate_button_2.click()


class ScoreEncodingPage(pypom.Page):
    _results_selector = (By.CLASS_NAME, "result")
    _encode_btn = fields.ButtonField(By.ID, "lnk_encode")
    _double_encode_btn = fields.ButtonField(By.ID, "lnk_online_double_encoding")
    _excel_btn = fields.ButtonField(By.ID, "lnk_scores_excel")
    _inject_excel_btn = fields.ButtonField(By.ID, "bt_upload_score_modal")
    _page_title = fields.CharField(By.CLASS_NAME, "panel-title")
    _number_session = fields.CharField(By.ID, "number_session")
    _academic_year = fields.CharField(By.ID, "academic_year")

    _file_upload_input = fields.InputField(By.ID, "fle_scores_input_file")
    _submit_file = fields.ButtonField(By.ID, "bt_submit_upload_score_modal")

    def encode(self):
        self._encode_btn.click()

    def double_encode(self):
        self._double_encode_btn.click()

    def download_excel(self):
        self._excel_btn.click()

    def inject_excel(self, filepath):
        self._inject_excel_btn.click()
        self._file_upload_input.element.send_keys(filepath)
        self._submit_file.click()

    def get_excel_filename(self):
        academic_year = self._academic_year.text.split("-")[0]
        learning_unit_acronym = self._page_title.text.split()[-1]
        number_session = self._number_session.text
        return 'session_{}_{}_{}.xlsx'.format(academic_year, number_session, learning_unit_acronym)

    @property
    def results(self):
        return [self.ScoreElement(self, el) for el in self.find_elements(*self._results_selector)]

    class ScoreElement(pypom.Region):
        score = fields.CharField(By.CSS_SELECTOR, "[headers=score]")
        justification = fields.CharField(By.CSS_SELECTOR, "[headers=justification]")

        _status_selector = (By.CSS_SELECTOR, "[headers=code]")
        _program_selector = (By.CSS_SELECTOR, "[headers=program]")
        _registration_number_selector = (By.CSS_SELECTOR, "[headers=registration_number]")
        _lastname_selector = (By.CSS_SELECTOR, "[headers=lastname]")
        _firstname_selector = (By.CSS_SELECTOR, "[headers=firstname]")
        _score_selector = (By.CSS_SELECTOR, "[headers=score]")
        _deadline_selector = (By.CSS_SELECTOR, "[headers=deadline]")
