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
from django.forms import model_to_dict
from django.test import TestCase
from django.utils.translation import ugettext as _

from base.business.education_groups.postponement import EDUCATION_GROUP_MAX_POSTPONE_YEARS, _compute_end_year
from base.business.group_element_years.postponement import PostponeContent, NotPostponeError, \
    ReuseOldLearningUnitYearWarning, PrerequisiteItemWarning
from base.business.utils.model import model_to_dict_fk
from base.models.education_group_year import EducationGroupYear
from base.models.enums import entity_type
from base.models.enums import organization_type
from base.models.enums.education_group_categories import GROUP, MINI_TRAINING
from base.models.enums.education_group_types import MiniTrainingType
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_language import EducationGroupLanguageFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory
from base.tests.factories.education_group_year_domain import EducationGroupYearDomainFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory


class EducationGroupPostponementTestCase(TestCase):
    """This mixin is used in this test file in order to setup an environment for testing EGY POSTPONEMENT"""

    def setUp(self):
        # Create several academic year
        self.current_academic_year = create_current_academic_year()
        self.generated_ac_years = GenerateAcademicYear(self.current_academic_year.year + 1,
                                                       self.current_academic_year.year + 10)
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

    def assertPostponementEquals(self, education_group_year, education_group_year_postponed):
        # Check all attribute without m2m / unreleveant fields
        fields_to_exclude = ['id', 'external_id', 'academic_year', 'languages', 'secondary_domains']
        egy_dict = model_to_dict(
            education_group_year,
            exclude=fields_to_exclude
        )
        egy_postponed_dict = model_to_dict(
            education_group_year_postponed,
            exclude=fields_to_exclude
        )
        self.assertDictEqual(egy_dict, egy_postponed_dict)

        # Check if m2m is the same
        self.assertEqual(
            self.education_group_year.secondary_domains.all().count(),
            education_group_year_postponed.secondary_domains.all().count()
        )
        self.assertEqual(
            self.education_group_year.languages.all().count(),
            education_group_year_postponed.languages.all().count()
        )


class TestComputeEndPostponement(EducationGroupPostponementTestCase):
    def test_education_group_max_postpone_years(self):
        expected_max_postpone = 6
        self.assertEqual(EDUCATION_GROUP_MAX_POSTPONE_YEARS, expected_max_postpone)

    def test_compute_end_postponement_case_no_specific_end_date_and_no_data_in_future(self):
        # Set end date of education group to None
        self.education_group_year.education_group.end_year = None
        self.education_group_year.refresh_from_db()
        # Remove all data in future
        EducationGroupYear.objects.filter(academic_year__year__gt=self.current_academic_year.year).delete()

        expected_end_year = self.current_academic_year.year + EDUCATION_GROUP_MAX_POSTPONE_YEARS
        result = _compute_end_year(self.education_group_year.education_group)
        self.assertEqual(result, expected_end_year)

    def test_compute_end_postponement_case_specific_end_date_and_no_data_in_future(self):
        # Set end date of education group
        self.education_group_year.education_group.end_year = self.current_academic_year.year + 2
        self.education_group_year.refresh_from_db()
        # Remove all data in future
        EducationGroupYear.objects.filter(academic_year__year__gt=self.current_academic_year.year).delete()

        result = _compute_end_year(self.education_group_year.education_group)
        self.assertEqual(result, self.education_group_year.education_group.end_year)

    def test_compute_end_postponement_case_specific_end_date_and_data_in_future_gte(self):
        # Set end date of education group
        self.education_group_year.education_group.end_year = self.current_academic_year.year + 2
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


class TestPostpone(TestCase):
    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.next_academic_year = AcademicYearFactory(year=self.current_academic_year.year + 1)

        self.education_group = EducationGroupFactory(end_year=self.next_academic_year.year)

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
            academic_year=self.next_academic_year
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
        gr = GroupElementYearFactory(parent=self.next_education_group_year)

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception), _("The content has already been postponed."))

        AuthorizedRelationshipFactory(
            parent_type=self.next_education_group_year.education_group_type,
            child_type=gr.child_branch.education_group_type,
            min_count_authorized=1
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        GroupElementYearFactory(parent=gr.child_branch)

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
        self.education_group.end_year = 1200

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(
            str(cm.exception),
            _("The end date of the education group is smaller than the year of postponement.")
        )

    def test_init_wrong_instance(self):
        self.current_education_group_year.education_group_type.category = GROUP
        self.current_education_group_year.education_group_type.save()

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception),
                         _('You are not allowed to copy the content of this kind of education group.'))

    def test_init_wrong_instance_minitraining(self):
        self.current_education_group_year.education_group_type.category = MINI_TRAINING
        self.current_education_group_year.education_group_type.name = MiniTrainingType.OPTION.name
        self.current_education_group_year.education_group_type.save()

        with self.assertRaises(NotPostponeError) as cm:
            self.postponer = PostponeContent(self.current_education_group_year)
        self.assertEqual(str(cm.exception),
                         _("You are not allowed to copy the content of this kind of education group."))

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
            child_branch__academic_year=self.current_academic_year
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
        self.current_group_element_year.child_branch.save()

        n1_mandatory_egy = EducationGroupYearFactory(
            academic_year=self.next_academic_year,
            acronym='mandatory_child_n1',
            education_group=self.current_group_element_year.child_branch.education_group,
            education_group_type=self.current_education_group_year.education_group_type,
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
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year,
        )

        n1_item_luy = LearningUnitYearFactory(academic_year=self.next_academic_year)

        PrerequisiteItemFactory(
            prerequisite=prerequisite,
            learning_unit=n1_item_luy.learning_unit,
        )

        group_leaf = GroupElementYearFactory(
            parent=self.current_education_group_year, child_branch=None, child_leaf=prerequisite.learning_unit_year
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()
        new_child_leaf = new_root.groupelementyear_set.last().child_leaf
        self.assertEqual(new_child_leaf.acronym, group_leaf.child_leaf.acronym)
        # If the luy does not exist in N+1, it should attach N instance
        self.assertEqual(new_child_leaf.academic_year, self.current_academic_year)
        new_prerequisite = new_child_leaf.prerequisite_set.first()

        self.assertEqual(new_prerequisite.education_group_year.education_group,
                         prerequisite.education_group_year.education_group)

        self.assertTrue(self.postponer.warnings)

        self.assertIsInstance(self.postponer.warnings[0], ReuseOldLearningUnitYearWarning)
        self.assertEqual(
            str(self.postponer.warnings[0]),
            _("The learning unit %(learning_unit_year)s does not exist in %(academic_year)s.") % {
                "learning_unit_year": prerequisite.learning_unit_year.acronym,
                "academic_year": self.next_academic_year,
            }
        )
        self.assertFalse(new_root.prerequisite_set.all())

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

    def test_postpone_with_outdated_prerequisite(self):
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year
        )

        item_luy = LearningUnitYearFactory(academic_year=self.current_academic_year)
        item = PrerequisiteItemFactory(
            prerequisite=prerequisite,
            learning_unit=item_luy.learning_unit
        )
        n1_luy = LearningUnitYearFactory(
            learning_unit=prerequisite.learning_unit_year.learning_unit,
            academic_year=self.next_academic_year,
        )

        GroupElementYearFactory(
            parent=self.current_education_group_year, child_branch=None, child_leaf=prerequisite.learning_unit_year
        )

        self.postponer = PostponeContent(self.current_education_group_year)

        new_root = self.postponer.postpone()

        new_child_leaf = new_root.groupelementyear_set.last().child_leaf
        self.assertEqual(new_child_leaf.acronym, n1_luy.acronym)
        # If the luy does not exist in N+1, it should attach N instance
        self.assertEqual(new_child_leaf.academic_year, self.next_academic_year)

        self.assertTrue(self.postponer.warnings)
        self.assertIsInstance(self.postponer.warnings[0], PrerequisiteItemWarning)
        self.assertEqual(
            str(self.postponer.warnings[0]),
            _("The postponed learning unit %(learning_unit)s has a "
              "prerequisite %(item)s which does not exist in %(academic_year)s.") % {
                "learning_unit": prerequisite.learning_unit_year.acronym,
                "item": item.learning_unit.acronym,
                "academic_year": self.next_academic_year,
            }
        )

    def test_postpone_with_prerequisite(self):
        prerequisite = PrerequisiteFactory(
            learning_unit_year__academic_year=self.current_academic_year,
            education_group_year=self.current_education_group_year
        )

        item_luy = LearningUnitYearFactory(academic_year=self.current_academic_year)
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
            child_branch__education_group__end_year=self.current_academic_year.year,
        )
        self.postponer = PostponeContent(self.current_education_group_year)

        self.postponer.postpone()

        self.assertTrue(self.postponer.warnings)
        self.assertEqual(
            str(self.postponer.warnings[0]),
            _("%(education_group_year)s is closed in %(end_year)s, there is no more link to this "
              "element in %(academic_year)s.") % {
                "education_group_year": sub_group.child_branch.acronym,
                "end_year": sub_group.child_branch.education_group.end_year,
                "academic_year": self.next_academic_year,
            }
        )
