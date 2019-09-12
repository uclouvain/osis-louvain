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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
from gettext import ngettext

from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base.models import learning_unit
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit import LearningUnitAdmin, LearningUnit, pedagogy_information_postponement, \
    teaching_material_postponement
from base.models.teaching_material import TeachingMaterial
from base.templatetags.learning_unit import academic_years, academic_year
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.user import SuperUserFactory
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import PedagogyTextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory


def create_learning_unit(acronym, title):
    return LearningUnitFactory(acronym=acronym, title=title, start_year=2010)


class LearningUnitTest(TestCase):

    def test_create_learning_unit_with_start_year_higher_than_end_year(self):
        l_unit = LearningUnitFactory.build(start_year=2000, end_year=1999)
        with self.assertRaises(AttributeError):
            l_unit.save()

    def test_get_partims_related(self):
        current_year = datetime.date.today().year
        academic_year = AcademicYearFactory(year=current_year)
        l_container_year = LearningContainerYearFactory(academic_year=academic_year)
        l_container_year_2 = LearningContainerYearFactory(academic_year=academic_year)
        # Create learning unit year attached to learning container year
        learning_unit_year_1 = LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        learning_unit_year_2 = LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year_2,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year, learning_container_year=None)

        all_partims_container_year_1 = l_container_year.get_partims_related()
        self.assertEqual(len(all_partims_container_year_1), 2)
        all_partims_container_year_2 = l_container_year_2.get_partims_related()
        self.assertEqual(len(all_partims_container_year_2), 0)

    def test_academic_years_tags(self):
        self.assertEqual(academic_years(2017, 2018), _('From').title() + " 2017-18 " + _('to').lower() + " 2018-19")
        self.assertEqual(academic_years(None, 2018), "-")
        self.assertEqual(academic_years(2017, None),
                         _('From').title() + " 2017-18 (" + _('no planned end').lower() + ")")
        self.assertEqual(academic_years(None, None), "-")

    def test_academic_year_tags(self):
        self.assertEqual(academic_year(2017), "2017-18")
        self.assertEqual(academic_year(None), "-")

    def test_learning_unit_start_end_year_constraint(self):
        # Case same year for start/end
        LearningUnitFactory(start_year=2017, end_year=2017)

        # Case end_year < start year
        with self.assertRaises(AttributeError):
            LearningUnitFactory(start_year=2017, end_year=2016)

        # Case end year > start year
        LearningUnitFactory(start_year=2017, end_year=2018)

    def test_delete_before_2015(self):
        lu = LearningUnitFactory(start_year=2014, end_year=2018)

        with self.assertRaises(DatabaseError):
            lu.delete()

        lu.start_year = 2015
        lu.delete()

    def test_properties_acronym_and_title(self):
        a_learning_unit = LearningUnitFactory()
        a_learning_unit_year = LearningUnitYearFactory(learning_unit=a_learning_unit)
        self.assertEqual(a_learning_unit.title, a_learning_unit_year.specific_title)
        self.assertEqual(a_learning_unit.acronym, a_learning_unit_year.acronym)


class LearningUnitGetByAcronymWithLatestAcademicYearTest(TestCase):
    def setUp(self):
        self.learning_unit_year_2009 = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=2009),
            acronym='LDROI1200'
        )
        self.learning_unit_year_2017 = LearningUnitYearFactory(
            academic_year=AcademicYearFactory(year=2017),
            acronym='LDROI1200'
        )

    def test_get_by_acronym_with_highest_academic_year(self):
        self.assertEqual(
            learning_unit.get_by_acronym_with_highest_academic_year(acronym='LDROI1200'),
            self.learning_unit_year_2017.learning_unit
        )


class TestLearningUnitAdmin(TestCase):
    def test_apply_learning_unit_year_postponement(self):
        """ Postpone to N+6 in Learning Unit Admin """
        current_year = get_current_year()
        academic_years = GenerateAcademicYear(current_year, current_year + 6)

        lu = LearningUnitFactory(end_year=None)
        LearningUnitYearFactory(
            academic_year=academic_years[0],
            learning_unit=lu
        )

        postpone_url = reverse('admin:base_learningunit_changelist')

        self.client.force_login(SuperUserFactory())
        response = self.client.post(postpone_url, data={'action': 'apply_learning_unit_year_postponement',
                                                        '_selected_action': [lu.pk]})

        msg = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(msg[0], ngettext(
            "%(count)d learning unit has been postponed with success",
            "%(count)d learning units have been postponed with success", 6
        ) % {'count': 6})


class TestApplyPedagogyInformationsPostponement(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        learning_unit = LearningUnitFactory()
        cls.luys = [LearningUnitYearFactory(academic_year=academic_year, learning_unit=learning_unit)
                for academic_year in academic_years]

        cls.queryset = LearningUnit.objects.filter(pk=learning_unit.pk)


    def test_do_not_postpone_text_which_is_not_pedagogical(self):
        translated_text = TranslatedTextRandomFactory(
            text_label__label="not_pedagogical",
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[0].id
        )

        pedagogy_information_postponement(self.queryset)

        self.assertQuerysetEqual(
            TranslatedText.objects.all(),
            [translated_text.id],
            transform=lambda obj: obj.id
        )

    def test_do_not_overwrite_text_of_next_academic_year_with_the_current_one(self):
        translated_text_of_current_academic_year = TranslatedTextRandomFactory(
            text_label=PedagogyTextLabelFactory(),
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[0].id
        )
        translated_text_of_next_academic_year = TranslatedTextRandomFactory(
            text_label=translated_text_of_current_academic_year.text_label,
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[1].id
        )

        pedagogy_information_postponement(self.queryset)

        translated_text_of_next_academic_year.refresh_from_db()
        self.assertNotEqual(
            translated_text_of_next_academic_year.text,
            translated_text_of_current_academic_year.text
        )

    def test_should_create_text_for_the_next_academic_year_based_on_the_current_one_if_not_existent(self):
        translated_text_of_current_academic_year = TranslatedTextRandomFactory(
            text_label=PedagogyTextLabelFactory(),
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[0].id
        )

        pedagogy_information_postponement(self.queryset)

        translated_text_of_next_academic_year = TranslatedText.objects.get(
            reference=self.luys[1].id,
            entity=entity_name.LEARNING_UNIT_YEAR,
            text_label=translated_text_of_current_academic_year.text_label
        )
        self.assertEqual(
            translated_text_of_current_academic_year.text,
            translated_text_of_next_academic_year.text
        )

    def test_should_postpone_text_for_each_learning_unit_year_from_next_academic_year(self):
        translated_text_of_current_academic_year = TranslatedTextRandomFactory(
            text_label=PedagogyTextLabelFactory(),
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[0].id
        )
        translated_text_of_next_academic_year = TranslatedTextRandomFactory(
            text_label=translated_text_of_current_academic_year.text_label,
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.luys[1].id
        )

        pedagogy_information_postponement(self.queryset)

        translated_texts = TranslatedText.objects.filter(
            text_label=translated_text_of_next_academic_year.text_label,
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference__in=[luy.id for luy in self.luys[2:]]
        )
        self.assertEqual(
            [tt.text for tt in translated_texts],
            [translated_text_of_next_academic_year.text] * 4,
        )


class TestApplyTeachingMaterialPostponement(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = AcademicYearFactory.produce_in_future(quantity=6)
        learning_unit = LearningUnitFactory()
        cls.luys = [LearningUnitYearFactory(academic_year=academic_year, learning_unit=learning_unit)
                for academic_year in academic_years]

        cls.queryset = LearningUnit.objects.filter(pk=learning_unit.pk)

    def test_do_not_overwrite_teaching_material_of_next_academic_year_with_the_current_one(self):
        tm_current_year = TeachingMaterialFactory(learning_unit_year=self.luys[0])
        tm_next_year = TeachingMaterialFactory(learning_unit_year=self.luys[1])

        teaching_material_postponement(self.queryset)

        tm_next_year.refresh_from_db()
        self.assertNotEqual(
            tm_current_year.title,
            tm_next_year.title
        )

    def test_should_create_teaching_material_for_the_next_academic_year_based_on_the_current_one_if_not_existent(self):
        tm_current_year = TeachingMaterialFactory(learning_unit_year=self.luys[0])

        teaching_material_postponement(self.queryset)

        tm_next_year = TeachingMaterial.objects.get(learning_unit_year=self.luys[1])

        self.assertEqual(
            tm_current_year.title,
            tm_next_year.title
        )

    def test_should_postpone_teaching_material_for_each_learning_unit_year_from_next_academic_year(self):
        tm_current_year = TeachingMaterialFactory(learning_unit_year=self.luys[0])
        tm_next_year = TeachingMaterialFactory(learning_unit_year=self.luys[1])

        teaching_material_postponement(self.queryset)

        teaching_materials = TeachingMaterial.objects.filter(learning_unit_year__in=self.luys[2:])
        self.assertEqual(
            [tm.title for tm in teaching_materials],
            [tm_next_year.title] * 4
        )

