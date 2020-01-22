##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ValidationError
from django.test import TestCase

from base.models import proposal_learning_unit
from base.models.enums import proposal_state, proposal_type
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


class TestSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.proposal_learning_unit = ProposalLearningUnitFactory()

    def test_find_by_learning_unit_year(self):
        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(
            self.proposal_learning_unit.learning_unit_year
        )
        self.assertEqual(a_proposal_learning_unit, self.proposal_learning_unit)

    def test_find_by_learning_unit(self):
        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit(
            self.proposal_learning_unit.learning_unit_year.learning_unit
        )
        self.assertEqual(a_proposal_learning_unit, self.proposal_learning_unit)

    def test_str(self):
        expected_str = "{} - {}".format(self.proposal_learning_unit.folder_id,
                                        self.proposal_learning_unit.learning_unit_year)
        self.assertEqual(str(self.proposal_learning_unit), expected_str)


class TestSearchCases(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.entity_1 = EntityFactory()
        EntityVersionFactory(entity=cls.entity_1)
        cls.an_academic_year = AcademicYearFactory(current=True)

        cls.learning_container_yr = LearningContainerYearFactory(
            academic_year=cls.an_academic_year,
            requirement_entity=cls.entity_1,
        )
        a_learning_unit_year = LearningUnitYearFactory(acronym="LBIO1212",
                                                       academic_year=cls.an_academic_year,
                                                       learning_container_year=cls.learning_container_yr)
        cls.a_proposal_learning_unit = ProposalLearningUnitFactory(learning_unit_year=a_learning_unit_year,
                                                                   type=proposal_type.ProposalType.CREATION,
                                                                   state=proposal_state.ProposalState.CENTRAL,
                                                                   entity=cls.entity_1)

    def test_search_by_proposal_type(self):
        qs = LearningUnitYear.objects.all()
        results = proposal_learning_unit.filter_proposal_fields(qs, proposal_type=self.a_proposal_learning_unit.type)
        self.check_search_result(results)

    def test_search_by_proposal_state(self):
        qs = LearningUnitYear.objects.all()
        results = proposal_learning_unit.filter_proposal_fields(qs, proposal_state=self.a_proposal_learning_unit.state)
        self.check_search_result(results)

    def test_search_by_folder_id(self):
        qs = LearningUnitYear.objects.all()
        results = proposal_learning_unit.filter_proposal_fields(qs, folder_id=self.a_proposal_learning_unit.folder_id)
        self.check_search_result(results)

    def test_search_by_entity_folder(self):
        qs = LearningUnitYear.objects.all()
        results = proposal_learning_unit.filter_proposal_fields(
            qs,
            entity_folder_id=self.a_proposal_learning_unit.entity.id
        )
        self.check_search_result(results)

    def check_search_result(self, results):
        self.assertCountEqual(results, [self.a_proposal_learning_unit.learning_unit_year])


class TestEnsureFolderIdValidator(TestCase):
    def test_ensure_folder_id_is_not_to_big(self):
        bad_proposal = ProposalLearningUnitFactory(folder_id=100000000, initial_data={'acronym': 'LDROI1200'})
        with self.assertRaises(ValidationError) as cm:
            bad_proposal.full_clean()
        self.assertTrue('folder_id' in cm.exception.message_dict.keys())
