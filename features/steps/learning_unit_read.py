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

from behave import *
from behave.runner import Context
from selenium.webdriver.common.by import By

import program_management.views.tree.move

use_step_matcher("parse")


@when("Cliquer sur l'onglet Formations")
def step_impl(context):
    context.current_page = context.current_page.tab_training.click()


@then("Vérifier que l'unité d'enseignement est incluse dans {list_acronym}")
def step_impl(context, list_acronym):
    context.test.assertEqual(context.current_page.including_groups(), list_acronym.split(', '))


@then("Vérifier que {acronym} à la ligne {nb_row} a {nb_training} inscrits dont {nb_luy} à l'ue")
def step_impl(context, acronym, nb_row, nb_training, nb_luy):
    context.test.assertEqual(context.current_page.enrollments_row(nb_row), [acronym, nb_training, nb_luy])


@when("Cliquer sur l'onglet Enseignant·e·s")
def step_impl(context):
    context.current_page = context.current_page.tab_attribution.click()


@then("Vérifier que à la ligne {nb_row}, l'enseignant est bien {teacher} avec comme fonction {function} "
      "débutant en {start_year} pour une durée de {duration} ans avec un volume en Q1 de {vol_q1} et en Q2 de {vol_q2}")
def step_impl(context, nb_row, teacher, function, start_year, duration, vol_q1, vol_q2):
    # It is not possible to check the teacher with anonymized data.
    context.test.assertEqual(context.current_page.attribution_row(nb_row)[1:],
                             [function, start_year, duration, vol_q1, vol_q2])


@then("Vérifier que à la ligne {nb_row}, l'enseignant est bien {teacher} avec comme fonction {function} "
      "débutant en {start_year} pour une durée de {duration} ans")
def step_impl(context, nb_row, teacher, function, start_year, duration):
    context.test.assertEqual(context.current_page.attribution_row(nb_row), [teacher, function, duration])


@step("Cliquer sur le bouton « Gérer la répartition »")
def step_impl(context):
    context.current_page = context.current_page.manage_repartition.click()


@step("Cliquer sur « Ajouter sur l’année en cours » sur la ligne {row}")
def step_impl(context, row):
    context.current_page.find_corresponding_button(row).click()


@then("Vérifier que à la ligne {row}, l'enseignant a comme fonction {function} "
      "avec un volume en Q1 de {vol_q1} et en Q2 de {vol_q2}")
def step_impl(context, row, function, vol_q1, vol_q2):
    context.test.assertEqual(context.current_page.attribution_row(row)[1:], [function, vol_q1, vol_q2])


@when("Cliquer sur le bouton « Modifier » sur la ligne {row}")
def step_impl(context, row):
    context.current_page.find_edit_button(row).click()
    # Wait modal
    time.sleep(1)


@when("Cliquer sur l'onglet Fiche descriptive")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page = context.current_page.tab_description.click()


@step("Cliquer sur le bouton « Ajouter »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page.add_button.click()
    # Wait modal
    time.sleep(1)


@then("Vérifier que la  Méthode d'enseignement est à {value}")
def step_impl(context, value):
    """
    :type context: behave.runner.Context
    """
    context.test.assertEqual(context.current_page.find_element(By.ID, 'cms_text_fr_9').text, value)


@step("Vérifier que le support de cours possède bien {value}")
def step_impl(context, value):
    """
    :type context: behave.runner.Context
    """
    context.test.assertEqual(
        context.current_page.find_element(By.XPATH, '//*[@id="pedagogy"]/div[2]/div[2]/ul/li').text,
        value)


@when("Sélectionner l’onglet « Cahier des charges »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page = context.current_page.tab_specification.click()


@then("Vérifier que {value} est bien un thème abordé")
def step_impl(context, value):
    """
    :type context: behave.runner.Context
    """
    context.test.assertEqual(context.current_page.find_element(By.ID, 'cms_text_fr_0').text, value)


@when("Cliquer sur le bouton « Ajouter un autre »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page.add_button.click()
    time.sleep(1)


@step("Cliquer sur la « flèche vers le haut »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    program_management.views.tree.move.up.click()
    time.sleep(1)


@then("Vérifier que {value} est bien présent à la ligne {row} des acquis d'apprentissage.")
def step_impl(context, value, row):
    """
    :type context: behave.runner.Context
    """
    context.test.assertEqual(
        context.current_page.find_element(By.ID, 'cms_text_fr_achievement_{}'.format(int(row) - 1)).text, value
    )


@when("Cliquer sur le bouton « Oui, je confirme »")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.current_page = context.current_page.save_button.click()


@then("Vérifier que la unité d'enseignement {acronym} a bien été mise en proposition pour l'année {year}")
def step_impl(context, acronym, year):
    string_to_check = "{} ({})".format(acronym, year)
    context.test.assertIn(string_to_check, context.current_page.success_messages.text)


@then("Vérifier que une proposition de {proposal_type} a été faite pour l'unité d'enseignement {acronym}")
def step_impl(context, proposal_type, acronym):
    """
    :type context: behave.runner.Context
    """
    context.test.assertIn(acronym, context.current_page.success_messages.text)
    context.test.assertIn(proposal_type, context.current_page.success_messages.text)


@then("Vérifier que une proposition de {proposal_type} a été faite")
def step_impl(context: Context, proposal_type):
    """
    :type context: behave.runner.Context
    """
    context.test.assertIn(proposal_type, context.current_page.success_messages.text)


@step("Vérifier que l'année academique termine en {year}")
def step_impl(context, year):
    """
    :type context: behave.runner.Context
    """
    context.test.assertIn(year, context.current_page.find_element(By.ID, "id_end_year").text)


@step("Vérifier que l'année academique termine")
def step_impl(context: Context):
    context.test.assertIn(str(context.anac.year), context.current_page.find_element(By.ID, "id_end_year").text)


@then("Vérifier que le dossier {acronym} est bien {state}")
def step_impl(context, acronym, state):
    """
    :type context: behave.runner.Context
    """
    current_state = context.current_page.find_element(
        By.CSS_SELECTOR,
        "#table_learning_units > tbody > tr:nth-child(1) > td:nth-child(9)"
    ).text
    context.test.assertEqual(current_state.strip(), state.strip())


@then("Vérifier que {acronym} n'est pas en proposition.")
def step_impl(context, acronym):
    is_proposal = context.current_page.find_element(
        By.CSS_SELECTOR,
        '#table_learning_units > tbody > tr.odd > td:nth-child(10)'
    ).text
    context.test.assertEqual(is_proposal, "")
