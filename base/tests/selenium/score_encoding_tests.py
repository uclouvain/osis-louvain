##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
# designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
"""
File that contains all the selenium tests for the scores encoding.
Each class represent a specific feature to test.
Most of the time a feature need tata to be on a specific state; for that reason the database
is reconstructed on the class level.
Data will be injected for specific state.
"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.select import Select

from backoffice.settings import FIREFOX_PROFILE_PATH
from base.tests.selenium.util import get_element_by_id, assert_is_element_present, assert_is_enabled, login_as,\
    log_out


class ScoreEncodingTests(StaticLiveServerTestCase):
    """
    This class test the sending of a message to all the tutors of a learning_unit ,
     after the score encoding is submitted.
    All the previous states of this business feature are supposed to be done.
    We only test the fact that after the submission , a mail is sent
    """

    fixtures = ['base/fixtures/score_encoding_base.json', 'base/fixtures/messages_templates.json']

    @classmethod
    def setUpClass(cls):
        """
        Initialisation for all the testCase , done only once
        - Initialise Firefox driver
        - Maximize browser window
        """
        capabilities = {
            'javascriptEnabled': True,
        }
        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE_PATH)
        cls.selenium = webdriver.Firefox(firefox_profile=profile, capabilities=capabilities)
        cls.selenium.implicitly_wait(3)
        cls.selenium.maximize_window()
        super(ScoreEncodingTests, cls).setUpClass()

    def setUp(self):
        """
        Initialisation For each test:
        """
        self.verificationErrors = []

    @classmethod
    def tearDownClass(cls):
        """
        - close selenium conexion
        """
        cls.selenium.quit()
        # dump_data_after_tests(['auth','base'],'score_encoding')
        super(ScoreEncodingTests, cls).tearDownClass()

    def test_score_encoding(self):
        """
        Test the encoding mechanism.
        - Encode as a professor
        - Encode as a coordinator
        - Double encode
        - Test decimal encoding
        - Test message sending after submission
        """
        self.__test_encode_as_professor()
        self.__test_encode_as_coordinator()
        self.__test_double_encoding()
        self.__test_decimal_encoding()
        self.__sent_message_after_submission()

    def __test_encode_as_professor(self):
        """
        Test the encoding of scores as a professor
        :param self: The class used to make the tests
        """

        # Log in as prof3
        login_as(self, 'prof3')

        # Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()

        # Check if all the learning units are there
        assert_is_element_present(self, True, 'lnk_encode_LBIR1320B')
        assert_is_element_present(self, True, 'lnk_encode_LSINF1211')
        assert_is_element_present(self, True, 'lnk_encode_LPSPG1021')

        # Encode on a learning unit
        get_element_by_id(self, 'lnk_encode_LBIR1320B').click()
        # #Fill one score
        get_element_by_id(self, 'num_score_14').send_keys('15')
        Select(get_element_by_id(self, 'slt_justification_score_29')).select_by_value('ABSENT')
        # #Save and assert it's done (button save is not present anymore)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')

        # Professor cannot submit partial scores
        assert_is_enabled(self, False, 'bt_score_submission_modal')

        # #While sores are not submited, they can be changed
        # #First we test with the same user
        get_element_by_id(self, 'lnk_encode').click()
        get_element_by_id(self, 'num_score_14').clear()
        get_element_by_id(self, 'num_score_14').send_keys('13')
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        # #Then we test with another professor
        log_out(self)
        login_as(self, 'prof5')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        # #We test with an already saved score
        get_element_by_id(self, 'lnk_encode_LBIR1320B').click()
        get_element_by_id(self, 'num_score_14').clear()
        get_element_by_id(self, 'num_score_14').send_keys('15')
        # #We test that he can encode not already encoded score
        get_element_by_id(self, 'num_score_44').send_keys('14')
        # #Save and assert it's done (button save is not present anymore)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')

        # Encode all scores and submit scores (with one justification)
        # #Encode all scores
        get_element_by_id(self, 'lnk_encode').click()
        get_element_by_id(self, 'num_score_59').send_keys('14')
        get_element_by_id(self, 'num_score_74').send_keys('14')
        Select(get_element_by_id(self, 'slt_justification_score_89')).select_by_value('CHEATING')
        get_element_by_id(self, 'num_score_104').send_keys('14')
        get_element_by_id(self, 'num_score_119').send_keys('14')
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        # #Professor cannot submit complete scores
        assert_is_enabled(self, False, 'bt_score_submission_modal')
        log_out(self)

    def __test_encode_as_coordinator(self):
        """
        Test the encoding of score as coordinator
        """
        login_as(self, 'coord2')

        # Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()

        # Check if all the learning units are there
        assert_is_element_present(self, True, 'lnk_encode_LDUAL4367')
        assert_is_element_present(self, True, 'lnk_encode_LBIR2000A')

        # Encode on a learning unit
        get_element_by_id(self, 'lnk_encode_LDUAL4367').click()
        # #Fill one score
        get_element_by_id(self, 'num_score_83').send_keys('15')
        Select(get_element_by_id(self, 'slt_justification_score_113')).select_by_value('SCORE_MISSING')
        # #Save and assert it's done (button save is not present anymore)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')

        # As a coordinator ,i can submit partial encoding
        assert_is_enabled(self, True, 'bt_score_submission_modal')
        get_element_by_id(self, 'bt_score_submission_modal').submit()
        get_element_by_id(self, 'lnk_post_scores_submission_btn').click()

        # Once scores are partially submitted , the already submitted scores can not be encoded anymore
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        get_element_by_id(self, 'lnk_encode_LDUAL4367').click()
        assert_is_enabled(self, False, 'num_score_83')
        assert_is_enabled(self, False, 'slt_justification_score_113')
        # #We can still encode not submitted notes
        # #As a coordinator
        get_element_by_id(self, 'num_score_68').send_keys('15')
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')
        log_out(self)
        # #And as a professor
        login_as(self, 'prof2')
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        get_element_by_id(self, 'lnk_encode_LDUAL4367').click()
        # #Assert submitted scores are not enabled
        assert_is_enabled(self, False, 'num_score_83')
        assert_is_enabled(self, False, 'slt_justification_score_113')
        # #Encode not submitted
        get_element_by_id(self, 'num_score_8').send_keys('12')
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')
        log_out(self)

        # Test if scores encoded by professor are submitable
        login_as(self, 'coord3')
        # Submitt the scores
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        get_element_by_id(self, 'lnk_LBIR1320B').click()
        get_element_by_id(self, 'bt_score_submission_modal').submit()
        get_element_by_id(self, 'lnk_post_scores_submission_btn').click()

        # Once scores are submitted it is not possible to encode scores
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        assert_is_enabled(self, False, 'lnk_encode_LBIR1320B')
        log_out(self)

    def __test_double_encoding(self):
        """
        Test the double encoding mechanism
        """
        # Log as coordinator
        login_as(self, 'coord3')

        # Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()

        # Encode on a learning unit
        get_element_by_id(self, 'lnk_encode_LSINF1211').click()
        # #Fill one score
        get_element_by_id(self, 'num_score_92').send_keys('14,3')
        Select(get_element_by_id(self, 'slt_justification_score_137')).select_by_value('SCORE_MISSING')
        # #Save and assert it's done (button save is not present anymore)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')

        # Submit partilally encoded scores
        get_element_by_id(self, 'bt_score_submission_modal').submit()
        get_element_by_id(self, 'lnk_post_scores_submission_btn').click()

        log_out(self)

        # Log as professor
        login_as(self, 'prof3')
        # Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        get_element_by_id(self, 'lnk_LSINF1211').click()

        # Double Encode on a learning unit
        get_element_by_id(self, 'lnk_online_double_encoding').click()
        # #Check that only the submitted scores are available
        assert_is_element_present(self, False, 'num_double_score_215')
        assert_is_element_present(self, False, 'num_double_score_152')
        assert_is_element_present(self, False, 'num_double_score_167')
        assert_is_element_present(self, False, 'num_double_score_182')
        assert_is_element_present(self, False, 'num_double_score_200')
        assert_is_element_present(self, False, 'num_double_score_122')
        # #Double encode scores
        get_element_by_id(self, 'num_score_92').send_keys('14,8')
        Select(get_element_by_id(self, 'slt_justification_score_137')).select_by_value('ABSENT')
        # #Compare and save
        get_element_by_id(self, 'bt_compare').submit()
        get_element_by_id(self, 'bt_submit_online_double_encoding_validation').submit()
        log_out(self)

    def __test_decimal_encoding(self):
        # Encode non decimal learning unit
        login_as(self, 'coord1')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        # #Take a learning unit where decimal are not allowed
        get_element_by_id(self, 'lnk_encode_LSINF1211').click()
        # #Fill one score with decimal
        get_element_by_id(self, 'num_score_2').send_keys('13,8')
        # #Try to save and assert is not possible (button save remain present)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, True, 'bt_save_online_encoding')
        # #Change the decimal score to non decimal score
        get_element_by_id(self, 'num_score_2').clear()
        # #Fill one score with non decimal
        get_element_by_id(self, 'num_score_2').send_keys('14')
        # #Save and assert is ok (button save not present)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')
        log_out(self)

        # DoubleEncode non decimal learning unit
        login_as(self, 'prof1')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        # #Take a learning unit where decimal are not allowed
        get_element_by_id(self, 'lnk_LDUAL4355').click()
        get_element_by_id(self, 'lnk_online_double_encoding').click()
        get_element_by_id(self, 'lnk_encode_LDUAL4355').click()
        # #Fill one score with decimal
        get_element_by_id(self, 'num_double_score_2').send_keys('12,6')
        # #Try to compare and assert is not possible
        get_element_by_id(self, 'bt_compare').submit()
        assert_is_element_present(self, True, 'bt_compare')
        # #Fil in a non decimal score
        get_element_by_id(self, 'num_double_score_2').send_keys('13')
        # #Try to compare and assert it is ok
        get_element_by_id(self, 'bt_compare').submit()
        # #validate second note
        get_element_by_id(self, 'bt_take_reencoded_2').submit()
        # #Save and assert it's done
        get_element_by_id(self, 'bt_submit_online_double_encoding_validation').submit()
        assert_is_element_present(self, False, 'bt_submit_online_double_encoding_validation')
        log_out(self)

        # Encode for decimal learning unit
        login_as(self, 'coord5')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        # #Take a learning unit where decimal are allowed
        get_element_by_id(self, 'lnk_encode_LMEM2110').click()
        # #Fill one score with decimal
        get_element_by_id(self, 'num_score_146').send_keys('13,8')
        # #Save and assert is ok (button save not present)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')
        log_out(self)

        # DoubleEncode decimal learning unit
        login_as(self, 'prof5')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        # #Take a learning unit where decimal are not allowed
        get_element_by_id(self, 'lnk_LMEM2110').click()
        get_element_by_id(self, 'lnk_online_double_encoding').click()
        get_element_by_id(self, 'lnk_encode_LMEM2110').click()
        # #Fill one score decimal
        get_element_by_id(self, 'num_double_score_2').send_keys('12,6')
        # #Try to compare and assert it is ok
        get_element_by_id(self, 'bt_compare').submit()
        assert_is_element_present(self, False, 'bt_compare')
        # #validate second note
        get_element_by_id(self, 'bt_take_reencoded_146').submit()
        # #Save and assert it's done
        get_element_by_id(self, 'bt_submit_online_double_encoding_validation').submit()
        assert_is_element_present(self, False, 'bt_submit_online_double_encoding_validation')
        log_out(self)

    def __sent_message_after_submission(self):
        """
        Each time scores are submitted, a message is sent to all the professors of the learning unit
        """
        # Encode and submit partial scores as coordinator
        login_as(self, 'coord4')
        # #Go to encoding page
        get_element_by_id(self, 'lnk_home_dropdown_parcours').click()
        get_element_by_id(self, 'lnk_dropdown_evaluations').click()
        get_element_by_id(self, 'lnk_score_encoding').click()
        get_element_by_id(self, 'lnk_encode_LPSPG1021').click()
        # #Encode
        get_element_by_id(self, 'num_score_140').send_keys('15')
        Select(get_element_by_id(self, 'slt_justification_score_155')).select_by_value('ABSENT')
        # #Save and assert it's done (button save is not present anymore)
        get_element_by_id(self, 'bt_save_online_encoding').submit()
        assert_is_element_present(self, False, 'bt_save_online_encoding')
        # As a coordinator ,i can submit partial encoding
        assert_is_enabled(self, True, 'bt_score_submission_modal')
        get_element_by_id(self, 'bt_score_submission_modal').submit()
        get_element_by_id(self, 'lnk_post_scores_submission_btn').click()
        log_out(self)

        # Login as admin and check message history
        login_as(self, 'osis')
        # #Go to mesage_history page
        get_element_by_id(self, 'bt_administration').click()
        get_element_by_id(self, 'lnk_messages').click()
        get_element_by_id(self, 'lnk_messages_history').click()
        get_element_by_id(self, 'txt_subject').send_keys('LELTR7911')
        get_element_by_id(self, 'lnk_messages_history').click()
        assert_is_element_present(self, True, '')
        assert_is_element_present(self, True, '')
        log_out(self)

