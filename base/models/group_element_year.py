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
import collections
import itertools
from collections import Counter

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, connection
from django.db.models import Q, F, Case, When
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel
from reversion.admin import VersionAdmin

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.models import education_group_year
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums import quadrimesters
from base.models.enums.education_group_types import GroupType, MiniTrainingType, TrainingType
from base.models.enums.link_type import LinkTypes
from base.models.learning_component_year import LearningComponentYear, volume_total_verbose
from base.models.learning_unit_year import LearningUnitYear
from osis_common.models.osis_model_admin import OsisModelAdmin

COMMON_FILTER_TYPES = [MiniTrainingType.OPTION.name]
DEFAULT_ROOT_TYPES = TrainingType.get_names() + MiniTrainingType.get_names()


class GroupElementYearAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('parent', 'child_branch', 'child_leaf',)
    readonly_fields = ('order',)
    search_fields = [
        'child_branch__acronym',
        'child_branch__partial_acronym',
        'child_leaf__acronym',
        'parent__acronym',
        'parent__partial_acronym'
    ]
    list_filter = ('is_mandatory', 'access_condition', 'parent__academic_year')


def validate_block_value(value):
    max_authorized_value = 6
    _error_msg = _(
        "Please register a maximum of %(max_authorized_value)s digits in ascending order, "
        "without any duplication. Authorized values are from 1 to 6. Examples: 12, 23, 46"
    ) % {'max_authorized_value': max_authorized_value}

    MinValueValidator(1, message=_error_msg)(value)
    if not all([
        _check_integers_max_authorized_value(value, max_authorized_value),
        _check_integers_duplications(value),
        _check_integers_orders(value),
    ]):
        raise ValidationError(_error_msg)


def _check_integers_max_authorized_value(value, max_authorized_value):
    return all(int(char) <= max_authorized_value for char in str(value))


def _check_integers_duplications(value):
    if any(integer for integer, occurence in Counter(str(value)).items() if occurence > 1):
        return False
    return True


def _check_integers_orders(value):
    digit_values = [int(char) for char in str(value)]
    return list(sorted(digit_values)) == digit_values


class GroupElementYearManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            Q(child_branch__isnull=False) | Q(child_leaf__learning_container_year__isnull=False)
        )

    def get_adjacency_list(self, root_elements_ids):
        if not isinstance(root_elements_ids, list):
            raise Exception('root_elements_ids must be an instance of list')
        if not root_elements_ids:
            return []

        adjacency_query = """
            WITH RECURSIVE
                adjacency_query AS (
                    SELECT
                        parent_id as starting_node_id,
                        id,
                        child_branch_id,
                        child_leaf_id,
                        parent_id,
                        "order",
                        0 AS level,
                        CAST(parent_id || '|' ||
                            (
                                CASE
                                WHEN child_branch_id is not null
                                    THEN child_branch_id
                                    ELSE child_leaf_id
                                END
                            ) as varchar(1000)
                        ) As path
                    FROM base_groupelementyear
                    WHERE parent_id IN (%s)

                    UNION ALL

                    SELECT parent.starting_node_id,
                           child.id,
                           child.child_branch_id,
                           child.child_leaf_id,
                           child.parent_id,
                           child.order,
                           parent.level + 1,
                           CAST(
                                parent.path || '|' ||
                                    (
                                        CASE
                                        WHEN child.child_branch_id is not null
                                            THEN child.child_branch_id
                                            ELSE child.child_leaf_id
                                        END
                                    ) as varchar(1000)
                               ) as path
                    FROM base_groupelementyear AS child
                    INNER JOIN adjacency_query AS parent on parent.child_branch_id = child.parent_id
                )
            SELECT * FROM adjacency_query
            ORDER BY starting_node_id, level, "order";
        """ % ','.join(["%s"] * len(root_elements_ids))

        with connection.cursor() as cursor:
            cursor.execute(adjacency_query, root_elements_ids)
            return [
                {
                    'starting_node_id': row[0],
                    'id': row[1],
                    'child_branch_id': row[2],
                    'child_leaf_id': row[3],
                    'parent_id': row[4],
                    'child_id': row[2] or row[3],
                    'order': row[5],
                    'level': row[6],
                    'path': row[7],
                } for row in cursor.fetchall()
            ]

    def get_reverse_adjacency_list(
            self,
            child_leaf_ids=None,
            child_branch_ids=None,
            academic_year_id=None,
            link_type: LinkTypes = None
    ):
        if child_leaf_ids is None:
            child_leaf_ids = []
        if child_branch_ids is None:
            child_branch_ids = []
        if child_leaf_ids and not isinstance(child_leaf_ids, list):
            raise Exception('child_leaf_ids must be an instance of list')
        if child_branch_ids and not isinstance(child_branch_ids, list):
            raise Exception('child_branch_ids must be an instance of list')
        if not child_leaf_ids and not child_branch_ids:
            return []

        # TODO :: simplify the code (by using a param child_ids_instance=LearningUnitYear by default?)
        where_statement_leaf = ""
        if child_leaf_ids:
            where_statement_leaf = "child_leaf_id in (%(child_ids)s)" % {
                'child_ids': ','.join(["%s"] * len(child_leaf_ids))
            }

        where_statement_branch = ""
        if child_branch_ids:
            where_statement_branch = "child_branch_id in (%(child_ids)s)" % {
                'child_ids': ','.join(["%s"] * len(child_branch_ids))
            }

        if child_leaf_ids and child_branch_ids:
            where_statement = where_statement_leaf + ' OR ' + where_statement_branch
        elif child_leaf_ids and not child_branch_ids:
            where_statement = where_statement_leaf
        else:
            where_statement = where_statement_branch

        reverse_adjacency_query = """
            WITH RECURSIVE
                reverse_adjacency_query AS (
                    SELECT
                        CASE
                            WHEN gey.child_leaf_id is not null then gey.child_leaf_id
                            ELSE gey.child_branch_id
                        END as starting_node_id,
                           gey.id,
                           gey.child_branch_id,
                           gey.child_leaf_id,
                           gey.parent_id,
                           gey.order,
                           edyc.academic_year_id,
                           0 AS level
                    FROM base_groupelementyear gey
                    INNER JOIN base_educationgroupyear AS edyc on gey.parent_id = edyc.id
                    WHERE %(where_statement)s
                    AND (%(link_type)s IS NULL or gey.link_type = %(link_type)s)

                    UNION ALL

                    SELECT 	child.starting_node_id,
                            parent.id,
                            parent.child_branch_id,
                            parent.child_leaf_id,
                            parent.parent_id,
                            parent.order,
                            edyp.academic_year_id,
                            child.level + 1
                    FROM base_groupelementyear AS parent
                    INNER JOIN reverse_adjacency_query AS child on parent.child_branch_id = child.parent_id
                    INNER JOIN base_educationgroupyear AS edyp on parent.parent_id = edyp.id
                )

            SELECT distinct starting_node_id, id, child_branch_id, child_leaf_id, parent_id, "order", level
            FROM reverse_adjacency_query
            WHERE %(academic_year_id)s IS NULL OR academic_year_id = %(academic_year_id)s
            ORDER BY starting_node_id,  level DESC, "order";
        """ % {
            'where_statement': where_statement,
            'academic_year_id': "%s",
            'link_type': '%s',
        }
        with connection.cursor() as cursor:
            parameters = child_leaf_ids + child_branch_ids + [
                link_type.name if link_type else None,
                link_type.name if link_type else None,
                academic_year_id,
                academic_year_id
            ]
            cursor.execute(reverse_adjacency_query, parameters)
            return [
                {
                    'starting_node_id': row[0],
                    'id': row[1],
                    'child_branch_id': row[2],
                    'child_leaf_id': row[3],
                    'parent_id': row[4],
                    'child_id': row[2] or row[3],
                    'order': row[5],
                    'level': row[6],
                } for row in cursor.fetchall()
            ]


class GroupElementYear(OrderedModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    parent = models.ForeignKey(
        EducationGroupYear,
        null=True,  # TODO: can not be null, dirty data
        on_delete=models.PROTECT,
    )

    child_branch = models.ForeignKey(
        EducationGroupYear,
        related_name='child_branch',  # TODO: can not be child_branch
        blank=True, null=True,
        on_delete=models.CASCADE,
    )

    child_leaf = models.ForeignKey(
        LearningUnitYear,
        related_name='child_leaf',  # TODO: can not be child_leaf
        blank=True, null=True,
        on_delete=models.CASCADE,
    )

    relative_credits = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("relative credits"),
    )

    min_credits = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Min. credits"),
    )

    max_credits = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Max. credits"),
    )

    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_("Mandatory"),
    )

    block = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Block"),
        validators=[validate_block_value]
    )

    access_condition = models.BooleanField(
        default=False,
        verbose_name=_('Access condition')
    )

    comment = models.TextField(
        max_length=500,
        blank=True, null=True,
        verbose_name=_("comment"),
    )
    comment_english = models.TextField(
        max_length=500,
        blank=True, null=True,
        verbose_name=_("english comment"),
    )

    own_comment = models.CharField(max_length=500, blank=True, null=True)

    quadrimester_derogation = models.CharField(
        max_length=10,
        choices=quadrimesters.DerogationQuadrimester.choices(),
        blank=True, null=True, verbose_name=_('Quadrimester derogation')
    )

    link_type = models.CharField(
        max_length=25,
        choices=LinkTypes.choices(),
        blank=True, null=True, verbose_name=_('Link type')
    )

    order_with_respect_to = 'parent'

    objects = GroupElementYearManager()

    def __str__(self):
        return "{} - {}".format(self.parent, self.child)

    @property
    def verbose(self):
        if self.child_branch:
            return self._verbose_credits()
        else:
            components = LearningComponentYear.objects.filter(
                learning_unit_year=self.child_leaf).annotate(
                total=Case(When(hourly_volume_total_annual=None, then=0),
                           default=F('hourly_volume_total_annual'))).values('type', 'total')

            return "{} {} [{}] ({} {})".format(
                self.child_leaf.acronym,
                self.child.complete_title_english
                if self.child.complete_title_english and translation.get_language() == 'en'
                else self.child.complete_title,
                volume_total_verbose(components),
                self.relative_credits or self.child_leaf.credits or 0,
                _("credits"),
            )

    @property
    def verbose_comment(self):
        if self.comment_english and translation.get_language() == LANGUAGE_CODE_EN:
            return self.comment_english
        return self.comment

    class Meta:
        unique_together = (('parent', 'child_branch'), ('parent', 'child_leaf'))
        ordering = ('order',)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.clean()
        return super().save(force_insert, force_update, using, update_fields)

    # FIXME :: DEPRECATED ??? Move this to validators? (is a model validation - not a business validation?)
    def clean(self):
        if self.child_branch and self.child_leaf:
            raise ValidationError(_("It is forbidden to save a GroupElementYear with a child branch and a child leaf."))

        if self.child_branch == self.parent:
            raise ValidationError(_("It is forbidden to add an element to itself."))

        if self.parent and self.child_branch in self.parent.ascendants_of_branch:
            raise ValidationError(_("It is forbidden to add an element to one of its included elements."))

        if self.child_leaf and self.link_type == LinkTypes.REFERENCE.name:
            raise ValidationError(
                {'link_type': _("You are not allowed to create a reference with a learning unit")}
            )
        self._check_same_academic_year_parent_child_branch()

    # FIXME :: DEPRECATED -  Use AttachOptionsValidator
    def _check_same_academic_year_parent_child_branch(self):
        if (self.parent and self.child_branch) and \
                (self.parent.academic_year.year != self.child_branch.academic_year.year):
            raise ValidationError(_("It is prohibited to attach a group, mini-training or training to an element of "
                                    "another academic year."))

        self._clean_link_type()

    def _clean_link_type(self):
        if getattr(self.parent, 'type', None) in [GroupType.MINOR_LIST_CHOICE.name,
                                                  GroupType.MAJOR_LIST_CHOICE.name] and \
                isinstance(self.child, EducationGroupYear) and self.child.type in MiniTrainingType.minors() + \
                [MiniTrainingType.FSA_SPECIALITY.name, MiniTrainingType.DEEPENING.name]:
            self.link_type = LinkTypes.REFERENCE.name

    @cached_property
    def child(self):
        return self.child_branch or self.child_leaf

    def _verbose_credits(self):
        if self.relative_credits or self.child_branch.credits:
            return "{} ({} {})".format(
                self.child.verbose_title, self.relative_credits or self.child_branch.credits or 0, _("credits")
            )
        else:
            return "{}".format(self.child.verbose_title)


def find_learning_unit_roots(objects, return_result_params=None, luy=None, recursive_conditions=None):
    if return_result_params is None:
        return_result_params = {}
    parents_as_instances = return_result_params.get('parents_as_instances', False)
    with_parents_of_parents = return_result_params.get('with_parents_of_parents', False)
    if with_parents_of_parents and not parents_as_instances:
        raise ValueError("If parameter with_parents_of_parents is True, parameter parents_as_instances must be True")

    roots_by_object_id = {}
    if objects:
        _raise_if_incorrect_instance(objects)
        academic_year = None
        if not luy:
            try:
                academic_year = _extract_common_academic_year(objects)
            except AttributeError:
                academic_year = None

        parents_by_id = _build_parent_list_by_education_group_year_id(academic_year, luy)

        roots_by_object_id = _find_related_formations(objects, parents_by_id, recursive_conditions)

        if parents_as_instances:
            roots_by_object_id = _convert_parent_ids_to_instances(roots_by_object_id)
            if with_parents_of_parents:
                flat_list_of_parents = _flatten_list_of_lists(roots_by_object_id.values())
                roots_by_parent_id = _find_related_formations(flat_list_of_parents, parents_by_id, recursive_conditions)
                roots_by_parent_id = _convert_parent_ids_to_instances(roots_by_parent_id)
                roots_by_object_id = {**roots_by_object_id, **roots_by_parent_id}

    return roots_by_object_id


def _flatten_list_of_lists(list_of_lists):
    return list(set(itertools.chain.from_iterable(list_of_lists)))


def _find_related_formations(objects, parents_by_id, recursive_conditions=None):
    if not objects:
        return {}
    if isinstance(objects[0], LearningUnitYear):
        return {obj.id: _find_elements(parents_by_id, recursive_conditions, child_leaf_id=obj.id) for obj in objects}
    else:
        return {obj.id: _find_elements(parents_by_id, recursive_conditions, child_branch_id=obj.id) for obj in objects}


def _build_parent_list_by_education_group_year_id(academic_year: AcademicYear = None, learning_unit_year=None):
    if academic_year:
        group_elements = GroupElementYear.objects.filter(
            Q(parent__academic_year=academic_year) |
            Q(child_branch__academic_year=academic_year) |
            Q(child_leaf__academic_year=academic_year)
        ).filter(
            parent__isnull=False
        ).filter(
            Q(child_leaf__isnull=False) | Q(child_branch__isnull=False)
        )
    else:
        geys = fetch_row_sql_tree_from_child(child_leaf_id=learning_unit_year.pk)

        group_elements = GroupElementYear.objects.filter(pk__in=[gey['id'] for gey in geys])

    group_elements = group_elements.select_related(
        'education_group_year__education_group_type'
    ).values(
        'parent', 'child_branch', 'child_leaf', 'parent__education_group_type__name',
        'parent__education_group_type__category'
    )
    result = collections.defaultdict(list)
    for group_element_year in group_elements:
        key = _build_child_key(
            child_branch=group_element_year["child_branch"],
            child_leaf=group_element_year["child_leaf"]
        )
        result[key].append(group_element_year)
    return result


def _convert_parent_ids_to_instances(root_ids_by_object_id):
    flat_root_ids = _flatten_list_of_lists(root_ids_by_object_id.values())
    map_instance_by_id = {obj.id: obj for obj in education_group_year.search(id=flat_root_ids)}
    return {
        obj_id: sorted([map_instance_by_id[parent_id] for parent_id in parents], key=lambda obj: obj.acronym)
        for obj_id, parents in root_ids_by_object_id.items()
    }


def _raise_if_incorrect_instance(objects):
    first_obj = objects[0]
    obj_class = first_obj.__class__
    if obj_class not in (LearningUnitYear, EducationGroupYear):
        raise AttributeError("Objects must be either LearningUnitYear or EducationGroupYear instances.")
    if any(obj for obj in objects if obj.__class__ != obj_class):
        raise AttributeError("All objects must be the same class instance ({})".format(obj_class))


def _extract_common_academic_year(objects):
    if len(set(getattr(obj, 'academic_year_id') for obj in objects)) > 1:
        raise AttributeError("The algorithm should load only graph/structure for 1 academic_year "
                             "to avoid too large 'in-memory' data and performance issues.")
    return objects[0].academic_year


def _build_child_key(child_branch=None, child_leaf=None):
    args = [child_leaf, child_branch]
    if not any(args) or all(args):
        raise AttributeError('Only one of the 2 param must bet set (not both of them).')
    if child_leaf:
        branch_part = LearningUnitYear._meta.db_table
        id_part = child_leaf
    else:
        branch_part = EducationGroupYear._meta.db_table
        id_part = child_branch
    return '{branch_part}_{id_part}'.format(branch_part=branch_part, id_part=id_part)


def _is_root_group_element_year(group_element_year, recursive_conditions=None):
    recursive_conditions = {'stop': [], 'continue': []} if recursive_conditions is None \
        else recursive_conditions
    filter_types = COMMON_FILTER_TYPES + recursive_conditions['continue']
    return group_element_year["parent__education_group_type__name"] not in filter_types and \
        group_element_year["parent__education_group_type__name"] in recursive_conditions['stop'] + DEFAULT_ROOT_TYPES


def _find_elements(group_elements_by_child_id, recursive_conditions=None, child_leaf_id=None, child_branch_id=None):
    roots = []
    unique_child_key = _build_child_key(child_leaf=child_leaf_id, child_branch=child_branch_id)
    group_elem_year_parents = group_elements_by_child_id.get(unique_child_key, [])

    for group_elem_year in group_elem_year_parents:
        parent_id = group_elem_year['parent']
        if _is_root_group_element_year(group_elem_year, recursive_conditions):
            # If record matches any filter, we must stop mounting across the hierarchy.
            roots.append(parent_id)
        else:
            # Recursive call ; the parent_id becomes the child_branch.
            roots.extend(
                _find_elements(group_elements_by_child_id, recursive_conditions, child_branch_id=parent_id)
            )

    return list(set(roots))


def fetch_all_group_elements_in_tree(root: EducationGroupYear, queryset, exclude_options=False) -> dict:
    if queryset.model != GroupElementYear:
        raise AttributeError("The querySet arg has to be built from model {}".format(GroupElementYear))

    elements = fetch_row_sql([root.id])

    distinct_group_elem_ids = {elem['id'] for elem in elements}
    queryset = queryset.filter(pk__in=distinct_group_elem_ids)

    group_elems_by_parent_id = {}  # Map {<EducationGroupYear.id>: [GroupElementYear, GroupElementYear...]}
    for group_elem_year in queryset:
        if exclude_options and group_elem_year.child_branch and \
                group_elem_year.child_branch.education_group_type.name == GroupType.OPTION_LIST_CHOICE.name:
            if EducationGroupYear.hierarchy.filter(pk=group_elem_year.child_branch.pk).get_parents(). \
                        filter(education_group_type__name__in=TrainingType.finality_types()).exists():
                continue
        parent_id = group_elem_year.parent_id
        group_elems_by_parent_id.setdefault(parent_id, []).append(group_elem_year)
    return group_elems_by_parent_id


def fetch_row_sql(root_ids):
    return GroupElementYear.objects.get_adjacency_list(root_ids)


def fetch_row_sql_tree_from_child(child_leaf_id: int, academic_year_id: int = None) -> list:
    return GroupElementYear.objects.get_reverse_adjacency_list(
        child_leaf_ids=[child_leaf_id],
        academic_year_id=academic_year_id
    )


def get_or_create_group_element_year(parent, child_branch=None, child_leaf=None):
    if child_branch:
        return GroupElementYear.objects.get_or_create(parent=parent, child_branch=child_branch)
    elif child_leaf:
        return GroupElementYear.objects.get_or_create(parent=parent, child_leaf=child_leaf)
    return AttributeError('child branch OR child leaf params must be set')


def get_all_group_elements_in_tree(root: EducationGroupYear, queryset) -> dict:
    if queryset.model != GroupElementYear:
        raise AttributeError("The querySet arg has to be built from model {}".format(GroupElementYear))

    elements = fetch_row_sql([root.id])

    distinct_group_elem_ids = {elem['id'] for elem in elements}
    return queryset.filter(pk__in=distinct_group_elem_ids)
