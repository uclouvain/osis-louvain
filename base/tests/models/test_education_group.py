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

from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import ngettext

from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import GROUP
from base.models.enums.education_group_types import TrainingType, GroupType
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory, GroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.user import SuperUserFactory


class EducationGroupTest(TestCase):
    def setUp(self):
        self.academic_year_1999 = AcademicYearFactory(year=1999)
        self.academic_year_2000 = AcademicYearFactory(year=2000)
        self.academic_year_2016 = AcademicYearFactory(year=2016)
        self.academic_year_2018 = AcademicYearFactory(year=2018)

    def test_most_recent_acronym(self):
        education_group = EducationGroupFactory()
        most_recent_year = self.academic_year_2018.year
        for year in range(self.academic_year_2016.year, most_recent_year + 1):
            EducationGroupYearFactory(education_group=education_group, academic_year=AcademicYearFactory(year=year))
        most_recent_educ_group_year = EducationGroupYear.objects.get(academic_year__year=most_recent_year,
                                                                     education_group=education_group)
        self.assertEqual(education_group.most_recent_acronym, most_recent_educ_group_year.acronym)

    def test_clean_case_start_year_greater_than_end_year_error(self):
        education_group = EducationGroupFactory.build(
            start_year=self.academic_year_2000,
            end_year=self.academic_year_1999
        )
        with self.assertRaises(ValidationError):
            education_group.clean()

    def test_clean_case_start_year_equals_to_end_year_no_error(self):
        education_group = EducationGroupFactory.build(
            start_year=self.academic_year_2000,
            end_year=self.academic_year_2000
        )
        education_group.clean()
        education_group.save()

    def test_clean_case_start_year_lower_to_end_year_no_error(self):
        education_group = EducationGroupFactory.build(
            start_year=self.academic_year_1999,
            end_year=self.academic_year_2000
        )
        education_group.clean()
        education_group.save()


class EducationGroupManagerTest(TestCase):
    def setUp(self):
        self.education_group_training = EducationGroupFactory()
        most_recent_year = 2018
        for year in range(2016, most_recent_year + 1):
            EducationGroupYearFactory(
                education_group=self.education_group_training,
                academic_year=AcademicYearFactory(year=year)
            )

    def test_education_group_trainings_manager(self):
        self.assertCountEqual(
            EducationGroup.objects.all(),
            EducationGroup.objects.having_related_training()
        )

    def test_education_group_trainings_manager_with_other_types(self):
        education_group_not_training = EducationGroupFactory()
        EducationGroupYearFactory(
            education_group=education_group_not_training,
            academic_year=AcademicYearFactory(year=2015),
            education_group_type=EducationGroupTypeFactory(category=GROUP)
        )

        self.assertCountEqual(
            list(EducationGroup.objects.having_related_training()),
            [self.education_group_training]
        )

        self.assertNotEqual(
            list(EducationGroup.objects.all()),
            list(EducationGroup.objects.having_related_training())
        )


class TestEducationGroupAdmin(TestCase):
    def test_apply_education_group_year_postponement(self):
        """ Postpone to N+6 in Education Group Admin """
        current_year = get_current_year()
        current_academic_year = AcademicYearFactory(year=current_year)
        end_year = AcademicYearFactory(year=current_year + 6)
        academic_years = GenerateAcademicYear(current_academic_year, end_year)

        eg = EducationGroupFactory(end_year=None)
        EducationGroupYearFactory(
            academic_year=academic_years[0],
            education_group=eg
        )

        postpone_url = reverse('admin:base_educationgroup_changelist')

        self.client.force_login(SuperUserFactory())
        response = self.client.post(postpone_url, data={'action': 'apply_education_group_year_postponement',
                                                        '_selected_action': [eg.pk]})

        msg = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(msg[0], ngettext(
            "%(count)d education group has been postponed with success.",
            "%(count)d education groups have been postponed with success.", 6
        ) % {'count': 6})


class TestEducationGroupConstraintEndYearOn2M(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_2018 = AcademicYearFactory(year=2018)
        cls.academic_year_2019 = AcademicYearFactory(year=cls.academic_year_2018.year + 1)
        cls.academic_year_2020 = AcademicYearFactory(year=cls.academic_year_2018.year + 2)

    def setUp(self):
        # Create 2m pgrm structure as
        #   2M
        #   |--FINALITY_LIST
        #      |--2MS
        #      |--2MD

        self.master_120 = TrainingFactory(
            academic_year=self.academic_year_2018,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            education_group__end_year=None
        )
        self.finality_group = GroupFactory(
            academic_year=self.academic_year_2018,
            education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
            education_group__end_year=None
        )
        GroupElementYearFactory(parent=self.master_120, child_branch=self.finality_group)

        self.master_120_specialized = GroupFactory(
            academic_year=self.academic_year_2018,
            education_group_type__name=TrainingType.MASTER_MS_120.name,
            education_group__end_year=None
        )
        GroupElementYearFactory(parent=self.finality_group, child_branch=self.master_120_specialized)
        self.master_120_didactic = GroupFactory(
            academic_year=self.academic_year_2018,
            education_group_type__name=TrainingType.MASTER_MD_120.name,
            education_group__end_year=self.academic_year_2019
        )
        GroupElementYearFactory(parent=self.finality_group, child_branch=self.master_120_didactic)

    def test_check_end_year_constraints_case_2m_end_year_is_greater_or_equals_than_finalities(self):
        """
        In this test, we ensure that a root 2M can have end date which are greater or equals than his finalities
        """
        self.master_120_specialized.education_group.end_year = self.academic_year_2019
        self.master_120_specialized.education_group.save()
        self.master_120_specialized.refresh_from_db()

        self.master_120.education_group._check_end_year_constraints_on_2m()

    def test_check_end_year_constraints_case_2m_end_year_is_lower_than_finalities(self):
        """
        In this test, we ensure that a root 2M CANNOT have end date which are lower than at least one
        end year of his finalities
        """
        # Set root 2M to 2019
        self.master_120.education_group.end_year = self.academic_year_2019
        self.master_120.education_group.save()
        self.master_120.refresh_from_db()

        with self.assertRaises(ValidationError):
            self.master_120.education_group._check_end_year_constraints_on_2m()

    def test_check_end_year_constraints_case_finality_end_year_greater_than_2m(self):
        for edy in [self.master_120_didactic, self.master_120_specialized, self.master_120]:
            edy.education_group.end_year = self.academic_year_2019
            edy.education_group.save()
            edy.education_group.refresh_from_db()

        self.master_120_didactic.education_group._check_end_year_constraints_on_2m()

        self.master_120_didactic.education_group.end_year = self.academic_year_2020
        self.master_120_didactic.education_group.save()
        self.master_120_didactic.education_group.refresh_from_db()
        with self.assertRaises(ValidationError):
            self.master_120_didactic.education_group._check_end_year_constraints_on_2m()
