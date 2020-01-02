##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext as _

from base.business.education_groups.postponement import EDUCATION_GROUP_MAX_POSTPONE_YEARS, _compute_end_year
from base.business.utils.model import model_to_dict_fk
from base.models.education_group_year import EducationGroupYear
from base.models.enums import entity_type
from base.models.enums import organization_type
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import MiniTrainingType, TrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_language import EducationGroupLanguageFactory
from base.tests.factories.education_group_type import GroupEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from program_management.business.group_element_years.postponement import PostponeContent, NotPostponeError, \
    ReuseOldLearningUnitYearWarning


class EducationGroupPostponementTestCase(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing EGY POSTPONEMENT"""

    @classmethod
    def setUpTestData(cls):
        # Create several academic year
        cls.current_academic_year = create_current_academic_year()
        start_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)
        end_year = AcademicYearFactory(year=cls.current_academic_year.year + 10)
        cls.generated_ac_years = GenerateAcademicYear(start_year, end_year)

    def setUp(self):
        # Create small entities
        self.entity = EntityFactory(organization__type=organization_type.MAIN)
        self.entity_version = EntityVersionFactory(
            entity=self.entity,
            entity_type=entity_type.SECTOR
        )

        self.education_group_year = EducationGroupYearFactory(
            management_entity=self.entity,
            administration_entity=self.entity,
            academic_year=self.current_academic_year
        )
        # Create a group language
        EducationGroupLanguageFactory(education_group_year=self.education_group_year)

        # Create two secondary domains
        EducationGroupYearDomainFactory(education_group_year=self.education_group_year)
        EducationGroupYearDomainFactory(education_group_year=self.education_group_year)


class TestComputeEndPostponement(EducationGroupPostponementTestCase):
    def test_education_group_max_postpone_years(self):
        expected_max_postpone = 6
        self.assertEqual(EDUCATION_GROUP_MAX_POSTPONE_YEARS, expected_max_postpone)

    def test_compute_end_postponement_case_no_specific_end_date_and_no_data_in_future(self):
        # Set end date of education group to None
        self.education_group_year.education_group.end_year = None
        self.education_group_year.education_group.save()
        self.education_group_year.refresh_from_db()
        # Remove all data in future
        EducationGroupYear.objects.filter(academic_year__year__gt=self.current_academic_year.year).delete()

        expected_end_year = self.current_academic_year.year + EDUCATION_GROUP_MAX_POSTPONE_YEARS
        result = _compute_end_year(self.education_group_year.education_group)
        self.assertEqual(result, expected_end_year)

    def test_compute_end_postponement_case_specific_end_date_and_no_data_in_future(self):
        # Set end date of education group
        self.education_group_year.education_group.end_year = self.generated_ac_years.academic_years[1]
        self.education_group_year.education_group.save()
        self.education_group_year.refresh_from_db()
        # Remove all data in future
        EducationGroupYear.objects.filter(academic_year__year__gt=self.current_academic_year.year).delete()

        result = _compute_end_year(self.education_group_year.education_group)
        self.assertEqual(result, self.education_group_year.education_group.end_year.year)

    def test_compute_end_postponement_case_specific_end_date_and_data_in_future_gte(self):
        # Set end date of education group
        self.education_group_year.education_group.end_year = self.generated_ac_years.academic_years[1]
        self.education_group_year.refresh_from_db()

        # Create data in future
        lastest_academic_year = self.generated_ac_years.academic_years[-1]
        field_to_exclude = ['id', 'external_id', 'academic_year', 'languages', 'secondary_domains', 'certificate_aims']
        defaults = model_to_dict_fk(self.education_group_year, exclude=field_to_exclude)
        EducationGroupYear.objects.update_or_create(
            education_group=self.education_group_year.education_group,
            academic_year=lastest_academic_year,
            defaults=defaults
        )

        result = _compute_end_year(self.education_group_year.education_group)
        self.assertEqual(result, lastest_academic_year.year)


class TestPostponeContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.previous_academic_year = AcademicYearFactory(year=cls.current_academic_year.year - 1)
        cls.next_academic_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)

    def setUp(self):
        self.education_group = EducationGroupFactory(end_year=self.next_academic_year)

        self.current_education_group_year = TrainingFactory(
            education_group=self.education_group,
            academic_year=self.current_academic_year
        )

        self.current_group_element_year = GroupElementYearFactory(
            parent=self.current_education_group_year,
            child_branch__academic_year=self.current_academic_year,
            child_branch__education_group__end_year=None
        )

        self.next_education_group_year = TrainingFactory(
            education_group=self.education_group,
            academic_year=self.next_academic_year,
            education_group_type=self.current_education_group_year.education_group_type
        )

    def test_init_postponement(self):
        self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(self.postponer.instance, self.current_education_group_year)

    def test_init_not_postponed_root(self):
        self.next_education_group_year.delete()

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception), _("The root does not exist in the next academic year."))

    def test_init_already_postponed_content(self):
        gr = GroupElementYearFactory(parent=self.next_education_group_year,
                                     child_branch__academic_year=self.next_education_group_year.academic_year)

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception), _("The content has already been postponed."))

        AuthorizedRelationshipFactory(
            parent_type=self.next_education_group_year.education_group_type,
            child_type=gr.child_branch.education_group_type,
            min_count_authorized=1
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        GroupElementYearFactory(parent=gr.child_branch, child_branch__academic_year=gr.child_branch.academic_year)

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception), _("The content has already been postponed."))

    def test_init_already_postponed_content_with_child_leaf(self):
        GroupElementYearFactory(parent=self.next_education_group_year,
                                child_branch=None,
                                child_leaf=LearningUnitYearFactory())

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception), _("The content has already been postponed."))

    def test_init_old_education_group(self):
        self.education_group.end_year = AcademicYearFactory(year=2000)

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(
            str(cm.exception),
            _("The end date of the education group is smaller than the year of postponement.")
        )

    def test_postpone_with_child_branch(self):
        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        self.assertEqual(new_root, self.next_education_group_year)
        self.assertEqual(new_root.groupelementyear_set.count(), 1)
        new_child_branch = new_root.groupelementyear_set.get().child_branch
        self.assertEqual(new_child_branch.acronym, self.current_group_element_year.child_branch.acronym)
        self.assertEqual(new_child_branch.academic_year, self.next_academic_year)

    def test_postpone_with_child_branch_existing_in_N1(self):
        n1_child_branch = EducationGroupYearFactory(
            education_group=self.current_group_element_year.child_branch.education_group,
            academic_year=self.next_academic_year
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        self.assertEqual(new_root, self.next_education_group_year)
        self.assertEqual(new_root.groupelementyear_set.count(), 1)
        new_child_branch = new_root.groupelementyear_set.get().child_branch
        self.assertEqual(new_child_branch, n1_child_branch)
        self.assertEqual(new_child_branch.academic_year, self.next_academic_year)

    def test_postpone_with_same_child_branch_existing_in_N1(self):
        n1_child_branch = EducationGroupYearFactory(
            academic_year=self.next_academic_year,
            education_group=self.current_group_element_year.child_branch.education_group,
        )
        n_child_branch = GroupElementYearFactory(
            parent=self.current_group_element_year.child_branch,
            child_branch__academic_year=self.current_academic_year,
            child_branch__education_group__end_year=None
        )

        GroupElementYearFactory(
            parent=self.next_education_group_year,
            child_branch=n1_child_branch
        )

        AuthorizedRelationshipFactory(
            parent_type=self.next_education_group_year.education_group_type,
            child_type=n1_child_branch.education_group_type,
            min_count_authorized=1
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        self.assertEqual(new_root, self.next_education_group_year)
        self.assertEqual(new_root.groupelementyear_set.count(), 1)
        new_child_branch = new_root.groupelementyear_set.get().child_branch
        self.assertEqual(new_child_branch.groupelementyear_set.get().child_branch.education_group,
                         n_child_branch.child_branch.education_group)

    def test_postpone_with_same_child_branch_existing_in_N1_without_relationship(self):
        """
        When the postponed child has a min_count_authorized relation to 1,
        we have to check if the link to the existing egy is correctly created.
        """
        n1_gr = GroupElementYearFactory(
            parent=self.next_education_group_year,
            child_branch__education_group=self.current_group_element_year.child_branch.education_group,
            child_branch__academic_year=self.next_academic_year,
        )
        AuthorizedRelationshipFactory(
            parent_type=self.next_education_group_year.education_group_type,
            child_type=n1_gr.child_branch.education_group_type,
            min_count_authorized=1
        )

        n_1_gr = GroupElementYearFactory(
            parent=self.current_group_element_year.child_branch,
            child_branch__academic_year=self.current_academic_year
        )

        n1_1_child = EducationGroupYearFactory(
            education_group=n_1_gr.child_branch.education_group,
            academic_year=self.next_academic_year,
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        self.assertEqual(
            new_root.groupelementyear_set.first().child_branch.groupelementyear_set.first().child_branch,
            n1_1_child
        )

    def test_postpone_attach_an_existing_mandatory_group_with_existing_children(self):
        """
        We have to postpone the mandatory children, but if they are already postponed, we have to reuse them.
        But the copy of the structure must be stopped if these mandatory children are not empty.
        """
        AuthorizedRelationshipFactory(
            parent_type=self.current_education_group_year.education_group_type,
            child_type=self.current_group_element_year.child_branch.education_group_type,
            min_count_authorized=1
        )
        self.current_group_element_year.child_branch.acronym = "mandatory_child_n"
        self.current_group_element_year.child_branch.education_group_type = GroupEducationGroupTypeFactory()
        self.current_group_element_year.child_branch.save()

        n1_mandatory_egy = EducationGroupYearFactory(
            academic_year=self.next_academic_year,
            acronym='mandatory_child_n1',
            education_group=self.current_group_element_year.child_branch.education_group,
            education_group_type=self.current_group_element_year.child_branch.education_group_type,
        )

        n1_child_gr = GroupElementYearFactory(
            parent=n1_mandatory_egy,
            child_branch__academic_year=self.next_academic_year,
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_mandatory_child = new_root.groupelementyear_set.first().child_branch
        self.assertEqual(new_mandatory_child, n1_mandatory_egy)
        self.assertEqual(new_mandatory_child.groupelementyear_set.first(), n1_child_gr)
        self.assertEqual(
            _("%(education_group_year)s has already been copied in %(academic_year)s in another program. "
              "It may have been already modified.") % {
                "education_group_year": n1_mandatory_egy.partial_acronym,
                "academic_year": n1_mandatory_egy.academic_year
            },
            str(self.postponer.warnings[0])
        )

    def test_postpone_with_child_branches(self):
        sub_group = GroupElementYearFactory(
            parent=self.current_group_element_year.child_branch,
            child_branch__academic_year=self.current_academic_year,
            child_branch__education_group__end_year=None,
        )
        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        self.assertEqual(new_root, self.next_education_group_year)
        self.assertEqual(new_root.groupelementyear_set.count(), 1)

        new_child_branch = new_root.groupelementyear_set.get().child_branch
        self.assertEqual(new_child_branch.acronym, self.current_group_element_year.child_branch.acronym)
        self.assertEqual(new_child_branch.academic_year, self.next_academic_year)

        self.assertEqual(new_child_branch.groupelementyear_set.count(), 1)
        new_child_branch_2 = new_child_branch.groupelementyear_set.get().child_branch
        self.assertEqual(new_child_branch_2.acronym, sub_group.child_branch.acronym)
        self.assertEqual(new_child_branch_2.academic_year, self.next_academic_year)

    def test_postpone_with_old_child_leaf(self):
        n_minus_1_luy = LearningUnitYearFactory(
            academic_year=self.previous_academic_year
        )
        LearningUnitYearFactory(
            learning_unit=n_minus_1_luy.learning_unit,
            academic_year=self.current_academic_year
        )

        group_leaf = GroupElementYearFactory(
            parent=self.current_education_group_year, child_branch=None, child_leaf=n_minus_1_luy
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_child_leaf = new_root.groupelementyear_set.last().child_leaf
        self.assertEqual(new_child_leaf.acronym, group_leaf.child_leaf.acronym)
        # If the luy does not exist in N+1, it should attach N instance
        self.assertEqual(new_child_leaf.academic_year, self.previous_academic_year)

        self.assertTrue(self.postponer.warnings)

        self.assertIsInstance(self.postponer.warnings[0], ReuseOldLearningUnitYearWarning)
        self.assertEqual(
            str(self.postponer.warnings[0]),
            _("Learning unit %(learning_unit_year)s does not exist in %(academic_year)s => "
              "Learning unit is postponed with academic year of %(learning_unit_academic_year)s.") % {
                "learning_unit_year": n_minus_1_luy.acronym,
                "academic_year": self.next_academic_year,
                "learning_unit_academic_year": n_minus_1_luy.academic_year
            }
        )

    def test_postpone_with_new_child_leaf(self):
        luy = LearningUnitYearFactory(academic_year=self.current_academic_year)
        new_luy = LearningUnitYearFactory(academic_year=self.next_academic_year,
                                          learning_unit=luy.learning_unit)
        GroupElementYearFactory(parent=self.current_education_group_year, child_branch=None, child_leaf=luy)

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_child_leaf = new_root.groupelementyear_set.last().child_leaf
        self.assertEqual(new_child_leaf, new_luy)
        self.assertEqual(new_child_leaf.academic_year, self.next_academic_year)

    def test_when_prerequisite_learning_unit_does_not_exist_in_n1(self):
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year
        )

        PrerequisiteItemFactory(
            prerequisite=prerequisite,
        )

        LearningUnitYearFactory(
            learning_unit=prerequisite.learning_unit_year.learning_unit,
            academic_year=self.next_academic_year,
        )

        GroupElementYearFactory(
            parent=self.current_group_element_year.child_branch,
            child_branch=None,
            child_leaf=prerequisite.learning_unit_year
        )

        GroupElementYearFactory(
            parent=EducationGroupYearFactory(
                education_group=self.current_group_element_year.child_branch.education_group,
                academic_year=self.next_academic_year
            ),
            child_branch=None,
            child_leaf=LearningUnitYearFactory(academic_year=self.next_academic_year)
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        self.assertIn(
            _("%(learning_unit_year)s is not anymore contained in "
              "%(education_group_year_root)s "
              "=> the prerequisite for %(learning_unit_year)s is not copied.") % {
                "education_group_year_root": "{} - {}".format(new_root.partial_acronym, new_root.acronym),
                "learning_unit_year": prerequisite.learning_unit_year.acronym,
            },
            [str(warning) for warning in self.postponer.warnings]
        )

    def test_when_prerequisite_item_does_not_exist_in_formation(self):
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year
        )

        item_luy = LearningUnitYearFactory(academic_year=self.current_academic_year)
        PrerequisiteItemFactory(
            prerequisite=prerequisite,
            learning_unit=item_luy.learning_unit
        )

        LearningUnitYearFactory(
            learning_unit=prerequisite.learning_unit_year.learning_unit,
            academic_year=self.next_academic_year,
        )

        GroupElementYearFactory(
            parent=self.current_education_group_year,
            child_branch=None,
            child_leaf=prerequisite.learning_unit_year
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        self.assertEqual(
            _("%(prerequisite_item)s is not anymore contained in "
              "%(education_group_year_root)s "
              "=> the prerequisite for %(learning_unit_year)s "
              "having %(prerequisite_item)s as prerequisite is not copied.") % {
                "education_group_year_root": "{} - {}".format(new_root.partial_acronym, new_root.acronym),
                "learning_unit_year": prerequisite.learning_unit_year.acronym,
                "prerequisite_item": item_luy.acronym
            },
            str(self.postponer.warnings[0]),
        )

    def test_postpone_with_prerequisite(self):
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year
        )

        item_luy = LearningUnitYearFactory(academic_year=self.current_academic_year)
        LearningUnitYearFactory(
            academic_year=self.previous_academic_year,
            learning_unit=item_luy.learning_unit
        )
        n1_item_luy = LearningUnitYearFactory(
            academic_year=self.next_academic_year,
            learning_unit=item_luy.learning_unit,
        )
        PrerequisiteItemFactory(
            prerequisite=prerequisite,
            learning_unit=item_luy.learning_unit
        )

        n1_luy = LearningUnitYearFactory(
            learning_unit=prerequisite.learning_unit_year.learning_unit,
            academic_year=self.next_academic_year,
        )

        GroupElementYearFactory(
            parent=self.current_education_group_year,
            child_branch=None,
            child_leaf=item_luy
        )
        GroupElementYearFactory(
            parent=self.current_education_group_year,
            child_branch=None,
            child_leaf=prerequisite.learning_unit_year
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        new_child_leaf = new_root.groupelementyear_set.last().child_leaf
        self.assertEqual(new_child_leaf.acronym, n1_luy.acronym)
        # If the luy does not exist in N+1, it should attach N instance
        self.assertEqual(new_child_leaf.academic_year, self.next_academic_year)

        self.assertFalse(self.postponer.warnings)
        self.assertEqual(
            new_child_leaf.prerequisite_set.first().prerequisiteitem_set.first().learning_unit,
            n1_item_luy.learning_unit
        )

    def test_postpone_with_terminated_child_branches(self):
        sub_group = GroupElementYearFactory(
            parent=self.current_group_element_year.child_branch,
            child_branch__academic_year=self.current_academic_year,
            child_branch__education_group__end_year=self.current_academic_year,
        )
        self.postponer = PostponeContent(self.current_education_group_year)

        self.postponer.postpone()

        self.assertTrue(self.postponer.warnings)
        self.assertEqual(
            _("%(education_group_year)s is closed in %(end_year)s. This element will not be copied "
              "in %(academic_year)s.") % {
                "education_group_year": "{} - {}".format(sub_group.child_branch.partial_acronym,
                                                         sub_group.child_branch.acronym),
                "end_year": sub_group.child_branch.education_group.end_year,
                "academic_year": self.next_academic_year,
            },
            str(self.postponer.warnings[0])
        )

    def test_when_education_group_year_exists_in_n1_has_no_child_and_is_reference_link(self):
        self.current_group_element_year.link_type = LinkTypes.REFERENCE.name
        self.current_group_element_year.save()

        n1_referenced_egy = EducationGroupYearFactory(
            academic_year=self.next_academic_year,
            education_group=self.current_group_element_year.child_branch.education_group,
            education_group_type=self.current_education_group_year.education_group_type,
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_referenced_egy = new_root.groupelementyear_set.first().child_branch
        self.assertEqual(new_referenced_egy, n1_referenced_egy)
        self.assertFalse(new_referenced_egy.groupelementyear_set.all())
        self.assertEqual(
            _("%(education_group_year)s (reference link) has not been copied. Its content is empty.") % {
                "education_group_year": "{} - {}".format(new_referenced_egy.partial_acronym,
                                                         new_referenced_egy.acronym)
            },
            str(self.postponer.warnings[0]),
        )

    def test_when_education_group_year_does_not_exist_in_n1_and_is_reference_link(self):
        self.current_group_element_year.link_type = LinkTypes.REFERENCE.name
        self.current_group_element_year.save()

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_referenced_egy = new_root.groupelementyear_set.first().child_branch
        self.assertEqual(
            new_referenced_egy.acronym,
            new_referenced_egy.acronym)
        self.assertEqual(
            new_referenced_egy.academic_year,
            self.next_academic_year
        )
        self.assertEqual(
            _("%(education_group_year)s (reference link) has not been copied. Its content is empty.") % {
                "education_group_year": "{} - {}".format(new_referenced_egy.partial_acronym,
                                                         new_referenced_egy.acronym)
            },
            str(self.postponer.warnings[0]),
        )

    def test_when_options_in_finalities_are_not_consistent(self):
        root_grp = GroupElementYearFactory(
            parent=EducationGroupYearFactory(
                education_group_type__category=Categories.TRAINING.name,
                education_group_type__name=TrainingType.PGRM_MASTER_120.name,
                academic_year=self.current_academic_year,
                education_group__end_year=None
            ),
            child_branch=EducationGroupYearFactory(
                education_group_type__category=Categories.GROUP.name,
                education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
                academic_year=self.current_academic_year,
                education_group__end_year=None
            )
        )

        child_grp = GroupElementYearFactory(
            parent=root_grp.child_branch,
            child_branch=EducationGroupYearFactory(
                education_group_type__category=Categories.TRAINING.name,
                education_group_type__name=TrainingType.MASTER_MA_120.name,
                academic_year=self.current_academic_year,
                education_group__end_year=None
            )
        )

        child_child_grp = GroupElementYearFactory(
            parent=child_grp.child_branch,
            child_branch=EducationGroupYearFactory(
                education_group_type__category=Categories.MINI_TRAINING.name,
                education_group_type__name=MiniTrainingType.OPTION.name,
                academic_year=self.current_academic_year,
                education_group__end_year=None
            )
        )

        root_egy_n1 = EducationGroupYearFactory(
            education_group_type=root_grp.parent.education_group_type,
            education_group=root_grp.parent.education_group,
            academic_year=self.next_academic_year
        )
        EducationGroupYearFactory(
            acronym=child_grp.child_branch.acronym,
            partial_acronym=child_grp.child_branch.partial_acronym,
            education_group_type=child_grp.child_branch.education_group_type,
            education_group=child_grp.child_branch.education_group,
            academic_year=self.next_academic_year,
        )
        EducationGroupYearFactory(
            acronym=child_child_grp.child_branch.acronym,
            partial_acronym=child_child_grp.child_branch.partial_acronym,
            education_group_type=child_child_grp.child_branch.education_group_type,
            education_group=child_child_grp.child_branch.education_group,
            academic_year=self.next_academic_year,
        )

        self.postponer = PostponeContent(root_grp.parent)
        self.postponer.postpone()

        self.assertEqual(
            _("The option %(education_group_year_option)s is not anymore accessible in "
              "%(education_group_year_root)s "
              "in %(academic_year)s => It is retired of the finality %(education_group_year_finality)s.") % {
                "education_group_year_option": "{}".format(child_child_grp.child_branch.partial_acronym),
                "education_group_year_root": "{} - {}".format(root_egy_n1.partial_acronym, root_egy_n1.acronym),
                "education_group_year_finality": "{} - {}".format(child_grp.child_branch.partial_acronym,
                                                                  child_grp.child_branch.acronym),
                "academic_year": self.next_academic_year
            },
            str(self.postponer.warnings[0])
        )
