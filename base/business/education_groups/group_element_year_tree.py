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
#  at the root of the source code of this program.  If not,                              #
#  see http://www.gnu.org/licenses/.                                                     #
# ########################################################################################
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import OuterRef, Exists
from django.urls import reverse

from base.business.group_element_years.management import EDUCATION_GROUP_YEAR, LEARNING_UNIT_YEAR
from base.models.education_group_year import EducationGroupYear
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear, fetch_all_group_elements_in_tree
from base.models.prerequisite_item import PrerequisiteItem


class EducationGroupHierarchy:
    """ Use to generate json from a list of education group years compatible with jstree """
    element_type = EDUCATION_GROUP_YEAR

    _cache_hierarchy = None

    def __init__(self, root: EducationGroupYear, link_attributes: GroupElementYear = None,
                 cache_hierarchy: dict = None):

        self.children = []
        self.root = root
        self.group_element_year = link_attributes
        self.reference = self.group_element_year.link_type == LinkTypes.REFERENCE.name \
            if self.group_element_year else False
        self.icon = self._get_icon()
        self._cache_hierarchy = cache_hierarchy
        self.generate_children()

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
                node = EducationGroupHierarchy(self.root, group_element_year, cache_hierarchy=self.cache_hierarchy)

            elif group_element_year.child_leaf:
                node = NodeLeafJsTree(self.root, group_element_year, cache_hierarchy=self.cache_hierarchy)

            else:
                continue

            self.children.append(node)

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
                            'child_leaf__academic_year',
                            'child_leaf__learning_container_year',
                            'parent')

    def to_json(self):
        group_element_year_pk = self.group_element_year.pk if self.group_element_year else '#'
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
                ]) if self.group_element_year else '#'
            },
            'id': 'id_{}_{}'.format(self.education_group_year.pk, group_element_year_pk),
        }

    def to_list(self):
        """ Generate list of group_element_year without reference link """
        result = []

        for child in self.children:
            child_list = child.to_list()

            if child.reference:
                result.extend(child_list)

            else:
                result.append(child.group_element_year)
                if child_list:
                    result.append(child_list)

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
        url = reverse('education_group_read', args=[self.root.pk, self.education_group_year.pk])
        return url + self.url_group_to_parent()


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
        group_element_year_pk = self.group_element_year.pk if self.group_element_year else '#'
        return {
            'text': self._get_acronym(),
            'icon': self.icon,
            'a_attr': {
                'href': self.get_url(),
                'root': self.root.pk,
                'group_element_year': self.group_element_year and self.group_element_year.pk,
                'element_id': self.learning_unit_year.pk,
                'element_type': self.element_type,
                'title': self.learning_unit_year.complete_title,
                'has_prerequisite': self.group_element_year.has_prerequisite,
                'is_prerequisite': self.group_element_year.is_prerequisite,
                'detach_url': reverse('group_element_year_delete', args=[
                    self.root.pk, self.group_element_year.parent.pk, self.group_element_year.pk
                ]) if self.group_element_year else '#'
            },
            'id': 'id_{}_{}'.format(self.learning_unit_year.pk, group_element_year_pk),
        }

    def _get_icon(self):
        if self.group_element_year.has_prerequisite and self.group_element_year.is_prerequisite:
            return "fa fa-exchange"
        elif self.group_element_year.has_prerequisite:
            return "fa fa-arrow-right"
        elif self.group_element_year.is_prerequisite:
            return "fa fa-arrow-left"
        return "jstree-file"

    def _get_acronym(self) -> str:
        """ When the LU year is different than its education group, we have to display the year in the title. """
        if self.learning_unit_year.academic_year != self.root.academic_year:
            return "|{}| {}".format(self.learning_unit_year.academic_year.year, self.learning_unit_year.acronym)
        return self.learning_unit_year.acronym

    def get_url(self):
        url = reverse('learning_unit_utilization', args=[self.root.pk, self.learning_unit_year.pk])
        return url + self.url_group_to_parent()

    def generate_children(self):
        """ The leaf does not have children """
        return
