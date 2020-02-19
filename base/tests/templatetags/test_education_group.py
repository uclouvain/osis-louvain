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
from datetime import timedelta

import mock
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, pgettext
from waffle.testutils import override_switch

from base.models.enums import education_group_categories
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING, Categories
from base.models.enums.education_group_types import GroupType
from base.templatetags.education_group import li_with_deletion_perm, \
    button_order_with_permission, li_with_create_perm_training, \
    li_with_create_perm_mini_training, li_with_create_perm_group, link_detach_education_group, \
    link_pdf_content_education_group, button_edit_administrative_data, dl_with_parent, li_with_update_perm
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import TrainingFactory, EducationGroupYearFactory
from base.tests.factories.person import FacultyManagerFactory, CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.program_manager import ProgramManagerFactory

DELETE_MSG = _("delete education group")
PERMISSION_DENIED_MSG = _("This education group is not editable during this period.")
UNAUTHORIZED_TYPE_MSG = "No type of %(child_category)s can be created as child of %(category)s of type %(type)s"

CUSTOM_LI_TEMPLATE = """
    <li {li_attributes}>
        <a {a_attributes} data-toggle="tooltip">{text}</a>
    </li>
"""


class TestEducationGroupAsCentralManagerTag(TestCase):
    """ This class will test the tag as central manager """
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory(year=2020)
        cls.education_group_year = TrainingFactory(academic_year=academic_year)
        cls.person = CentralManagerFactory(
            "delete_educationgroup",
            "change_educationgroup",
            "add_educationgroup",
            "can_edit_education_group_administrative_data"
        )
        PersonEntityFactory(person=cls.person, entity=cls.education_group_year.management_entity)

        cls.url = reverse('delete_education_group', args=[cls.education_group_year.id, cls.education_group_year.id])

        cls.request = RequestFactory().get("")

    def setUp(self):
        self.client.force_login(user=self.person.user)
        self.context = {
            "person": self.person,
            "education_group_year": self.education_group_year,
            "request": self.request,
            "root": self.education_group_year,
        }

    def test_li_with_deletion_perm(self):
        result = li_with_deletion_perm(self.context, self.url, DELETE_MSG)
        self.assertEqual(
            result, {
                'load_modal': True,
                'title': '',
                'class_li': '',
                'id_li': 'link_delete',
                'url': self.url,
                'text': DELETE_MSG
            }
        )

    @mock.patch('base.business.education_groups.perms.check_permission')
    @mock.patch('base.business.education_groups.perms.is_eligible_to_change_education_group')
    def test_button_order_with_permission(self, mock_permission, mock_eligibility):
        mock_permission.return_value = True
        mock_eligibility.return_value = True
        result = button_order_with_permission(self.context, "title", "id", "edit")
        self.assertEqual(result, {"title": "title", "id": "id", "value": "edit", 'disabled': "",
                                  'icon': "glyphicon glyphicon-edit"})

    def test_li_with_create_perm_training(self):
        relation = AuthorizedRelationshipFactory(parent_type=self.education_group_year.education_group_type)
        relation.child_type.category = TRAINING
        relation.child_type.save()

        result = li_with_create_perm_training(self.context, self.url, "")
        self.assertEqual(
            result, {
                'load_modal': True,
                'id_li': 'link_create_training',
                'url': self.url,
                'title': '',
                'class_li': '',
                'text': ''
            }
        )

    def test_li_with_create_perm_mini_training(self):
        relation = AuthorizedRelationshipFactory(parent_type=self.education_group_year.education_group_type)
        relation.child_type.category = MINI_TRAINING
        relation.child_type.save()

        result = li_with_create_perm_mini_training(self.context, self.url, "")
        self.assertEqual(
            result, {
                'load_modal': True,
                'id_li': 'link_create_mini_training',
                'url': self.url,
                'title': '',
                'class_li': '',
                'text': ''
            }
        )

    def test_li_with_create_perm_group(self):
        relation = AuthorizedRelationshipFactory(parent_type=self.education_group_year.education_group_type)
        relation.child_type.category = Categories.GROUP.name
        relation.child_type.save()

        result = li_with_create_perm_group(self.context, self.url, "")

        self.assertEqual(
            result, {
                'load_modal': True,
                'title': '',
                'class_li': '',
                'id_li': 'link_create_group',
                'url': self.url, 'text': ''
            }
        )

    def test_li_with_create_perm_training_disabled(self):
        result = li_with_create_perm_training(self.context, self.url, "")

        msg = pgettext("female", UNAUTHORIZED_TYPE_MSG) % {
            "child_category": Categories.TRAINING.value,
            "category": self.education_group_year.education_group_type.get_category_display(),
            "type": self.education_group_year.education_group_type.get_name_display()
        }
        msg = msg.capitalize()
        self.assertEqual(
            result, {
                'load_modal': False,
                'title': msg,
                'class_li': 'disabled',
                'id_li': 'link_create_training',
                'url': "#",
                'text': ''
            }
        )

    def test_li_with_create_perm_mini_training_disabled(self):
        result = li_with_create_perm_mini_training(self.context, self.url, "")
        msg = pgettext("female", UNAUTHORIZED_TYPE_MSG) % {
            "child_category": Categories.MINI_TRAINING.value,
            "category": self.education_group_year.education_group_type.get_category_display(),
            "type": self.education_group_year.education_group_type.get_name_display()
        }
        msg = msg.capitalize()
        self.assertEqual(
            result, {
                'load_modal': False,
                'title': msg,
                'class_li': 'disabled',
                'id_li': 'link_create_mini_training',
                'url': "#",
                'text': ''
            }
        )

    def test_li_with_create_perm_group_disabled(self):
        result = li_with_create_perm_group(self.context, self.url, "")
        msg = pgettext("female", UNAUTHORIZED_TYPE_MSG) % {
            "child_category": Categories.GROUP.value,
            "category": self.education_group_year.education_group_type.get_category_display(),
            "type": self.education_group_year.education_group_type.get_name_display()
        }
        msg = msg.capitalize()
        self.assertEqual(
            result, {
                'load_modal': False,
                'title': msg,
                'class_li': 'disabled',
                'id_li': 'link_create_group',
                'url': "#",
                'text': ''
            }
        )

    def test_tag_detach_education_group_permitted_and_possible(self):
        self.context['can_change_education_group'] = True
        self.context['group_to_parent'] = '1'
        result = link_detach_education_group(self.context, "#")
        expected_result = CUSTOM_LI_TEMPLATE.format(
            li_attributes=""" class="trigger_modal" id="btn_operation_detach_1" data-url="#" """,
            a_attributes=""" href="#" title="{}" onclick="select()" """.format(_('Detach')),
            text=_('Detach'),
        )
        self.assertHTMLEqual(result, expected_result)

    def test_tag_detach_education_group_not_permitted(self):
        self.context['can_change_education_group'] = False
        self.context['group_to_parent'] = '1'
        result = link_detach_education_group(self.context, "#")
        expected_result = CUSTOM_LI_TEMPLATE.format(
            li_attributes=""" class="disabled" """,
            a_attributes=""" title="{}" """.format(_("The user has not permission to change education groups.")),
            text=_('Detach'),
        )
        self.assertHTMLEqual(result, expected_result)

    def test_tag_detach_education_group_not_possible(self):
        self.context['can_change_education_group'] = True
        self.context['group_to_parent'] = '0'
        result = link_detach_education_group(self.context, "#")
        expected_result = CUSTOM_LI_TEMPLATE.format(
            li_attributes=""" class="disabled" """,
            a_attributes=""" title=" {}" """.format(
                _("It is not possible to %(action)s the root element.") % {"action": _("Detach").lower()}),
            text=_('Detach'),
        )
        self.assertHTMLEqual(result, expected_result)

    def test_tag_detach_education_group_not_permitted_nor_possible(self):
        self.context['can_change_education_group'] = False
        self.context['group_to_parent'] = '0'
        result = link_detach_education_group(self.context, "#")
        expected_result = CUSTOM_LI_TEMPLATE.format(
            li_attributes=""" class="disabled" """,
            a_attributes=""" title="{} {}" """.format(
                _("The user has not permission to change education groups."),
                _("It is not possible to detach the root element."),
            ),
            text=_('Detach'),
        )
        self.maxDiff = None
        self.assertHTMLEqual(result, expected_result)

    @override_switch('education_group_year_generate_pdf', active=True)
    def test_tag_link_pdf_content_education_group_not_permitted(self):
        result = link_pdf_content_education_group(self.context)
        self.assertEqual(
            result,
            {
                'url': {
                    'person': self.person,
                    'education_group_year': self.education_group_year,
                    'request': self.request,
                    'root': self.education_group_year
                },
                'text': 'Générer le pdf',
                'class_li': '',
                'title': 'Générer le pdf',
                'id_li': 'btn_operation_pdf_content',
                'load_modal': True
            }
        )

    @override_switch('education_group_year_generate_pdf', active=False)
    def test_tag_link_pdf_content_education_group_not_permitted_with_sample_deactivated(self):
        result = link_pdf_content_education_group(self.context)
        self.assertEqual(
            result,
            {
                'url': '#',
                'text': 'Générer le pdf',
                'class_li': 'disabled',
                'title': 'Générer le PDF n\'est pas disponible. Veuillez utiliser EPC.',
                'id_li': 'btn_operation_pdf_content',
                'load_modal': False
            }
        )

    def test_button_edit_administrative_data_enabled(self):
        result = button_edit_administrative_data(self.context)

        self.assertEqual(
            result["url"],
            reverse('education_group_edit_administrative', args=[
                self.education_group_year.pk,
                self.education_group_year.pk
            ])
        )

        self.assertEqual(result["title"], "")

        self.assertEqual(result["class_li"], "")

        self.assertEqual(result["text"], _("Modify"))


class TestEducationGroupAsFacultyManagerTag(TestCase):
    """ This class will test the tag as faculty manager """
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory(year=2020)
        cls.education_group_year = TrainingFactory(academic_year=academic_year)
        cls.person = FacultyManagerFactory("delete_educationgroup", "change_educationgroup", "add_educationgroup")
        PersonEntityFactory(person=cls.person, entity=cls.education_group_year.management_entity)

        # Create an academic calendar in order to check permission [Faculty can modify when period is opened]
        cls.academic_calendar = AcademicCalendarFactory(
            reference=EDUCATION_GROUP_EDITION,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(weeks=+1),
            academic_year=academic_year,
            data_year=academic_year,
        )

        cls.url = reverse('delete_education_group', args=[cls.education_group_year.id, cls.education_group_year.id])

    def setUp(self):
        self.client.force_login(user=self.person.user)
        self.context = {
            "person": self.person,
            "root": self.education_group_year,
            "education_group_year": self.education_group_year,
            "request": RequestFactory().get("")
        }

    def test_li_tag_case_not_in_education_group_edition_period(self):
        """ This test ensure that as faculty manager, the li tag is disabled when outside of encoding period"""
        self.academic_calendar.delete()

        result = li_with_deletion_perm(self.context, self.url, DELETE_MSG)
        self.assertEqual(
            result, {
                'load_modal': False,
                'title': PERMISSION_DENIED_MSG,
                'class_li': 'disabled',
                'id_li': 'link_delete',
                'url': "#",
                'text': DELETE_MSG
            }
        )

    def test_li_tag_case_education_group_edition_period_within_the_past(self):
        academic_years = []
        education_group = EducationGroupFactory(start_year=AcademicYearFactory(year=2013))
        edys = []
        for i in range(2014, AcademicYearFactory(current=True).year + 1):
            aca_year = AcademicYearFactory(year=i)
            academic_years.append(aca_year)
            edys.append(TrainingFactory(academic_year=aca_year,
                                        education_group=education_group,
                                        management_entity=self.education_group_year.management_entity))

        url = reverse('delete_education_group', args=[edys[-1].id, edys[-1].id])
        context = {
            "person": self.person,
            "root": edys[-1],
            "education_group_year": edys[-1],
            "request": RequestFactory().get("")
        }
        result = li_with_deletion_perm(context, url, DELETE_MSG)
        self.assertEqual(
            {
                'load_modal': False,
                'title': PERMISSION_DENIED_MSG,
                'class_li': 'disabled',
                'id_li': 'link_delete',
                'url': "#",
                'text': DELETE_MSG
            },
            result
        )

    def test_li_tag_case_inside_education_group_edition_period(self):
        result = li_with_deletion_perm(self.context, self.url, DELETE_MSG)
        self.assertEqual(
            result, {
                'load_modal': True,
                'text': DELETE_MSG,
                'class_li': '',
                'id_li': "link_delete",
                'url': self.url,
                'title': ''
            }
        )

    def test_li_with_create_perm_mini_training(self):
        """
        This test ensure that as faculty manager, the li tag is enable for mini training
        """
        relation = AuthorizedRelationshipFactory(parent_type=self.education_group_year.education_group_type)
        relation.child_type.category = Categories.MINI_TRAINING.name
        relation.child_type.save()

        result = li_with_create_perm_mini_training(self.context, self.url, "")
        self.assertEqual(
            result, {
                'load_modal': True,
                'id_li': 'link_create_mini_training',
                'url': self.url,
                'title': '',
                'class_li': '',
                'text': ''
            }
        )

    def test_li_tag_case_training_disabled(self):
        """
        This test ensure that as faculty manager, the li tag is disabled for training
        Faculty manager must enter in proposition mode for training
        """
        self.context['education_group_year'] = TrainingFactory()
        result = li_with_create_perm_training(self.context, self.url, "")
        msg = pgettext("female", "The user has not permission to create a %(category)s.") % {
            "category": Categories.TRAINING.value
        }
        msg = msg.capitalize()
        self.assertEqual(
            result, {
                'load_modal': False,
                'title': msg,
                'class_li': 'disabled',
                'id_li': 'link_create_training',
                'url': "#",
                'text': ''
            }
        )

    def test_button_edit_administrative_data_disabled(self):
        result = button_edit_administrative_data(self.context)

        self.assertEqual(result["url"], "#")

        self.assertEqual(
            result["title"],
            _('Only program managers of the education group OR central manager linked to entity can edit.')
        )

        self.assertEqual(result["class_li"], "disabled")
        self.assertEqual(result["text"], _("Modify"))

    @mock.patch('base.business.education_groups.perms.check_permission')
    @mock.patch('base.business.education_groups.perms.is_eligible_to_change_education_group')
    def test_button_order_with_permission_for_major_minor_list_choice_disabled(self, mock_permission, mock_eligibility):
        mock_permission.return_value = True
        mock_eligibility.return_value = True
        group_type_disabled = [GroupType.MAJOR_LIST_CHOICE.name, GroupType.MINOR_LIST_CHOICE.name]
        self._get_permisson_order_button(group_type_disabled,
                                         "disabled",
                                         _('The user is not allowed to change education group content.'))

    @mock.patch('base.business.education_groups.perms.check_permission')
    @mock.patch('base.business.education_groups.perms.is_eligible_to_change_education_group')
    def test_button_order_with_permission_for_major_minor_list_choice_enabled(self, mock_permission, mock_eligibility):
        mock_permission.return_value = True
        mock_eligibility.return_value = True
        group_type_disabled = [GroupType.OPTION_LIST_CHOICE.name]
        self._get_permisson_order_button(group_type_disabled, "", "")

    def _get_permisson_order_button(self, group_type_disabled, disabled_status, message):
        for group_type in group_type_disabled:
            egt = EducationGroupTypeFactory(name=group_type, category=education_group_categories.TRAINING)
            self.context['education_group_year'] = TrainingFactory(education_group_type=egt)
            result = button_order_with_permission(self.context, message, "id", "edit")
            self.assertEqual(result, {"title": message,
                                      "id": "id", "value": "edit", 'disabled': disabled_status,
                                      'icon': "glyphicon glyphicon-edit"})



class TestEducationGroupDlWithParent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = EducationGroupYearFactory()

    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()
        self.context = {
            'parent': self.parent,
            'education_group_year': self.education_group_year,
        }

    def test_dl_value_in_education_group(self):
        response = dl_with_parent(self.context, "acronym")
        self.assertEqual(response["value"], self.education_group_year.acronym)
        self.assertEqual(response["label"], _("Acronym/Short title"))
        self.assertEqual(response["parent_value"], None)

    def test_dl_value_in_parent(self):
        self.education_group_year.acronym = ""
        response = dl_with_parent(self.context, "acronym")
        self.assertEqual(response["value"], "")
        self.assertEqual(response["label"], _("Acronym/Short title"))
        self.assertEqual(response["parent_value"], self.parent.acronym)

    def test_dl_default_value(self):
        self.education_group_year.acronym = ""
        self.parent.acronym = ""
        response = dl_with_parent(self.context, "acronym", default_value="avada kedavra")

        self.assertEqual(response["value"], "")
        self.assertEqual(response["label"], _("Acronym/Short title"))
        self.assertEqual(response["parent_value"], "")
        self.assertEqual(response["default_value"], "avada kedavra")

    def test_dl_with_bool(self):
        self.education_group_year.partial_deliberation = False
        response = dl_with_parent(self.context, "partial_deliberation")
        self.assertEqual(response["value"], "no")
        self.assertEqual(response["parent_value"], None)

        self.education_group_year.partial_deliberation = True
        response = dl_with_parent(self.context, "partial_deliberation")
        self.assertEqual(response["value"], "yes")
        self.assertEqual(response["parent_value"], None)

        self.education_group_year.partial_deliberation = None
        self.parent.partial_deliberation = True
        response = dl_with_parent(self.context, "partial_deliberation")
        self.assertEqual(response["value"], None)
        self.assertEqual(response["parent_value"], "yes")

    def test_dl_invalid_key(self):
        self.education_group_year.partial_deliberation = False
        with self.assertRaises(FieldDoesNotExist):
            dl_with_parent(self.context, "not_a_real_attr")


class TestEducationGroupUpdateTagAsProgramManager(TestCase):
    """ This class will test the tag as program manager """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.training = TrainingFactory(academic_year__year=2018)
        cls.program_manager = ProgramManagerFactory(education_group=cls.training.education_group)
        cls.context = {
            'person': cls.program_manager.person,
            'root': cls.training,
            'education_group_year': cls.training,
        }
        cls.url = reverse('update_education_group', args=[cls.training.pk, cls.training.pk])
        cls.request = RequestFactory().get("")

    def test_is_program_manager_with_permission_to_edit(self):
        result = li_with_update_perm(self.context, self.url, "")
        self.assertEqual(
            result, {
                'load_modal': True,
                'id_li': 'link_update',
                'url': self.url,
                'title': '',
                'class_li': '',
                'text': ''
            }
        )

    def test_is_program_manager_without_permission_to_edit_because_not_program_manager(self):
        result = li_with_update_perm({**self.context, 'education_group_year': TrainingFactory()}, self.url, "")
        self.assertEqual(
            result, {
                'load_modal': False,
                'id_li': 'link_update',
                'url': '#',
                'title': str(_("The user is not the program manager of the education group")),
                'class_li': 'disabled',
                'text': ''
            }
        )
