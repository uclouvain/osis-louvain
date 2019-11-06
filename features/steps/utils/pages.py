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
import time
from abc import ABC

import pypom
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from base.models.entity_version import EntityVersion
from features.steps.utils.fields import InputField, SubmitField, SelectField, ButtonField, \
    Checkbox, Select2Field, Link, \
    CkeditorField, RadioField, Field, SelectEntityVersionField


class AjaxModal(pypom.Page, ABC):
    def loaded(self):
        return self.find_element(By.ID, "form-modal-ajax-content")


class SuccessMessageRegion(pypom.Region):
    _root_locator = (By.ID, 'pnl_succes_messages')

    def loaded(self):
        return self.root.is_displayed()

    @property
    def text(self):
        return self.root.text


class CommonPageMixin:
    @property
    def success_messages(self):
        region = SuccessMessageRegion(self)
        region.wait_for_region_to_load()
        return region


class QuickSearchPage(AjaxModal):
    code = InputField(By.ID, 'id_search_text')
    search = ButtonField(By.CSS_SELECTOR, '#form-modal > div > div.col-md-1.col-md-offset-2 > button', 1)
    select_first = ButtonField(
        By.CSS_SELECTOR,
        '#form-modal-ajax-content > div.modal-body > div.row > div > table > tbody > tr > td:nth-child(1) > button'
    )

    lu_tab = ButtonField(By.CSS_SELECTOR, '#form-modal-ajax-content > div.modal-body > ul > li:nth-child(1) > a', 1)

    eg_tab = ButtonField(By.CSS_SELECTOR, '#form-modal-ajax-content > div.modal-body > ul > li:nth-child(2) > a')

    close = Link('EducationGroupPage', By.CSS_SELECTOR, '#form-modal-ajax-content > div.modal-header > button')


class LoginPage(pypom.Page):
    URL_TEMPLATE = '/login/'

    username = InputField(By.ID, 'id_username')
    password = InputField(By.ID, 'id_password')
    submit = SubmitField(By.ID, 'post_login_btn')

    def login(self, username, password='password123'):
        self.username = username
        self.password = password
        self.submit.click()


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
    entite_resp_cahier_des_charges = Select2Field(
        By.XPATH, "//*[@id='LearningUnitYearForm']/div[2]/div[1]/div[2]/div/div/div[3]/div/span")
    entite_dattribution = Select2Field(
        By.XPATH, "//*[@id='LearningUnitYearForm']/div[2]/div[1]/div[2]/div/div/div[4]/div/span")
    save_button = Link("LearningUnitPage", By.ID, 'btn-confirm', 2)


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
        value_0 = EntityVersion.objects.get(acronym=value[:3]).pk
        self._dossier_0 = value_0
        self._dossier_1 = value[3:]


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
    edit_button = Link('LearningUnitEditPage', By.CSS_SELECTOR, "#link_edit_lu > a")
    proposal_edit = Link(EditLearningUnitProposalPage, By.CSS_SELECTOR, "#link_proposal_modification > a")
    edit_proposal_button = Link(EditLearningUnitProposalPage, By.CSS_SELECTOR, "#link_proposal_edit > a")
    proposal_suppression = Link(LearningUnitProposalEndYearPage, By.CSS_SELECTOR, "#link_proposal_suppression > a")
    new_partim = Link(NewPartimPage, By.ID, "new_partim")
    go_to_full = ButtonField(By.ID, "full_acronym")

    credits = Field(By.ID, "id_credits")
    annee_academique = Field(By.ID, "id_end_year")
    tab_training = Link(LearningUnitTrainingPage, By.ID, "training_link")
    tab_attribution = Link(LearningUnitAttributionPage, By.ID, "attributions_link")
    tab_description = Link(DescriptionPage, By.ID, "description_link")
    tab_specification = Link(SpecificationPage, By.ID, "specification_link")

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
    quadrimestre = SelectField(By.ID, "id_quadrimester")
    session_derogation = SelectField(By.ID, "id_session")

    save_button = ButtonField(By.CSS_SELECTOR,
                              "#main > div.panel.panel-default > div.panel-heading > div > div > div > button")

    no_postponement = Link(LearningUnitPage, By.ID, "btn_without_postponement")
    with_postponement = Link(LearningUnitPage, By.ID, "btn_with_postponement")


class SearchLearningUnitPage(CommonPageMixin, pypom.Page):
    URL_TEMPLATE = '/learning_units/by_activity/'

    proposal_search = Link('SearchLearningUnitPage', By.ID, 'lnk_proposal_search', 1)

    anac = SelectField(By.ID, 'id_academic_year_id')
    acronym = InputField(By.ID, 'id_acronym')
    code = InputField(By.ID, 'id_acronym')
    tutor = InputField(By.ID, 'id_tutor')
    sigle_dossier = SelectField(By.ID, "id_entity_folder_id")

    requirement_entity = InputField(By.ID, 'id_requirement_entity_acronym')
    ent_charge = InputField(By.ID, 'id_requirement_entity_acronym')
    container_type = SelectField(By.ID, 'id_container_type')
    clear_button = ButtonField(By.ID, 'btn_clear_filter')

    search = Link('SearchLearningUnitPage', By.CSS_SELECTOR, 'button.btn-primary', 2)
    export = ButtonField(By.ID, "dLabel")
    list_learning_units = ButtonField(By.ID, "btn_produce_xls_with_parameters")
    with_program = ButtonField(By.ID, "chb_with_grp")
    with_tutor = ButtonField(By.ID, "chb_with_attributions")
    generate_xls = ButtonField(By.ID, "btn_xls_with_parameters")

    actions = ButtonField(By.ID, 'btn-action')
    new_luy = Link(NewLearningUnitPage, By.ID, 'lnk_learning_unit_create')
    create_proposal_url = Link(NewLearningUnitProposalPage, By.ID, 'lnk_create_proposal_url')

    # TODO this action is really slow.
    back_to_initial_yes = Link(
        'SearchLearningUnitPage', By.CSS_SELECTOR,
        '#modalBackToInitial > div > div > div.modal-footer > button.btn.btn-primary', 4
    )

    consolidate_yes = Link(
        'SearchLearningUnitPage', By.CSS_SELECTOR,
        '#modalConsolidate > div > div > div.modal-footer > button.btn.btn-primary', 4
    )

    def count_result(self):
        text = self.find_element(By.CSS_SELECTOR, "#main > div.panel.panel-default > div > strong").text
        return text.split()[0]

    def find_acronym_in_table(self, row: int=1):
        selector = '#table_learning_units > tbody > tr:nth-child({}) > td.col-acronym > a'.format(row)
        return self.find_element(By.CSS_SELECTOR, selector).text


class CopyModalPage(AjaxModal):
    copy_btn = Link('AttachModalPage', By.CSS_SELECTOR, '.modal-footer > .btn-primary', 1)


class DetachModalPage(AjaxModal):
    save_modal = Link('EducationGroupPage', By.CSS_SELECTOR, '.modal-footer > .btn-danger', 6)


class AttachModalPage(AjaxModal):
    type_de_lien = SelectField(By.ID, 'id_link_type')
    save_modal = Link('EducationGroupPage', By.CSS_SELECTOR, '.modal-footer > .btn-primary', 6)


class EducationGroupPage(CommonPageMixin, pypom.Page):
    sigleintitule_abrege = Field(
        By.CSS_SELECTOR,
        '#identification > div > div > div.row > div.col-md-7 > div:nth-child(1) > div > div.row > dl:nth-child(1) > dd'
    )
    code = Field(
        By.CSS_SELECTOR,
        '#identification > div > div > div.row > div.col-md-7 > div:nth-child(1) > div > div.row > dl:nth-child(2) > dd'
    )
    entite_de_gestion = Field(
        By.CSS_SELECTOR,
        '#identification > div > div > div.row > div.col-md-5 > div:nth-child(1) > div > dl:nth-child(1) > dd'
    )
    entite_dadministration = Field(
        By.CSS_SELECTOR,
        '#identification > div > div > div.row > div.col-md-5 > div:nth-child(1) > div > dl:nth-child(2) > dd'
    )
    actions = ButtonField(By.ID, 'dLabel')

    modify = Link('UpdateTrainingPage', By.CSS_SELECTOR, '#link_update > a', 1)
    delete = ButtonField(By.CSS_SELECTOR, '#link_delete > a', 1)
    select_first = ButtonField(By.CSS_SELECTOR, "#select_li > a", 1)

    confirm_modal = Link('SearchEducationGroupPage', By.CSS_SELECTOR, '.modal-footer>input[type=submit]')

    toggle_tree = ButtonField(By.CSS_SELECTOR, '#panel-data > div.panel-heading > div > a')
    open_first_node_tree = ButtonField(By.CSS_SELECTOR, '#panel_file_tree > ul > li > i')

    quick_search = Link(QuickSearchPage, By.ID, 'quick-search', 1)
    save_modal = Link('EducationGroupPage', By.CSS_SELECTOR, '.modal-footer > .btn-primary', 4)

    attach = Link(CopyModalPage, By.CSS_SELECTOR, 'body > ul > li:nth-child(4) > a', 2)
    detach = Link(DetachModalPage, By.CSS_SELECTOR, 'body > ul > li:nth-child(5) > a', 2)

    def get_name_first_children(self) -> list:
        children = self.find_elements(By.CSS_SELECTOR, '#panel_file_tree > ul > li > ul > li')
        return [child.text for child in children]

    def find_node_tree_by_acronym(self, acronym, parent=None):
        if not parent:
            parent = self
        else:
            parent = self.find_node_tree_by_acronym(parent)

        for node in parent.find_elements(By.CSS_SELECTOR, 'li.jstree-node'):
            if acronym == node.text.split('-')[0].strip():
                return node
        raise Exception("Node not found")

    def open_node_tree_by_acronym(self, acronym):
        node = self.find_node_tree_by_acronym(acronym)
        node.find_element(By.CSS_SELECTOR, 'i').click()

    def rigth_click_node_tree(self, acronym, parent=None):
        node = self.find_node_tree_by_acronym(acronym, parent)

        actionChains = ActionChains(self.driver)
        child = node.find_element(By.CSS_SELECTOR, 'a')
        actionChains.context_click(child).perform()
        return child

    def attach_node_tree(self, acronym, parent=None):
        self.rigth_click_node_tree(acronym, parent)
        return self.attach.click()

    def detach_node_tree(self, acronym, parent=None):
        self.rigth_click_node_tree(acronym, parent)
        return self.detach.click()

    def select_node_tree(self, acronym, parent=None):
        self.rigth_click_node_tree(acronym, parent)
        self.find_element(By.CSS_SELECTOR, 'body > ul > li:nth-child(1) > a').click()
        time.sleep(1)

    @property
    def loaded(self) -> bool:
        return "Identification" in self.find_element(
            By.CSS_SELECTOR, 'li.active[role=presentation]'
        ).text and not self.find_element(By.ID, 'modal_dialog_id').is_displayed()


class NewTrainingPage(pypom.Page):
    sigleintitule_abrege = InputField(By.ID, 'id_acronym')
    code = InputField(By.ID, 'id_partial_acronym')
    intitule_en_francais = InputField(By.ID, 'id_title')
    entite_de_gestion = SelectEntityVersionField(By.ID, 'id_management_entity')
    entite_dadministration = SelectEntityVersionField(By.ID, 'id_administration_entity')
    intitule_du_diplome = InputField(By.ID, 'id_diploma_printing_title')

    tab_diploma = ButtonField(By.ID, 'lnk_diplomas_certificats')
    save_button = Link(EducationGroupPage, By.ID, 'btn-confirm', waiting_time=3)


class UpdateTrainingPage(NewTrainingPage):
    fin = InputField(By.ID, 'id_end_year')


class SearchEducationGroupPage(CommonPageMixin, pypom.Page):
    URL_TEMPLATE = '/educationgroups/'

    sigleintitule_abrege = InputField(By.ID, 'id_acronym')
    code = InputField(By.ID, 'id_partial_acronym')
    anac = SelectField(By.ID, 'id_academic_year')

    actions = ButtonField(By.ID, 'btn-action')
    new_training = ButtonField(By.CSS_SELECTOR, '#link_create_training > a', 1)
    new_mini_training = ButtonField(By.CSS_SELECTOR, '#link_create_mini_training > a', 1)

    first_row = Link('EducationGroupPage', By.CSS_SELECTOR,
                     '#table_education_groups > tbody > tr:nth-child(1) > td:nth-child(2) > a')

    type_de_formation = SelectField(By.ID, "id_name")
    confirm_modal = Link(NewTrainingPage, By.CSS_SELECTOR, '.modal-footer>input.btn-primary')
    clear_button = ButtonField(By.ID, 'btn_clear_filter')
    search = Link('SearchEducationGroupPage', By.CSS_SELECTOR, 'button.btn-primary', 1)

    quick_search = Link(QuickSearchPage, By.ID, 'quick-search', 1)

    def count_result(self):
        text = self.find_element(
            By.CSS_SELECTOR,
            '#main > div.panel.panel-default > div > div > div.row > div:nth-child(1)').text
        return text.split()[0]


class SearchEntityPage(CommonPageMixin, pypom.Page):
    URL_TEMPLATE = '/entities/'

    acronym = InputField(By.ID, 'id_acronym')
    title = InputField(By.ID, 'id_title')
    entity_type = SelectField(By.ID, "id_entity_type")

    search = ButtonField(By.ID, "bt_submit_entity_search")

    def find_acronym_in_table(self, row: int=1):
        return self.find_element(By.ID, 'td_entity_%d' % row).text


class SearchOrganizationPage(CommonPageMixin, pypom.Page):

    URL_TEMPLATE = '/organizations/'

    acronym = InputField(By.ID, 'id_acronym')
    name = InputField(By.ID, 'id_name')
    type = SelectField(By.ID, "id_type")

    search = ButtonField(By.ID, "bt_submit_organization_search")

    def find_acronym_in_table(self, row: int=1):
        return self.find_element(By.ID, 'td_organization_%d' % row).text


class SearchStudentPage(CommonPageMixin, pypom.Page):

    URL_TEMPLATE = '/students/'

    registration_id = InputField(By.ID, 'id_registration_id')
    name = InputField(By.ID, 'id_name')

    search = ButtonField(By.ID, "bt_submit_student_search")

    def find_registration_id_in_table(self, row: int=1):
        return self.find_element(By.ID, 'td_student_%d' % row).text

    def find_name_in_table(self):
        names = []
        row = 1
        last = False
        while not last:
            try:
                elt = self.find_element(By.ID, 'spn_student_name_%d' % row)
                names.append(elt.text)

                row += 1
            except NoSuchElementException as e:
                return names

        return names
