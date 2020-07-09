import collections
import itertools
from typing import List, Dict

from base.models import education_group_year, group_element_year
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, MiniTrainingType
from program_management.models.element import Element

DEFAULT_ROOT_CATEGORIES = set(TrainingType) | set(MiniTrainingType) - {MiniTrainingType.OPTION}


#  DEPRECATED Suppress this method when borrowed course filter is refactored OSIS-3376
def find_all_roots_for_academic_year(academic_year_id: int) -> Dict[int, List[int]]:
    root_categories = DEFAULT_ROOT_CATEGORIES
    root_categories_names = [root_type.name for root_type in root_categories]

    child_root_list = group_element_year.GroupElementYear.objects.get_root_list(
        academic_year_id=academic_year_id,
        root_category_name=root_categories_names
    )

    roots_by_children_id = _group_roots_id_by_children_id(child_root_list)

    return roots_by_children_id


#  FIXME move this function out of the repository or replace by using load_trees_from_children()
def find_roots(
        objects: List['Element'],
        as_instances=False,
        with_parents_of_parents=False,
        additional_root_categories: List[EducationGroupTypesEnum] = None,
        exclude_root_categories: List[EducationGroupTypesEnum] = None
):
    _assert_same_academic_year(objects)

    root_categories = (DEFAULT_ROOT_CATEGORIES | set(additional_root_categories or [])) \
        - set(exclude_root_categories or [])
    root_categories_names = [root_type.name for root_type in root_categories]
    child_element_ids = [obj.id for obj in objects]

    child_root_list = group_element_year.GroupElementYear.objects.get_root_list(
        child_element_ids=child_element_ids,
        root_category_name=root_categories_names
    )

    roots_by_children_id = _group_roots_id_by_children_id(child_root_list)

    if with_parents_of_parents:
        flat_list_of_parents = _flatten_list_of_lists(roots_by_children_id.values())
        child_root_list = group_element_year.GroupElementYear.objects.get_root_list(
            child_element_ids=flat_list_of_parents,
            root_category_name=root_categories_names
        )
        roots_by_children_id.update(_group_roots_id_by_children_id(child_root_list))

    if as_instances:
        return _convert_parent_ids_to_instances(roots_by_children_id)

    return roots_by_children_id


def _group_roots_id_by_children_id(child_root_list: List[Dict]) -> Dict[int, List[int]]:
    roots_by_children_id = collections.defaultdict(list)
    for child_root in child_root_list:
        roots_by_children_id[child_root["child_id"]].append(child_root["root_id"])
    return roots_by_children_id


def _flatten_list_of_lists(list_of_lists):
    return list(set(itertools.chain.from_iterable(list_of_lists)))


def _convert_parent_ids_to_instances(root_ids_by_object_id):
    flat_root_ids = _flatten_list_of_lists(root_ids_by_object_id.values())
    map_instance_by_id = {
        obj.id: obj for obj in Element.objects.filter(pk__in=flat_root_ids).select_related('group_year')
    }

    result = collections.defaultdict(list)
    result.update({
        obj_id: sorted([map_instance_by_id[parent_id] for parent_id in parents], key=lambda obj: obj.group_year.acronym)
        for obj_id, parents in root_ids_by_object_id.items()
    })
    return result


def _assert_same_academic_year(objects: List['Element']):
    cnt = collections.Counter()
    for obj in objects:
        if hasattr(obj, 'learning_unit_year') and obj.learning_unit_year:
            cnt[obj.learning_unit_year.academic_year_id] += 1
        elif hasattr(obj, 'group_year') and obj.group_year:
            cnt[obj.group_year.academic_year_id] += 1

    if len(cnt.keys()) > 1:
        raise AttributeError(
            "The algorithm should load only graph/structure for 1 academic_year "
            "to avoid too large 'in-memory' data and performance issues."
        )
