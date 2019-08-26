# ########################################################################################
#  OSIS stands for Open Student Information System. It's an application                  #
#  designed to manage the core business of higher education institutions,                #
#  such as universities, faculties, institutes and professional schools.                 #
#  The core business involves the administration of students, teachers,                  #
#  courses, programs and so on.                                                          #
#                                                                                        #
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)    #
#                                                                                        #
#  This program is free software: you can redistribute it and/or modify                  #
#  it under the terms of the GNU General Public License as published by                  #
#  the Free Software Foundation, either version 3 of the License, or                     #
#  (at your option) any later version.                                                   #
#                                                                                        #
#  This program is distributed in the hope that it will be useful,                       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of                        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                         #
#  GNU General Public License for more details.                                          #
#                                                                                        #
#  A copy of this license - GNU General Public License - is available                    #
#  at the root of the source code of this program.  If not,                             #
#  see http://www.gnu.org/licenses/.                                                     #
# ########################################################################################
from django.conf import settings
from django.db.models import OuterRef, Exists
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from base.business.education_groups import perms as education_group_perms
from base.business.group_element_years.management import EDUCATION_GROUP_YEAR, LEARNING_UNIT_YEAR
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import MiniTrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.models.enums.proposal_type import ProposalType
from base.models.group_element_year import GroupElementYear, fetch_all_group_elements_in_tree
from base.models.learning_unit_year import LearningUnitYear
from base.models.prerequisite_item import PrerequisiteItem
from base.models.proposal_learning_unit import ProposalLearningUnit


class EducationGroupHierarchy:
    """ Use to generate json from a list of education group years compatible with jstree """
    element_type = EDUCATION_GROUP_YEAR

    _cache_hierarchy = None

    def __init__(self, root: EducationGroupYear, link_attributes: GroupElementYear = None,
                 cache_hierarchy: dict = None, tab_to_show: str = None, pdf_content: bool = False):

        self.children = []
        self.included_group_element_years = []
        self.root = root
        self.group_element_year = link_attributes
        self.reference = self.group_element_year.link_type == LinkTypes.REFERENCE.name \
            if self.group_element_year else False
        self.icon = self._get_icon()
        self._cache_hierarchy = cache_hierarchy
        self.tab_to_show = tab_to_show
        self.pdf_content = pdf_content

        if not self.pdf_content or \
                (not (self.group_element_year and
                      self.group_element_year.child.type == GroupType.MINOR_LIST_CHOICE.name)):
            self.generate_children()

        self.modification_perm = ModificationPermission(self.root, self.group_element_year)
        self.attach_perm = AttachPermission(self.root, self.group_element_year)
        self.detach_perm = DetachPermission(self.root, self.group_element_year)

    @property
    def cache_hierarchy(self):
        if self._cache_hierarchy is None:
            self._cache_hierarchy = self._init_cache()
        return self._cache_hierarchy

    def _init_cache(self):
        return fetch_all_group_elements_in_tree(self.education_group_year, self.get_queryset()) or {}

    def generate_children(self):
        for group_element_year in self.cache_hierarchy.get(self.education_group_year.id) or []:
            if group_element_year.child_branch and group_element_year.child_branch != self.root:
                node = EducationGroupHierarchy(self.root, group_element_year,
                                               cache_hierarchy=self.cache_hierarchy,
                                               tab_to_show=self.tab_to_show,
                                               pdf_content=self.pdf_content)
                self.included_group_element_years.extend(node.included_group_element_years)
            elif group_element_year.child_leaf:
                node = NodeLeafJsTree(self.root, group_element_year, cache_hierarchy=self.cache_hierarchy,
                                      tab_to_show=self.tab_to_show)

            else:
                continue

            self.children.append(node)
            self.included_group_element_years.append(group_element_year)

    def get_queryset(self):
        has_prerequisite = PrerequisiteItem.objects.filter(
            prerequisite__education_group_year__id=self.root.id,
            prerequisite__learning_unit_year__id=OuterRef("child_leaf__id"),
        )

        is_prerequisite = PrerequisiteItem.objects.filter(
            learning_unit__learningunityear__id=OuterRef("child_leaf__id"),
            prerequisite__education_group_year=self.root.id,
        )

        return GroupElementYear.objects.all() \
            .annotate(has_prerequisite=Exists(has_prerequisite)) \
            .annotate(is_prerequisite=Exists(is_prerequisite)) \
            .select_related('child_branch__academic_year',
                            'child_branch__education_group_type',
                            'child_leaf__academic_year',
                            'child_leaf__learning_container_year',
                            'child_leaf__proposallearningunit',
                            'parent').order_by("order", "parent__partial_acronym")

    def to_json(self):
        return {
            'text': self.education_group_year.verbose,
            'icon': self.icon,
            'children': [child.to_json() for child in self.children],
            'a_attr': {
                'href': self.get_url(),
                'root': self.root.pk,
                'group_element_year': self.group_element_year and self.group_element_year.pk,
                'element_id': self.education_group_year.pk,
                'element_type': self.element_type,
                'title': self.education_group_year.acronym,
                'attach_url': reverse('education_group_attach', args=[self.root.pk, self.education_group_year.pk]),
                'detach_url': reverse('group_element_year_delete', args=[
                    self.root.pk, self.education_group_year.pk, self.group_element_year.pk
                ]) if self.group_element_year else '#',
                'modify_url': reverse('group_element_year_update', args=[
                    self.root.pk, self.education_group_year.pk, self.group_element_year.pk
                ]) if self.group_element_year else '#',
                'attach_disabled': not self.attach_perm.is_permitted(),
                'attach_msg': escape(self.attach_perm.errors[0]) if self.attach_perm.errors else "",
                'detach_disabled': not self.detach_perm.is_permitted(),
                'detach_msg': escape(self.detach_perm.errors[0]) if self.detach_perm.errors else "",
                'modification_disabled': not self.modification_perm.is_permitted(),
                'modification_msg': escape(self.modification_perm.errors[0]) if self.modification_perm.errors else "",
                'search_url': reverse('quick_search_education_group')+'?academic_year={}'.format(
                    self.education_group_year.academic_year.pk
                ),
            },
        }

    def to_list(self, flat=False, pruning_function=None):
        """ Generate list of group_element_year without reference link
        @:param flat: return a flat list
        @:param pruning_function: Allow to prune the tree
        """
        result = []
        _children = filter(pruning_function, self.children) if pruning_function else self.children

        for child in _children:
            child_list = child.to_list(flat=flat, pruning_function=pruning_function)

            if child.reference:
                result.extend(child_list)
            else:
                result.append(child.group_element_year)
                if child_list:
                    result.extend(child_list) if flat else result.append(child_list)
        return result

    def _get_icon(self):
        if self.reference:
            return static('img/reference.jpg')

    @property
    def education_group_year(self):
        return self.root if not self.group_element_year else self.group_element_year.child_branch

    def url_group_to_parent(self):
        return "?group_to_parent=" + str(self.group_element_year.pk if self.group_element_year else 0)

    def get_url(self):
        default_url = reverse('education_group_read', args=[self.root.pk, self.education_group_year.pk])
        add_to_url = ""
        urls = {
            'show_identification': self.__get_base_url('education_group_read'),
            'show_diploma': self.__get_base_url('education_group_diplomas'),
            'show_administrative': self.__get_base_url('education_group_administrative'),
            'show_content': self.__get_base_url('education_group_content'),
            'show_utilization': self.__get_base_url('education_group_utilization'),
            'show_general_information': self.__get_base_url('education_group_general_informations'),
            'show_skills_and_achievements': self.__get_base_url('education_group_skills_achievements'),
            'show_admission_conditions': self.__get_base_url('education_group_year_admission_condition_edit'),
            None: default_url
        }

        return self._construct_url(add_to_url, urls)

    def _construct_url(self, add_to_url, urls):
        try:
            url = urls[self.tab_to_show]
        except KeyError:
            self.tab_to_show = None
            url = urls[self.tab_to_show]
        finally:
            if self.tab_to_show:
                add_to_url = "&tab_to_show=" + self.tab_to_show
            return url + self.url_group_to_parent() + add_to_url

    def __get_base_url(self, view_name):
        return reverse(view_name, args=[self.root.pk, self.education_group_year.pk])

    def get_option_list(self):
        def pruning_function(node):
            return node.group_element_year.child_branch and \
                   node.group_element_year.child_branch.education_group_type.name not in \
                   [GroupType.FINALITY_120_LIST_CHOICE.name, GroupType.FINALITY_180_LIST_CHOICE.name]

        return [
            element.child_branch for element in self.to_list(flat=True, pruning_function=pruning_function)
            if element.child_branch.education_group_type.name == MiniTrainingType.OPTION.name
        ]

    def get_learning_unit_year_list(self):
        return [element.child_leaf for element in self.to_list(flat=True) if element.child_leaf]

    def get_learning_unit_years(self):
        luy_ids = [element.child_leaf.id for element in self.to_list(flat=True) if element.child_leaf]
        return LearningUnitYear.objects.filter(id__in=luy_ids)


class NodeLeafJsTree(EducationGroupHierarchy):
    element_type = LEARNING_UNIT_YEAR

    @property
    def learning_unit_year(self):
        if self.group_element_year:
            return self.group_element_year.child_leaf

    @property
    def education_group_year(self):
        return

    def to_json(self):
        return {
            'text': self._get_acronym(),
            'icon': self.icon,
            'a_attr': {
                'href': self.get_url(),
                'root': self.root.pk,
                'group_element_year': self.group_element_year and self.group_element_year.pk,
                'element_id': self.learning_unit_year.pk,
                'element_type': self.element_type,
                'title': self._get_tooltip_text(),
                'has_prerequisite': self.group_element_year.has_prerequisite,
                'is_prerequisite': self.group_element_year.is_prerequisite,
                'detach_url': reverse('group_element_year_delete', args=[
                    self.root.pk, self.group_element_year.parent.pk, self.group_element_year.pk
                ]) if self.group_element_year else '#',
                'modify_url': reverse('group_element_year_update', args=[
                    self.root.pk, self.learning_unit_year.pk, self.group_element_year.pk
                ]) if self.group_element_year else '#',
                'attach_disabled': not self.attach_perm.is_permitted(),
                'attach_msg': escape(self.attach_perm.errors[0]) if self.attach_perm.errors else "",
                'detach_disabled': not self.detach_perm.is_permitted(),
                'detach_msg': escape(self.detach_perm.errors[0]) if self.detach_perm.errors else "",
                'modification_disabled': not self.modification_perm.is_permitted(),
                'modification_msg': escape(self.modification_perm.errors[0]) if self.modification_perm.errors else "",
                'class': self._get_class()
            },
        }

    def _get_tooltip_text(self):
        title = self.learning_unit_year.complete_title
        if self.group_element_year.has_prerequisite and self.group_element_year.is_prerequisite:
            title = "%s\n%s" % (title, _("The learning unit has prerequisites and is a prerequisite"))
        elif self.group_element_year.has_prerequisite:
            title = "%s\n%s" % (title, _("The learning unit has prerequisites"))
        elif self.group_element_year.is_prerequisite:
            title = "%s\n%s" % (title, _("The learning unit is a prerequisite"))
        return title

    def _get_icon(self):
        if self.group_element_year.has_prerequisite and self.group_element_year.is_prerequisite:
            return "fa fa-exchange-alt"
        elif self.group_element_year.has_prerequisite:
            return "fa fa-arrow-left"
        elif self.group_element_year.is_prerequisite:
            return "fa fa-arrow-right"
        return "far fa-file"

    def _get_acronym(self) -> str:
        """
            When the LU year is different than its education group, we have to display the year in the title.
        """
        if self.learning_unit_year.academic_year != self.root.academic_year:
            return "|{}| {}".format(self.learning_unit_year.academic_year.year, self.learning_unit_year.acronym)
        return self.learning_unit_year.acronym

    def _get_class(self):
        try:
            proposal = self.learning_unit_year.proposallearningunit
        except ProposalLearningUnit.DoesNotExist:
            proposal = None

        class_by_proposal_type = {
            ProposalType.CREATION.name: "proposal proposal_creation",
            ProposalType.MODIFICATION.name: "proposal proposal_modification",
            ProposalType.TRANSFORMATION.name: "proposal proposal_transformation",
            ProposalType.TRANSFORMATION_AND_MODIFICATION.name: "proposal proposal_transformation_modification",
            ProposalType.SUPPRESSION.name: "proposal proposal_suppression"
        }
        return class_by_proposal_type[proposal.type] if proposal else ""

    def get_url(self):
        default_url = reverse('learning_unit_utilization', args=[self.root.pk, self.learning_unit_year.pk])
        add_to_url = ''
        urls = {
            'show_utilization': default_url,
            'show_prerequisite': reverse('learning_unit_prerequisite', args=[self.root.pk, self.learning_unit_year.pk]),
            None: default_url
        }

        return self._construct_url(add_to_url, urls)

    def generate_children(self):
        """ The leaf does not have children """
        return


class LinkActionPermission:
    def __init__(self, root: EducationGroupYear, link: GroupElementYear):
        self.root = root
        self.link = link
        self.errors = []

    def is_permitted(self):
        return len(self.errors) == 0


class AttachPermission(LinkActionPermission):
    def is_permitted(self):
        self._check_year_is_editable()
        self._check_if_leaf()
        return super().is_permitted()

    def _check_year_is_editable(self):
        if not education_group_perms._is_year_editable(self.root, False):
            self.errors.append(
                str(_("Cannot perform action on a education group before %(limit_year)s") % {
                    "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION
                })
            )

    def _check_if_leaf(self):
        if self.link and self.link.child_leaf:
            self.errors.append(
                str(_("Cannot attach element to learning unit"))
            )


class DetachPermission(LinkActionPermission):
    def is_permitted(self):
        self._check_year_is_editable()
        self._check_if_root()
        self._check_if_prerequisites()
        return super().is_permitted()

    def _check_year_is_editable(self):
        if not education_group_perms._is_year_editable(self.root, False):
            self.errors.append(
                str(_("Cannot perform action on a education group before %(limit_year)s") % {
                    "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION
                })
            )

    def _check_if_root(self):
        if self.link is None:
            self.errors.append(
                str(_("Cannot perform detach action on root."))
            )

    def _check_if_prerequisites(self):
        if self.link and (self.link.has_prerequisite or self.link.is_prerequisite):
            self.errors.append(
                str(_("Cannot detach due to prerequisites."))
            )


class ModificationPermission(LinkActionPermission):
    def is_permitted(self):
        self._check_year_is_editable()
        self._check_if_root()
        return super().is_permitted()

    def _check_year_is_editable(self):
        if not education_group_perms._is_year_editable(self.root, False):
            self.errors.append(
                str(_("Cannot perform action on a education group before %(limit_year)s") % {
                    "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION
                })
            )

    def _check_if_root(self):
        if self.link is None:
            self.errors.append(
                str(_("Cannot perform modification action on root."))
            )
