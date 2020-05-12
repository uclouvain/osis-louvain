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

from base.models.entity_version import EntityVersion
from features.fields.fields import InputField, Link, SelectField, Select2Field, ButtonField, CkeditorField, \
    RadioField, Field, Checkbox, CharField
from features.pages.common import CommonPageMixin


class RepartitionPage(pypom.Page):
    volume_2 = InputField(By.ID, "id_practical_form-allocation_charge")
    save_button = Link('LearningUnitAttributionPage', By.ID, 'save_btn')

    def find_corresponding_button(self, row):
        return self.find_element(By.XPATH, '//*[@id="attributions"]/table/tbody/tr[{}]/td[6]/a'.format(row))


class LearningUnitAttributionPage(pypom.Page):
    manage_repartition = Link(RepartitionPage, By.ID, "manage_repartition")
    save_button = Link('LearningUnitAttributionPage', By.ID, 'save_btn', 3)
    volume_1 = InputField(By.ID, "id_lecturing_form-allocation_charge")

    def find_edit_button(self, row):
        return self.find_element(By.XPATH, '//*[@id="attributions"]/table/tbody/tr[{}]/td[6]/a[1]'.format(row))

    def attribution_row(self, row) -> list:
        result = []

        for i in range(1, 7):
            text = self.find_element(By.XPATH, "//*[@id='attributions']/table/tbody/tr[{}]/td[{}]".format(row, i)).text
            if text:
                result.append(text)

        return result

    @property
    def loaded(self):
        return "Enseignant·e·s" in self.find_element(By.CSS_SELECTOR, 'li.active[role=presentation]').text and \
               self.find_element(By.ID, "manage_repartition")


class LearningUnitTrainingPage(pypom.Page):
    def including_groups(self) -> list:
        row_count = len(self.find_elements(By.XPATH, "//*[@id='trainings']/table/tbody/tr"))
        groups = []
        for i in range(1, row_count + 1):
            groups.append(self.find_element(By.XPATH, '//*[@id="trainings"]/table/tbody/tr[{}]/td[1]/a'.format(i)).text)

        return groups

    def enrollments_row(self, row) -> list:
        result = []
        for i in range(1, 4):
            result.append(self.find_element(
                By.XPATH, "//*[@id='learning_unit_enrollments']/table/tbody/tr[{}]/td[{}]".format(
                    row, i)
            ).text)
        return result


class NewLearningUnitPage(pypom.Page):
    _code_0 = SelectField(By.ID, "id_acronym_0")
    _code_1 = InputField(By.ID, "id_acronym_1")

    @property
    def code(self):
        return self._code_0.text + self._code_1.text

    @code.setter
    def code(self, value):
        self._code_0 = value[0]
        self._code_1 = value[1:]

    type = SelectField(By.ID, "id_container_type")
    credit = InputField(By.ID, "id_credits")
    credits = InputField(By.ID, "id_credits")
    lieu_denseignement = SelectField(By.ID, "id_campus")
    intitule_commun = InputField(By.ID, "id_common_title")
    intitule_commun_english = InputField(By.ID, "id_common_title_english")
    entite_resp_cahier_des_charges = Select2Field(
        By.XPATH, "//*[@id='LearningUnitYearForm']/div[2]/div[1]/div[2]/div/div/div[3]/div/span")
    entite_dattribution = Select2Field(
        By.XPATH, "//*[@id='LearningUnitYearForm']/div[2]/div[1]/div[2]/div/div/div[4]/div/span")

    def __init__(self, *args, **kwargs):
        self.create_save_button()
        super().__init__(*args, **kwargs)

    @classmethod
    def create_save_button(cls):
        cls.save_button = Link(LearningUnitPage, By.ID, 'btn-confirm', 4)


class NewLearningUnitProposalPage(NewLearningUnitPage):
    etat = SelectField(By.ID, 'id_state')
    periodicite = SelectField(By.ID, "id_periodicity")
    annee_academique = SelectField(By.ID, 'id_academic_year')

    _dossier_0 = SelectField(By.ID, 'id_entity')
    _dossier_1 = InputField(By.ID, 'id_folder_id')

    @property
    def dossier(self):
        return self._dossier_0.text + self._dossier_1.text

    @dossier.setter
    def dossier(self, value):
        value_0 = EntityVersion.objects.get(acronym=value[:4]).pk
        self._dossier_0 = str(value_0)
        self._dossier_1 = value[4:]


class EditLearningUnitProposalPage(NewLearningUnitProposalPage):
    pass


class LearningUnitProposalEndYearPage(NewLearningUnitProposalPage):
    anac_de_fin = SelectField(By.ID, "id_academic_year")
    type = SelectField(By.ID, 'id_type')


class NewPartimPage(NewLearningUnitPage):
    code_dedie_au_partim = InputField(By.ID, "id_acronym_2")
    save_button = ButtonField(By.XPATH,
                              '//*[@id="LearningUnitYearForm"]/div[1]/div/div/div/button')


class DescriptionPage(pypom.Page):
    methode_denseignement = CkeditorField(By.CLASS_NAME, 'cke_wysiwyg_frame')

    add_button = ButtonField(By.XPATH, '//*[@id="pedagogy"]/div[2]/div[2]/div/a')
    save_button = Link('DescriptionPage', By.XPATH, '//*[@id="form-modal-ajax-content"]/form/div[3]/button[1]', 2)

    intitule = InputField(By.ID, 'id_title')
    support_obligatoire = RadioField(By.ID, 'id_mandatory')

    def find_edit_button(self, _):
        return self.find_element(By.XPATH, '//*[@id="pedagogy"]/table[1]/tbody/tr[2]/td[2]/a')


class SpecificationPage(pypom.Page):
    themes_abordes = CkeditorField(By.CLASS_NAME, 'cke_wysiwyg_frame')
    save_button = Link('SpecificationPage', By.CSS_SELECTOR, 'div.modal-footer > .btn-primary', 1)
    add_button = ButtonField(By.CSS_SELECTOR, '.btn.btn-primary.trigger_modal')

    code = InputField(By.ID, 'id_code_name')
    texte = CkeditorField(By.CLASS_NAME, 'cke_wysiwyg_frame')

    up = ButtonField(By.XPATH, '//*[@id="form_achievements"]/div[3]/div[1]/div/button[1]')

    def find_edit_button(self, _):
        # TODO hardcoded value for "Thèmes abordés"
        return self.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[2]/div/div/div[1]/div/div[2]/div[1]/a')


class LearningUnitPage(CommonPageMixin, pypom.Page):
    actions = ButtonField(By.ID, "dLabel")
    proposal_edit = Link(EditLearningUnitProposalPage, By.CSS_SELECTOR, "#link_proposal_modification > a")
    edit_proposal_button = Link(EditLearningUnitProposalPage, By.CSS_SELECTOR, "#link_proposal_edit > a")
    proposal_suppression = Link(LearningUnitProposalEndYearPage, By.CSS_SELECTOR, "#link_proposal_suppression > a")
    new_partim = Link(NewPartimPage, By.ID, "new_partim")
    go_to_full = ButtonField(By.ID, "full_acronym")

    code = Field(By.ID, "id_acronym")
    credits = Field(By.ID, "id_credits")
    status = CharField(By.ID, "id_status")
    quadrimester = Field(By.ID, "id_quadrimester")
    session_derogation = Field(By.ID, "id_session")
    periodicity = Field(By.ID, "id_periodicity")

    annee_academique = Field(By.ID, "id_end_year")
    tab_training = Link(LearningUnitTrainingPage, By.ID, "training_link")
    tab_attribution = Link(LearningUnitAttributionPage, By.ID, "attributions_link")
    tab_description = Link(DescriptionPage, By.ID, "description_link")
    tab_specification = Link(SpecificationPage, By.ID, "specification_link")

    proposal_state = Field(By.ID, "id_proposal_state")

    def __init__(self, *args, **kwargs):
        self._edit_button()
        self._consolidate_proposal()
        self._confirm_consolidate()
        super().__init__(*args, **kwargs)

    @classmethod
    def _edit_button(cls):
        cls.edit_button = Link(LearningUnitEditPage, By.CSS_SELECTOR, "#link_edit_lu > a")

    @classmethod
    def _consolidate_proposal(cls):
        cls.consolidate_proposal = Link(LearningUnitPage, By.CSS_SELECTOR, "#link_consolidate_proposal > a")

    @classmethod
    def _confirm_consolidate(cls):
        cls.confirm_consolidate = Link(LearningUnitPage, By.ID, "id_confirm_consolidate")

    def is_li_edit_link_disabled(self):
        return "disabled" in self.find_element(By.ID, "link_edit_lu").get_attribute("class")

    @property
    def loaded(self) -> bool:
        return "Identification" in self.find_element(By.CSS_SELECTOR, 'li.active[role=presentation]').text


class LearningUnitEditPage(pypom.Page):
    actif = Checkbox(By.ID, "id_status")
    periodicite = SelectField(By.ID, "id_periodicity")
    credits = InputField(By.ID, "id_credits")
    volume_q1_pour_la_partie_magistrale = InputField(By.ID, "id_component-0-hourly_volume_partial_q1")
    volume_q1_pour_la_partie_pratique = InputField(By.ID, "id_component-1-hourly_volume_partial_q1")
    volume_q2_pour_la_partie_magistrale = InputField(By.ID, "id_component-0-hourly_volume_partial_q2")
    volume_q2_pour_la_partie_pratique = InputField(By.ID, "id_component-1-hourly_volume_partial_q2")
    volume_total_pour_la_partie_magistrale = InputField(By.ID, "id_component-0-hourly_volume_total_annual")
    volume_total_pour_la_partie_pratique = InputField(By.ID, "id_component-1-hourly_volume_total_annual")
    classes_prevues_pour_la_partie_magistrale = InputField(By.ID, "id_component-0-planned_classes")
    classes_prevues_pour_la_partie_pratique = InputField(By.ID, "id_component-1-planned_classes")
    volume_entites_de_charges_pour_la_partie_magistrale = InputField(By.ID, "id_component-0-repartition_volume_requirement_entity")
    volume_entites_de_charges_pour_la_partie_pratique = InputField(By.ID, "id_component-1-repartition_volume_requirement_entity")
    quadrimestre = SelectField(By.ID, "id_quadrimester")
    session_derogation = SelectField(By.ID, "id_session")

    save_button = ButtonField(By.CSS_SELECTOR,
                              "#main > div.panel.panel-default > div.panel-heading > div > div > div > button")

    no_postponement = Link(LearningUnitPage, By.ID, "btn_without_postponement")
    with_postponement = Link(LearningUnitPage, By.ID, "btn_with_postponement")


class SearchLearningUnitPage(CommonPageMixin, pypom.Page):
    URL_TEMPLATE = '/learning_units/by_activity/'

    anac = SelectField(By.ID, 'id_academic_year')
    acronym = InputField(By.ID, 'id_acronym')
    code = InputField(By.ID, 'id_acronym')
    tutor = InputField(By.ID, 'id_tutor')
    sigle_dossier = SelectField(By.ID, "id_entity_folder_id")

    requirement_entity = InputField(By.ID, 'id_requirement_entity')
    ent_charge = InputField(By.ID, 'id_requirement_entity')
    container_type = SelectField(By.ID, 'id_container_type')
    clear_button = ButtonField(By.ID, 'btn_clear_filter')

    export = ButtonField(By.ID, "dLabel")
    list_learning_units = ButtonField(By.ID, "btn_produce_xls_with_parameters")
    with_program = ButtonField(By.ID, "chb_with_grp")
    with_tutor = ButtonField(By.ID, "chb_with_attributions")
    generate_xls = ButtonField(By.ID, "btn_xls_with_parameters")

    actions = ButtonField(By.ID, 'btn-action')
    new_luy = Link(NewLearningUnitPage, By.ID, 'lnk_learning_unit_create')
    create_proposal_url = Link(NewLearningUnitProposalPage, By.ID, 'lnk_create_proposal_url')

    _results_selector = (By.CSS_SELECTOR, '#table_learning_units > tbody > tr')

    def __init__(self, *args, **kwargs):
        self._back_to_initial_yes()
        self._proposal_search_creation()
        self._consolidate_yes()
        self._search()
        super().__init__(*args, **kwargs)

    @classmethod
    def _back_to_initial_yes(cls):
        cls.back_to_initial_yes = Link(
            SearchLearningUnitPage, By.CSS_SELECTOR,
            '#modalBackToInitial > div > div > div.modal-footer > button.btn.btn-primary', 4
        )

    @classmethod
    def _proposal_search_creation(cls):
        cls.proposal_search = Link(SearchLearningUnitPage, By.ID, 'lnk_proposal_search', 1)

    @classmethod
    def _consolidate_yes(cls):
        cls.consolidate_yes = Link(
            SearchLearningUnitPage, By.CSS_SELECTOR,
            '#modalConsolidate > div > div > div.modal-footer > button.btn.btn-primary', 4
        )

    @classmethod
    def _search(cls):
        cls.search = Link(SearchLearningUnitPage, By.CSS_SELECTOR, 'button.btn-primary', 2)

    class LearningUnitElement(pypom.Region):
        acronym = CharField(By.CSS_SELECTOR, "td:nth-child(2)")
        type = CharField(By.CSS_SELECTOR, "td:nth-child(4)")
        requirement_entity = CharField(By.CSS_SELECTOR, "td:nth-child(6)")

    class ProposalLearningUnitElement(pypom.Region):
        acronym = Link(LearningUnitPage, By.CSS_SELECTOR, "td:nth-child(3)")
        proposal_type = CharField(By.CSS_SELECTOR, "td:nth-child(8)")

    @property
    def results(self):
        return [self.LearningUnitElement(self, element) for element in self.find_elements(*self._results_selector)]

    @property
    def proposal_results(self):
        return [self.ProposalLearningUnitElement(self, element) for element in self.find_elements(*self._results_selector)]

    def count_result(self):
        text = self.find_element(By.CSS_SELECTOR, "#main > div.panel.panel-default > div > strong").text
        return text.split()[0]

    def find_acronym_in_table(self, row: int = 1):
        selector = '#table_learning_units > tbody > tr:nth-child({}) > td.col-acronym > a'.format(row)
        return self.find_element(By.CSS_SELECTOR, selector).text


class SearchProposalPage(SearchLearningUnitPage):
    URL_TEMPLATE = None
    proposal_type = SelectField(By.ID, 'id_proposal_type')
