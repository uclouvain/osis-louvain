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
import re

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from base.models import entity_container_year
from base.models.academic_year import current_academic_year
from base.models.enums import active_status
from base.models.enums import learning_unit_year_subtypes, internship_subtypes, \
    learning_unit_year_session, entity_container_year_link_type, learning_unit_year_quadrimesters, attribution_procedure
from base.models.enums.learning_unit_periodicity import ANNUAL
from base.models.group_element_year import GroupElementYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from osis_common.models.auditable_serializable_model import AuditableSerializableModel, AuditableSerializableModelAdmin

AUTHORIZED_REGEX_CHARS = "$*+.^"
REGEX_ACRONYM_CHARSET = "[A-Z0-9" + AUTHORIZED_REGEX_CHARS + "]+"
MINIMUM_CREDITS = 0.0
MAXIMUM_CREDITS = 500


class LearningUnitYearAdmin(AuditableSerializableModelAdmin):
    list_display = ('external_id', 'acronym', 'specific_title', 'academic_year', 'credits', 'changed', 'structure',
                    'status')
    fieldsets = ((None, {'fields': ('academic_year', 'learning_unit', 'learning_container_year', 'acronym',
                                    'specific_title', 'specific_title_english', 'subtype', 'credits', 'decimal_scores',
                                    'structure', 'internship_subtype', 'status', 'session',
                                    'quadrimester', 'attribution_procedure', 'summary_editable')}),)
    list_filter = ('academic_year', 'decimal_scores', 'summary_editable')
    raw_id_fields = ('learning_unit', 'learning_container_year', 'structure')
    search_fields = ['acronym', 'structure__acronym', 'external_id']


class LearningUnitYear(AuditableSerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.ForeignKey('AcademicYear')
    learning_unit = models.ForeignKey('LearningUnit')
    learning_container_year = models.ForeignKey('LearningContainerYear', blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True)
    specific_title = models.CharField(max_length=255, blank=True, null=True)
    specific_title_english = models.CharField(max_length=250, blank=True, null=True)
    subtype = models.CharField(max_length=50, choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES)
    credits = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                  validators=[MinValueValidator(MINIMUM_CREDITS), MaxValueValidator(MAXIMUM_CREDITS)])
    decimal_scores = models.BooleanField(default=False)
    structure = models.ForeignKey('Structure', blank=True, null=True)
    internship_subtype = models.CharField(max_length=250, blank=True, null=True,
                                          choices=internship_subtypes.INTERNSHIP_SUBTYPES)
    status = models.BooleanField(default=False)
    session = models.CharField(max_length=50, blank=True, null=True,
                               choices=learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION)
    quadrimester = models.CharField(max_length=4, blank=True, null=True,
                                    choices=learning_unit_year_quadrimesters.LEARNING_UNIT_YEAR_QUADRIMESTERS)
    attribution_procedure = models.CharField(max_length=20, blank=True, null=True,
                                             choices=attribution_procedure.ATTRIBUTION_PROCEDURES)
    summary_editable = models.BooleanField(default=True, verbose_name=_("summary_editable"))

    class Meta:
        unique_together = ('learning_unit', 'academic_year', 'deleted')

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)

    @property
    def subdivision(self):
        if self.acronym and self.learning_container_year:
            return self.acronym.replace(self.learning_container_year.acronym, "")
        return None

    @property
    def parent(self):
        if self.subdivision and self.is_partim():
            return LearningUnitYear.objects.filter(
                subtype=learning_unit_year_subtypes.FULL,
                learning_container_year=self.learning_container_year,
            ).get()
        return None

    @property
    def same_container_learning_unit_years(self):
        return LearningUnitYear.objects.filter(
            learning_container_year=self.learning_container_year
        ).order_by('acronym')

    @property
    def allocation_entity(self):
        entity_container_yr = entity_container_year.search(
            link_type=entity_container_year_link_type.ALLOCATION_ENTITY,
            learning_container_year=self.learning_container_year
        ).first()
        return entity_container_yr.entity if entity_container_yr else None

    @property
    def complete_title(self):
        common_tit = None
        if self.learning_container_year:
            common_tit = self.learning_container_year.common_title

        if self.specific_title and common_tit:
            return "{} {}".format(common_tit, self.specific_title)
        return common_tit

    @property
    def container_common_title(self):
        if self.learning_container_year:
            return self.learning_container_year.common_title
        return ''

    def get_partims_related(self):
        if self.is_full() and self.learning_container_year:
            return self.learning_container_year.get_partims_related()
        return LearningUnitYear.objects.none()

    def find_list_group_element_year(self):
        return GroupElementYear.objects.filter(child_leaf=self).select_related('parent')

    def get_learning_unit_next_year(self):
        try:
            return LearningUnitYear.objects.get(learning_unit=self.learning_unit,
                                                academic_year__year=(self.academic_year.year + 1))
        except LearningUnitYear.DoesNotExist:
            return None

    @property
    def in_charge(self):
        return self.learning_container_year and self.learning_container_year.in_charge

    def is_in_proposal(self):
        return ProposalLearningUnit.objects.filter(learning_unit_year=self).exists()

    def find_gte_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gte=self.academic_year.year) \
            .order_by('academic_year__year')

    def find_gt_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gt=self.academic_year.year) \
            .order_by('academic_year__year')

    def is_past(self):
        return self.academic_year.year < current_academic_year().year

    def can_update_by_faculty_manager(self):
        result = False

        if not self.learning_container_year:
            return result

        current_year = current_academic_year().year
        year = self.academic_year.year

        if self.learning_unit.periodicity == ANNUAL and year <= current_year + 1:
            result = True
        elif self.learning_unit.periodicity != ANNUAL and year <= current_year + 2:
            result = True
        return result

    def is_full(self):
        return self.subtype == learning_unit_year_subtypes.FULL

    def is_partim(self):
        return self.subtype == learning_unit_year_subtypes.PARTIM


def get_by_id(learning_unit_year_id):
    return LearningUnitYear.objects.select_related('learning_container_year__learning_container') \
        .get(pk=learning_unit_year_id)


def find_by_acronym(acronym):
    return LearningUnitYear.objects.filter(acronym=acronym).select_related('learning_container_year')


def _is_regex(acronym):
    return set(AUTHORIZED_REGEX_CHARS).intersection(set(acronym))


def search(academic_year_id=None, acronym=None, learning_container_year_id=None, learning_unit=None,
           title=None, subtype=None, status=None, container_type=None, tutor=None, *args, **kwargs):
    queryset = LearningUnitYear.objects

    if academic_year_id:
        queryset = queryset.filter(academic_year=academic_year_id)

    if acronym:
        if _is_regex(acronym):
            queryset = queryset.filter(acronym__iregex=r"(" + acronym + ")")
        else:
            queryset = queryset.filter(acronym__icontains=acronym)

    if learning_container_year_id is not None:
        if isinstance(learning_container_year_id, list):
            queryset = queryset.filter(learning_container_year__in=learning_container_year_id)
        elif learning_container_year_id:
            queryset = queryset.filter(learning_container_year=learning_container_year_id)

    if learning_unit:
        queryset = queryset.filter(learning_unit=learning_unit)

    if title:
        queryset = queryset.\
            filter(Q(specific_title__icontains=title) | Q(learning_container_year__common_title__icontains=title))

    if subtype:
        queryset = queryset.filter(subtype=subtype)

    if status:
        queryset = queryset.filter(status=_convert_status_bool(status))

    if container_type:
        queryset = queryset.filter(learning_container_year__container_type=container_type)

    if tutor:
        queryset = queryset.\
            filter(Q(attribution__tutor__person__first_name__icontains=tutor) |
                   Q(attribution__tutor__person__last_name__icontains=tutor))

    return queryset.select_related('learning_container_year', 'academic_year')


def _convert_status_bool(status):
    if status in (active_status.ACTIVE, active_status.INACTIVE):
        boolean = status == active_status.ACTIVE
    else:
        boolean = status
    return boolean


def count_search_results(**kwargs):
    return search(**kwargs).count()


def find_gte_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__gte=academic_yr.year,
                                           acronym__iexact=acronym)


def find_lt_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__lt=academic_yr.year,
                                           acronym__iexact=acronym).order_by('academic_year')


def check_if_acronym_regex_is_valid(acronym):
    if isinstance(acronym, str):
        return re.fullmatch(REGEX_ACRONYM_CHARSET, acronym.upper())


def find_max_credits_of_related_partims(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().aggregate(max_credits=models.Max("credits"))["max_credits"]
