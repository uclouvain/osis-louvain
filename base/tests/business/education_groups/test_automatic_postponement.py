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
from django.test import TestCase

from base.business.education_groups.automatic_postponement import ReddotEducationGroupAutomaticPostponement
from base.models.admission_condition import AdmissionConditionLine
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.admission_condition import AdmissionConditionLineFactory
from base.tests.factories.education_group_detailed_achievement import EducationGroupDetailedAchievementFactory
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText
from cms.tests.factories.translated_text import TranslatedTextFactory


class TestReddotEducationGroupAutomaticPostponement(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_year = AcademicYearFactory(year=get_current_year())
        cls.previous_year = AcademicYearFactory(year=get_current_year() - 1)

    def test_postpone(self):
        self.current_education_group_year = EducationGroupYearFactory(academic_year=self.current_year)

        publication_contact_entity = EntityFactory()
        self.previous_education_group_year = EducationGroupYearFactory(
            academic_year=self.previous_year,
            education_group=self.current_education_group_year.education_group,
            publication_contact_entity=publication_contact_entity,
        )

        TranslatedTextFactory(
            entity=OFFER_YEAR, reference=str(self.previous_education_group_year.pk),
            text="It is our choices, Harry, that show what we truly are, far more than our abilities."
        )
        EducationGroupPublicationContactFactory(
            education_group_year=self.previous_education_group_year
        )

        EducationGroupDetailedAchievementFactory(
            education_group_achievement__education_group_year=self.previous_education_group_year
        )
        AdmissionConditionLineFactory(
            admission_condition__education_group_year=self.previous_education_group_year,
            section="nothing else matters"
        )

        # this object will be removed during the copy.
        AdmissionConditionLineFactory(
            admission_condition__education_group_year=self.current_education_group_year,
            section="the world is dying."
        )

        postponer = ReddotEducationGroupAutomaticPostponement()
        postponer.postpone()

        self.assertEqual(len(postponer.result), 1)
        self.assertEqual(len(postponer.errors), 0)
        self.assertEqual(
            TranslatedText.objects.get(entity=OFFER_YEAR, reference=str(self.current_education_group_year.pk)).text,
            "It is our choices, Harry, that show what we truly are, far more than our abilities."
        )
        self.assertTrue(EducationGroupPublicationContact.objects.filter(
            education_group_year=self.current_education_group_year).exists())
        self.current_education_group_year.refresh_from_db()
        self.assertEqual(self.current_education_group_year.publication_contact_entity, publication_contact_entity)

        self.assertTrue(EducationGroupDetailedAchievement.objects.filter(
            education_group_achievement__education_group_year=self.current_education_group_year).exists())

        self.assertTrue(AdmissionConditionLine.objects.get(
            admission_condition__education_group_year=self.current_education_group_year).section,
                        "nothing else matters")

    def test_no_previous_education_group(self):
        postponer = ReddotEducationGroupAutomaticPostponement()
        postponer.postpone()
        self.assertEqual(len(postponer.result), 0)
        self.assertEqual(len(postponer.errors), 0)
