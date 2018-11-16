##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from collections import OrderedDict

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from base.templatetags.learning_unit import get_difference_css, has_proposal, get_previous_acronym, value_label, \
    DIFFERENCE_CSS
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, create_learning_units_year
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.models.proposal_learning_unit import ProposalLearningUnit
from django.utils.safestring import mark_safe

LABEL_VALUE_BEFORE_PROPROSAL = _('Value before proposal')


class LearningUnitTagTest(TestCase):

    def test_get_difference_css(self):
        key_parameter_1 = 'parameter1'
        tooltip_parameter1 = 'tooltip1'

        differences = {key_parameter_1: tooltip_parameter1,
                       'parameter2': 'tooltip2'}

        self.assertEqual(get_difference_css(differences, key_parameter_1),
                         " data-toggle=tooltip title='{} : {}' class={} ".format(LABEL_VALUE_BEFORE_PROPROSAL,
                                                                                 tooltip_parameter1,
                                                                                 "proposal_value"))

    def test_get_no_differences_css(self):
        differences = {'parameter1': 'tooltip1'}
        self.assertIsNone(get_difference_css(differences, 'parameter_10'))

    def test_has_proposal(self):
        luy = LearningUnitYearFactory()
        self.assertFalse(has_proposal(luy))
        ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(has_proposal(luy))

    def test_previous_acronym(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2013, 2016, learning_unit)

        lu_yr_1 = dict_learning_unit_year.get(2013)
        lu_yr_1.acronym = "LBIR1212"
        lu_yr_1.save()

        lu_yr_2 = dict_learning_unit_year.get(2014)
        lu_yr_2.acronym = "LBIR1213"
        lu_yr_2.save()

        lu_yr_3 = dict_learning_unit_year.get(2015)
        lu_yr_3.acronym = "LBIR1214"
        lu_yr_3.save()

        self.assertEqual(get_previous_acronym(lu_yr_3), 'LBIR1213')
        self.assertEqual(get_previous_acronym(lu_yr_2), 'LBIR1212')
        self.assertIsNone(get_previous_acronym(lu_yr_1))

    def test_previous_acronym_with_acronym(self):
        learning_unit = LearningUnitFactory()
        dict_learning_unit_year = create_learning_units_year(2013, 2013, learning_unit)

        l_unit = dict_learning_unit_year.get(2013)
        initial_acronym = l_unit.acronym
        new_acronym = "{}9".format(l_unit.acronym)
        l_unit.acronym = new_acronym
        l_unit.save()

        ProposalLearningUnitFactory(learning_unit_year=l_unit,
                                    initial_data={'learning_unit_year': {'acronym': initial_acronym}})

        self.assertEqual(get_previous_acronym(l_unit), initial_acronym)

    def test_value_label_equal_values(self):
        data = self.get_dict_data()
        key = 'REQUIREMENT_ENTITY'
        sub_key = 'next'
        value_to_comp = 'current'

        self.assertCountEqual(value_label(data, key,sub_key=sub_key, key_comp=value_to_comp),
                              mark_safe("{}".format('DEXT')))

    def get_dict_data(self):
        return OrderedDict([('REQUIREMENT_ENTITY', {'current': 'DEXT', 'next': 'DEXT', 'prev': None}),
                            ("campus", {'current': 'campus 1', 'next': 'campus 2', 'prev': 'campus1'})
                            ])

    def test_value_label_different_values(self):
        data = self.get_dict_data()
        key = 'campus'
        sub_key = 'next'
        value_to_comp = 'current'

        self.assertCountEqual(value_label(data, key, sub_key=sub_key, key_comp=value_to_comp),
                              mark_safe("<label {}>{}</label>".format(DIFFERENCE_CSS, 'campus 2')))
