import collections
import itertools
from typing import List

from base.models import education_group_year, group_element_year
from base.models import learning_unit_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import EducationGroupTypesEnum, TrainingType, MiniTrainingType

DEFAULT_ROOT_CATEGORIES = set(TrainingType) | set(MiniTrainingType) - {MiniTrainingType.OPTION}


#  DEPRECATED Suppress this method when borrowed course filter is refactored OSIS-3376
def find_all_roots_for_academic_year(academic_year_id):
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
        objects,
        as_instances=False,
        with_parents_of_parents=False,
        additional_root_categories: List[EducationGroupTypesEnum] = None,
        exclude_root_categories: List[EducationGroupTypesEnum] = None
):
    _assert_same_academic_year(objects)
    _assert_same_objects_class(objects)

    root_categories = (DEFAULT_ROOT_CATEGORIES | set(additional_root_categories or [])) \
        - set(exclude_root_categories or [])
    root_categories_names = [root_type.name for root_type in root_categories]

    child_branch_ids = [obj.id for obj in objects if isinstance(obj, EducationGroupYear)]
    child_leaf_ids = [obj.id for obj in objects if isinstance(obj, learning_unit_year.LearningUnitYear)]

    child_root_list = group_element_year.GroupElementYear.objects.get_root_list(
        child_branch_ids=child_branch_ids,
        child_leaf_ids=child_leaf_ids,
        root_category_name=root_categories_names
    )

    roots_by_children_id = _group_roots_id_by_children_id(child_root_list)

    if with_parents_of_parents:
        flat_list_of_parents = _flatten_list_of_lists(roots_by_children_id.values())
        child_root_list = group_element_year.GroupElementYear.objects.get_root_list(
            child_branch_ids=flat_list_of_parents,
            root_category_name=root_categories_names
        )
        roots_by_children_id.update(_group_roots_id_by_children_id(child_root_list))

    if as_instances:
        return _convert_parent_ids_to_instances(roots_by_children_id)

    return roots_by_children_id


def _group_roots_id_by_children_id(child_root_list):
    roots_by_children_id = collections.defaultdict(list)
    for child_root in child_root_list:
        roots_by_children_id[child_root["child_id"]].append(child_root["root_id"])
    return roots_by_children_id


def _flatten_list_of_lists(list_of_lists):
    return list(set(itertools.chain.from_iterable(list_of_lists)))


def _convert_parent_ids_to_instances(root_ids_by_object_id):
    flat_root_ids = _flatten_list_of_lists(root_ids_by_object_id.values())
    map_instance_by_id = {obj.id: obj for obj in education_group_year.search(id=flat_root_ids)}
    result = collections.defaultdict(list)
    result.update({
        obj_id: sorted([map_instance_by_id[parent_id] for parent_id in parents], key=lambda obj: obj.acronym)
        for obj_id, parents in root_ids_by_object_id.items()
    })
    return result


def _assert_same_objects_class(objects):
    if not objects:
        return
    first_obj = objects[0]
    obj_class = first_obj.__class__
    if obj_class not in (learning_unit_year.LearningUnitYear, EducationGroupYear):
        raise AttributeError("Objects must be either LearningUnitYear or EducationGroupYear instances.")
    if any(obj for obj in objects if obj.__class__ != obj_class):
        raise AttributeError("All objects must be the same class instance ({})".format(obj_class))


def _assert_same_academic_year(objects):
    if len(set(getattr(obj, 'academic_year_id') for obj in objects)) > 1:
        raise AttributeError(
            "The algorithm should load only graph/structure for 1 academic_year "
            "to avoid too large 'in-memory' data and performance issues."
        )
