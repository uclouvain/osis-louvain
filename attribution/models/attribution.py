##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.db.models import Prefetch

from attribution.models.enums.function import Functions
from base.models import entity_container_year
from base.models import person
from base.models.academic_year import current_academic_year
from base.models.enums import entity_container_year_link_type
from base.models.learning_unit_year import LearningUnitYear
from osis_common.models.serializable_model import SerializableModelAdmin, SerializableModel


class AttributionAdmin(SerializableModelAdmin):
    list_display = ('tutor', 'function', 'score_responsible', 'summary_responsible', 'learning_unit_year', 'start_year',
                    'end_year', 'changed')
    list_filter = ('learning_unit_year__academic_year', 'function', 'score_responsible', 'summary_responsible')
    fieldsets = ((None, {'fields': ('learning_unit_year', 'tutor', 'function', 'score_responsible',
                                    'summary_responsible', 'start_year', 'end_year')}),)
    raw_id_fields = ('learning_unit_year', 'tutor')
    search_fields = ['tutor__person__first_name', 'tutor__person__last_name', 'learning_unit_year__acronym',
                     'tutor__person__global_id']


class Attribution(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    function = models.CharField(max_length=35, blank=True, null=True, choices=Functions.choices(), db_index=True)
    learning_unit_year = models.ForeignKey('base.LearningUnitYear')
    tutor = models.ForeignKey('base.Tutor')
    score_responsible = models.BooleanField(default=False)
    summary_responsible = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.tutor.person, self.function)

    @property
    def duration(self):
        if self.start_year and self.end_year:
            return (self.end_year - self.start_year) + 1
        return None


def search(tutor=None, learning_unit_year=None, score_responsible=None, summary_responsible=None,
           list_learning_unit_year=None):
    queryset = Attribution.objects
    if tutor:
        queryset = queryset.filter(tutor=tutor)
    if learning_unit_year:
        queryset = queryset.filter(learning_unit_year=learning_unit_year)
    if score_responsible is not None:
        queryset = queryset.filter(score_responsible=score_responsible)
    if summary_responsible is not None:
        queryset = queryset.filter(summary_responsible=summary_responsible)
    if list_learning_unit_year is not None:
        queryset = queryset.filter(learning_unit_year__in=list_learning_unit_year)
    return queryset.select_related('tutor__person', 'learning_unit_year')


def find_all_responsibles_by_learning_unit_year(a_learning_unit_year):
    attribution_list = Attribution.objects.filter(learning_unit_year=a_learning_unit_year,
                                                  score_responsible=True) \
        .distinct("tutor") \
        .select_related("tutor")
    return [attribution.tutor for attribution in attribution_list]


def find_all_tutors_by_learning_unit_year(a_learning_unit_year, responsibles_order=""):
    attribution_list = Attribution.objects.filter(learning_unit_year=a_learning_unit_year) \
        .distinct("tutor").values_list('id', flat=True)
    result = Attribution.objects.filter(id__in=attribution_list).order_by(responsibles_order, "tutor__person")
    return [
        [attribution.tutor, attribution.score_responsible, attribution.summary_responsible]
        for attribution in result
    ]


def find_responsible(a_learning_unit_year):
    tutors_list = find_all_responsibles_by_learning_unit_year(a_learning_unit_year)
    if tutors_list:
        return tutors_list[0]
    return None


def is_score_responsible(user, learning_unit_year):
    return Attribution.objects.filter(learning_unit_year=learning_unit_year,
                                      score_responsible=True,
                                      tutor__person__user=user)\
                              .count() > 0


def search_scores_responsible(learning_unit_title, course_code, entities, tutor, responsible):
    queryset = search_by_learning_unit_this_year(course_code, learning_unit_title)
    if tutor and responsible:
        queryset = queryset \
            .filter(learning_unit_year__id__in=LearningUnitYear.objects
                    .filter(attribution__id__in=Attribution.objects
                            .filter(score_responsible=True,
                                    tutor__person__in=person.find_by_firstname_or_lastname(responsible)))) \
            .filter(tutor__person__in=person.find_by_firstname_or_lastname(tutor))
    else:
        if tutor:
            queryset = _filter_by_tutor(queryset, tutor)
        if responsible:
            queryset = queryset \
                .filter(score_responsible=True, tutor__person__in=person.find_by_firstname_or_lastname(responsible))
    if entities:
        queryset = filter_by_entities(queryset, entities)

    queryset = _prefetch_entity_version(queryset)

    return queryset.select_related('learning_unit_year')\
                   .distinct("learning_unit_year")


def filter_attributions(attributions_queryset, entities, tutor, responsible):
    queryset = attributions_queryset
    if tutor:
        queryset = _filter_by_tutor(queryset, tutor)
    if responsible:
        queryset = queryset \
            .filter(summary_responsible=True, tutor__person__in=person.find_by_firstname_or_lastname(responsible))
    if entities:
        queryset = filter_by_entities(queryset, entities)

    queryset = _prefetch_entity_version(queryset)

    return queryset.select_related('learning_unit_year').distinct("learning_unit_year")


def search_by_learning_unit_this_year(code, specific_title, academic_year=None):
    if academic_year is None:
        academic_year = current_academic_year()
    queryset = Attribution.objects.filter(learning_unit_year__academic_year=academic_year)
    if specific_title:
        queryset = queryset.filter(learning_unit_year__specific_title__icontains=specific_title)
    if code:
        queryset = queryset.filter(learning_unit_year__acronym__icontains=code)
    return queryset


def filter_by_entities(queryset, entities):
    entities_ids = [entity.id for entity in entities]
    l_container_year_ids = entity_container_year.search(link_type=entity_container_year_link_type.ALLOCATION_ENTITY,
                                                        entity_id=entities_ids) \
        .values_list('learning_container_year_id', flat=True)
    queryset = queryset.filter(learning_unit_year__learning_container_year__id__in=l_container_year_ids)
    return queryset


def find_all_responsible_by_learning_unit_year(learning_unit_year):
    all_tutors = Attribution.objects.filter(learning_unit_year=learning_unit_year) \
        .distinct("tutor").values_list('id', flat=True)
    return Attribution.objects.filter(id__in=all_tutors).prefetch_related('tutor')\
                              .order_by("tutor__person")


def find_all_summary_responsibles_by_learning_unit_years(learning_unit_years):
    summary_responsibles_group_by_luy = {}
    all_attributions = Attribution.objects.filter(
        learning_unit_year__in=learning_unit_years,
        summary_responsible=True).select_related('tutor__person')
    for attribution in all_attributions:
        summary_responsibles_group_by_luy.setdefault(attribution.learning_unit_year_id, []).append(attribution.tutor)
    return summary_responsibles_group_by_luy


def find_by_tutor(tutor):
    if tutor:
        return [att.learning_unit_year for att in list(search(tutor=tutor))]
    else:
        return None


def clear_scores_responsible_by_learning_unit_year(learning_unit_year_pk):
    _clear_attributions_field_of_learning__unit_year(learning_unit_year_pk, "score_responsible")


def clear_summary_responsible_by_learning_unit_year(learning_unit_year_pk):
    _clear_attributions_field_of_learning__unit_year(learning_unit_year_pk, "summary_responsible")


def _clear_attributions_field_of_learning__unit_year(learning_unit_year_pk, field_to_clear):
    attributions = search_by_learning_unit_year_pk(learning_unit_year_pk)
    for attribution in attributions:
        setattr(attribution, field_to_clear, False)
        attribution.save()


def search_by_learning_unit_year_pk(learning_unit_year_pk):
    return Attribution.objects.filter(learning_unit_year__id=learning_unit_year_pk)


def find_by_id(attribution_id):
    return Attribution.objects.get(pk=attribution_id)


def find_by_learning_unit_year(learning_unit_year=None):
    queryset = Attribution.objects
    if learning_unit_year:
        queryset = queryset.filter(learning_unit_year=learning_unit_year)
    return queryset.select_related('tutor__person', 'learning_unit_year') \
        .order_by('tutor__person__last_name', 'tutor__person__first_name')


def _filter_by_tutor(queryset, tutor):
    return queryset.filter(tutor__person__in=person.find_by_firstname_or_lastname(tutor))


def _prefetch_entity_version(queryset):
    return queryset.prefetch_related(
        Prefetch('learning_unit_year__learning_container_year__entitycontaineryear_set',
                 queryset=entity_container_year.search(link_type=entity_container_year_link_type.ALLOCATION_ENTITY)
                 .prefetch_related(
                     Prefetch('entity__entityversion_set', to_attr='entity_versions')
                 ), to_attr='entities_containers_year')
    )
