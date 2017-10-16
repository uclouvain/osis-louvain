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
from django.db import models
from django.db.models import F
from django.db.models import Prefetch
from django.db.models import Q
from attribution.models.enums import function
from base.models import entity_container_year
from base.models.academic_year import current_academic_year
from base.models.enums import entity_container_year_link_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from osis_common.models.auditable_serializable_model import AuditableSerializableModel, AuditableSerializableModelAdmin
from attribution.models import attribution_charge
from base.models.enums import component_type


class AttributionAdmin(AuditableSerializableModelAdmin):
    list_display = ('tutor', 'function', 'score_responsible', 'learning_unit_year', 'start_year', 'end_year', 'changed')
    list_filter = ('function', 'learning_unit_year__academic_year', 'score_responsible')
    fieldsets = ((None, {'fields': ('learning_unit_year', 'tutor', 'function', 'score_responsible', 'start_year',
                                    'end_year')}),)
    raw_id_fields = ('learning_unit_year', 'tutor')
    search_fields = ['tutor__person__first_name', 'tutor__person__last_name', 'learning_unit_year__acronym',
                     'tutor__person__global_id']


class Attribution(AuditableSerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    start_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    end_date = models.DateField(auto_now=False, blank=True, null=True, auto_now_add=False)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    function = models.CharField(max_length=35, blank=True, null=True, choices=function.FUNCTIONS, db_index=True)
    learning_unit_year = models.ForeignKey('base.LearningUnitYear')
    tutor = models.ForeignKey('base.Tutor')
    score_responsible = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.tutor.person, self.function)

    @property
    def duration(self):
        if self.start_year and self.end_year:
            return (self.end_year - self.start_year) + 1
        return None

    @property
    def volume_lecturing(self):
        return self.get_attribution(component_type.LECTURING)

    @property
    def volume_practical(self):
        return self.get_attribution(component_type.PRACTICAL_EXERCISES)

    def get_attribution(self, a_component_type):
        attribution = attribution_charge.find_by_component_type(self, a_component_type)
        if attribution:
            return attribution.allocation_charge
        return "{0:.2f}".format(float(0))


def search(tutor=None, learning_unit_year=None, score_responsible=None, list_learning_unit_year=None):
    queryset = Attribution.objects
    if tutor:
        queryset = queryset.filter(tutor=tutor)
    if learning_unit_year:
        queryset = queryset.filter(learning_unit_year=learning_unit_year)
    if score_responsible is not None:
        queryset = queryset.filter(score_responsible=score_responsible)
    if list_learning_unit_year is not None:
        queryset = queryset.filter(learning_unit_year__in=list_learning_unit_year)
    return queryset.select_related('tutor__person', 'learning_unit_year')


def find_all_responsibles_by_learning_unit_year(a_learning_unit_year):
    attribution_list = Attribution.objects.filter(learning_unit_year=a_learning_unit_year,
                                                  score_responsible=True) \
        .distinct("tutor") \
        .select_related("tutor")
    return [attribution.tutor for attribution in attribution_list]


def find_all_tutors_by_learning_unit_year(a_learning_unit_year):
    attribution_list = Attribution.objects.filter(learning_unit_year=a_learning_unit_year) \
        .distinct("tutor").values_list('id', flat=True)
    result = Attribution.objects.filter(id__in=attribution_list).order_by("-score_responsible", "tutor__person")
    return [[attribution.tutor, attribution.score_responsible] for attribution in result]


def find_responsible(a_learning_unit_year):
    tutors_list = find_all_responsibles_by_learning_unit_year(a_learning_unit_year)
    if tutors_list:
        return tutors_list[0]
    return None


def find_tutor(a_learning_unit_year):
    tutors_list = find_all_tutors_by_learning_unit_year(a_learning_unit_year)
    if tutors_list:
        return tutors_list[0]
    return None


def is_score_responsible(user, learning_unit_year):
    return Attribution.objects.filter(learning_unit_year=learning_unit_year,
                                      score_responsible=True,
                                      tutor__person__user=user)\
                              .count() > 0


def search_scores_responsible(learning_unit_title, course_code, entities, tutor, responsible):
    queryset = Attribution.objects.filter(learning_unit_year__academic_year=current_academic_year())
    if learning_unit_title:
        queryset = queryset.filter(learning_unit_year__title__icontains=learning_unit_title)
    if course_code:
        queryset = queryset.filter(learning_unit_year__acronym__icontains=course_code)
    if tutor and responsible:
        queryset = queryset \
            .filter(learning_unit_year__id__in=LearningUnitYear.objects
                    .filter(attribution__id__in=Attribution.objects
                            .filter(score_responsible=True, tutor__person__in=Person.objects
                                    .filter(Q(first_name__icontains=responsible) |
                                            Q(last_name__icontains=responsible))))) \
            .filter(tutor__person__in=Person.objects
                    .filter(Q(first_name__icontains=tutor) |
                            Q(last_name__icontains=tutor)))
    else:
        if tutor:
            queryset = queryset \
                .filter(tutor__person__in=Person.objects.filter(Q(first_name__icontains=tutor) |
                                                                Q(last_name__icontains=tutor)))
        if responsible:
            queryset = queryset \
                .filter(score_responsible=True, tutor__person__in=Person.objects
                        .filter(Q(first_name__icontains=responsible) |
                                Q(last_name__icontains=responsible)))
    if entities:
        entities_ids = [entity.id for entity in entities]
        l_container_year_ids = entity_container_year.search(link_type=entity_container_year_link_type.ALLOCATION_ENTITY,
                                                            entity_id=entities_ids)\
                                                    .values_list('learning_container_year_id', flat=True)
        queryset = queryset.filter(learning_unit_year__learning_container_year__id__in=l_container_year_ids)

    # Prefetch entity version
    queryset = queryset.prefetch_related(
        Prefetch('learning_unit_year__learning_container_year__entitycontaineryear_set',
                 queryset=entity_container_year.search(link_type=entity_container_year_link_type.ALLOCATION_ENTITY)
                 .prefetch_related(
                     Prefetch('entity__entityversion_set', to_attr='entity_versions')
                 ), to_attr='entities_containers_year')
    )
    return queryset.select_related('learning_unit_year')\
                   .distinct("learning_unit_year")


def find_all_responsible_by_learning_unit_year(learning_unit_year):
    all_tutors = Attribution.objects.filter(learning_unit_year=learning_unit_year) \
        .distinct("tutor").values_list('id', flat=True)
    return Attribution.objects.filter(id__in=all_tutors).prefetch_related('tutor')\
                              .order_by("tutor__person")


def find_by_tutor(tutor):
    if tutor:
        return [att.learning_unit_year for att in list(search(tutor=tutor))]
    else:
        return None


def clear_responsible_by_learning_unit_year(learning_unit_year):
    Attribution.objects.filter(learning_unit_year=learning_unit_year,
                               score_responsible=True,
                               learning_unit_year__academic_year=current_academic_year())\
                       .update(score_responsible=False)


def find_by_id(attribution_id):
    return Attribution.objects.get(pk=attribution_id)


def find_by_learning_unit_year(learning_unit_year=None):
    queryset = Attribution.objects
    if learning_unit_year:
        queryset = queryset.filter(learning_unit_year=learning_unit_year)
    return queryset.select_related('tutor__person', 'learning_unit_year') \
        .order_by('tutor__person__last_name', 'tutor__person__first_name')
