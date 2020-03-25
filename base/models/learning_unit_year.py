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

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, When, CharField, Value, Case, Subquery, OuterRef
from django.db.models.functions import Concat
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.business.learning_container_year import get_learning_container_year_warnings
from base.models import entity_version
from base.models import group_element_year
from base.models.academic_year import compute_max_academic_year_adjournment, AcademicYear
from base.models.entity_version import get_entity_version_parent_or_itself_from_type
from base.models.enums import active_status, learning_container_year_types
from base.models.enums import learning_unit_year_subtypes, internship_subtypes, \
    learning_unit_year_session, entity_container_year_link_type, quadrimesters, attribution_procedure
from base.models.enums.learning_container_year_types import COURSE, INTERNSHIP
from base.models.enums.learning_unit_year_periodicity import PERIODICITY_TYPES, ANNUAL, BIENNIAL_EVEN, BIENNIAL_ODD
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit import LEARNING_UNIT_ACRONYM_REGEX_MODEL
from base.models.prerequisite_item import PrerequisiteItem
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin, SerializableModelManager, \
    SerializableQuerySet

AUTHORIZED_REGEX_CHARS = "$*+.^"
REGEX_ACRONYM_CHARSET = "[A-Z0-9" + AUTHORIZED_REGEX_CHARS + "]+"
MINIMUM_CREDITS = 0.0
MAXIMUM_CREDITS = 500

# This query can be used as annotation in a LearningUnitYearQuerySet with a RawSql.
# It return a dictionary with the closest trainings and mini_training (except 'option')
# through the recursive database structure
# ! It is a raw SQL : Use it only in last resort !
# The returned structure is :
# { id, gs_origin, child_branch_id, child_leaf_id, parent_id, acronym,
#   title, category, name, id (for education_group_type) and level }
SQL_RECURSIVE_QUERY_EDUCATION_GROUP_TO_CLOSEST_TRAININGS = """\
WITH RECURSIVE group_element_year_parent AS (
    SELECT gs.id, gs.id AS gs_origin, child_branch_id, child_leaf_id, parent_id, educ.acronym, educ.title,
    educ_type.category, educ_type.name, educ_type.id, 0 AS level
    
    FROM base_groupelementyear AS gs
    INNER JOIN base_educationgroupyear AS educ ON gs.parent_id = educ.id
    INNER JOIN base_educationgrouptype AS educ_type on educ.education_group_type_id = educ_type.id
    WHERE gs.child_leaf_id = "base_learningunityear"."id" 
    
    UNION ALL
    
    SELECT parent.id, gs_origin, parent.child_branch_id, parent.child_leaf_id, parent.parent_id, 
    educ.acronym, educ.title, educ_type.category, educ_type.name, educ_type.id, child.level + 1
    
    FROM base_groupelementyear AS parent
    INNER JOIN base_educationgroupyear AS educ ON parent.parent_id = educ.id
    INNER JOIN base_educationgrouptype AS educ_type ON educ.education_group_type_id = educ_type.id
    INNER JOIN base_educationgroupyear AS educ_child ON parent.child_branch_id = educ_child.id
    INNER JOIN base_educationgrouptype AS educ_type_child ON educ_child.education_group_type_id = educ_type_child.id
    INNER JOIN group_element_year_parent AS child on parent.child_branch_id = child.parent_id
    WHERE not(educ_type_child.name != 'OPTION' AND educ_type_child.category IN ('MINI_TRAINING', 'TRAINING'))
)

SELECT to_jsonb(array_agg(row_to_json(group_element_year_parent))) FROM group_element_year_parent
WHERE name != 'OPTION' AND category IN ('MINI_TRAINING', 'TRAINING') 
"""


def academic_year_validator(value):
    academic = AcademicYear.objects.get(pk=value)
    academic_year_max = compute_max_academic_year_adjournment()
    if academic.year > academic_year_max:
        raise ValidationError(
            _('Please select an academic year lower than %(academic_year_max)d.') % {
                'academic_year_max': academic_year_max,
            }
        )


class LearningUnitYearAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('external_id', 'acronym', 'specific_title', 'academic_year', 'credits', 'changed', 'structure',
                    'status')
    list_filter = ('academic_year', 'decimal_scores', 'summary_locked')
    search_fields = ['acronym', 'structure__acronym', 'external_id', 'id']
    actions = [
        'resend_messages_to_queue',
    ]


class LearningUnitYearQuerySet(SerializableQuerySet):
    def annotate_full_title(self):
        return self.annotate_full_title_class_method(self)

    @classmethod
    def annotate_full_title_class_method(cls, queryset):
        return queryset.annotate(
            full_title=Case(
                When(
                    Q(learning_container_year__common_title__isnull=True) |
                    Q(learning_container_year__common_title__exact=''),
                    then='specific_title'
                ),
                When(
                    Q(specific_title__isnull=True) | Q(specific_title__exact=''),
                    then='learning_container_year__common_title'
                ),
                default=Concat('learning_container_year__common_title', Value(' - '), 'specific_title'),
                output_field=CharField(),
            ),
            full_title_en=Case(
                When(
                    Q(learning_container_year__common_title_english__isnull=True) |
                    Q(learning_container_year__common_title_english__exact=''),
                    then='specific_title_english'
                ),
                When(
                    Q(specific_title_english__isnull=True) | Q(specific_title_english__exact=''),
                    then='learning_container_year__common_title_english'
                ),
                default=Concat('learning_container_year__common_title_english', Value(' - '), 'specific_title_english'),
                output_field=CharField(),
            ),
        )

    @classmethod
    def annotate_entity_requirement_acronym(cls, queryset):
        entity_requirement = entity_version.EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__requirement_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]
        return queryset.annotate(
            entity_requirement=Subquery(entity_requirement)
        )

    @classmethod
    def annotate_entity_allocation_acronym(cls, queryset):
        entity_allocation = entity_version.EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__allocation_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

        return queryset.annotate(
            entity_allocation=Subquery(entity_allocation)
        )

    @classmethod
    def annotate_entities_allocation_and_requirement_acronym(cls, queryset):
        return cls.annotate_entity_allocation_acronym(
            cls.annotate_entity_requirement_acronym(queryset)
        )


class BaseLearningUnitYearManager(SerializableModelManager):
    def get_queryset(self):
        return LearningUnitYearQuerySet(self.model, using=self._db)


class LearningUnitYearWithContainerManager(models.Manager):
    def get_queryset(self):
        # FIXME For the moment, the learning_unit_year without container must be hide !
        return super().get_queryset().select_related('learning_container_year')\
            .filter(learning_container_year__isnull=False)


class LearningUnitYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    academic_year = models.ForeignKey(AcademicYear, verbose_name=_('Academic year'),
                                      validators=[academic_year_validator], on_delete=models.PROTECT)
    learning_unit = models.ForeignKey('LearningUnit', on_delete=models.CASCADE)

    learning_container_year = models.ForeignKey('LearningContainerYear', null=True, on_delete=models.CASCADE)

    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True, verbose_name=_('Code'),
                               validators=[RegexValidator(LEARNING_UNIT_ACRONYM_REGEX_MODEL)])
    specific_title = models.CharField(max_length=255, blank=True, null=True,
                                      verbose_name=_('French title proper'))
    specific_title_english = models.CharField(max_length=250, blank=True, null=True,
                                              verbose_name=_('English title proper'))
    subtype = models.CharField(max_length=50, choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
                               default=learning_unit_year_subtypes.FULL)
    credits = models.DecimalField(null=True, max_digits=5, decimal_places=2,
                                  validators=[MinValueValidator(MINIMUM_CREDITS), MaxValueValidator(MAXIMUM_CREDITS)],
                                  verbose_name=_('Credits'))
    decimal_scores = models.BooleanField(default=False)
    structure = models.ForeignKey('Structure', blank=True, null=True, on_delete=models.CASCADE)
    internship_subtype = models.CharField(max_length=250, blank=True, null=True,
                                          verbose_name=_('Internship subtype'),
                                          choices=internship_subtypes.INTERNSHIP_SUBTYPES)
    status = models.BooleanField(default=False, verbose_name=_('Active'))
    session = models.CharField(max_length=50, blank=True, null=True,
                               choices=learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION,
                               verbose_name=_('Session derogation'))
    quadrimester = models.CharField(max_length=9, blank=True, null=True, verbose_name=_('Quadrimester'),
                                    choices=quadrimesters.LearningUnitYearQuadrimester.choices())

    attribution_procedure = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name=_('Procedure'),
        choices=attribution_procedure.ATTRIBUTION_PROCEDURES
    )

    summary_locked = models.BooleanField(default=False, verbose_name=_("blocked update for tutor"))

    professional_integration = models.BooleanField(default=False, verbose_name=_('professional integration'))

    campus = models.ForeignKey('Campus', null=True, verbose_name=_("Learning location"), on_delete=models.PROTECT)

    language = models.ForeignKey('reference.Language', null=True, verbose_name=_('Language'), on_delete=models.PROTECT)

    periodicity = models.CharField(max_length=20, choices=PERIODICITY_TYPES, default=ANNUAL,
                                   verbose_name=_('Periodicity'))

    objects = BaseLearningUnitYearManager()
    objects_with_container = LearningUnitYearWithContainerManager()

    _warnings = None

    class Meta:
        unique_together = (('learning_unit', 'academic_year'), ('acronym', 'academic_year'))
        ordering = ('academic_year', 'acronym')
        verbose_name = _("Learning unit year")
        permissions = (
            ("can_receive_emails_about_automatic_postponement", "Can receive emails about automatic postponement"),
        )

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

    @cached_property
    def allocation_entity(self):
        return self.get_entity(entity_container_year_link_type.ALLOCATION_ENTITY)

    @cached_property
    def requirement_entity(self):
        return self.get_entity(entity_container_year_link_type.REQUIREMENT_ENTITY)

    def is_service(self, entities_version, *args, **kwargs):
        if getattr(self, 'externallearningunityear', None):
            if self.externallearningunityear.mobility:
                return False
        if self.requirement_entity and self.allocation_entity:
            return get_entity_version_parent_or_itself_from_type(entities_version,
                                                                 entity=self.requirement_entity.most_recent_acronym,
                                                                 entity_type='FACULTY') \
                   != get_entity_version_parent_or_itself_from_type(entities_version,
                                                                    entity=self.allocation_entity.most_recent_acronym,
                                                                    entity_type='FACULTY')
        else:
            return False

    @property
    def complete_title(self):
        complete_title = self.specific_title
        if self.learning_container_year:
            complete_title = ' - '.join(filter(None, [self.learning_container_year.common_title, self.specific_title]))
        return complete_title

    @property
    def complete_title_english(self):
        complete_title_english = self.specific_title_english
        if self.learning_container_year:
            complete_title_english = ' - '.join(filter(None, [
                self.learning_container_year.common_title_english,
                self.specific_title_english,
            ]))
        return complete_title_english

    @property
    def complete_title_i18n(self):
        complete_title = self.complete_title
        if translation.get_language() == LANGUAGE_CODE_EN:
            complete_title = self.complete_title_english or complete_title
        return complete_title

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
        return self.child_leaf.filter(child_leaf=self).select_related('parent')

    def get_learning_unit_previous_year(self):
        try:
            return self.learning_unit.learningunityear_set.get(academic_year__year=(self.academic_year.year - 1))
        except LearningUnitYear.DoesNotExist:
            return None

    def get_learning_unit_next_year(self):
        try:
            return self.learning_unit.learningunityear_set.get(academic_year__year=(self.academic_year.year + 1))
        except LearningUnitYear.DoesNotExist:
            return None

    @property
    def in_charge(self):
        return self.learning_container_year and self.learning_container_year.in_charge

    @property
    def container_type_verbose(self):
        verbose_type = ''
        if self.learning_container_year:  # FIXME :: remove this 'if' when classes will be remoed from LearningUnitYear
            verbose_type = _(self.learning_container_year.get_container_type_display())

            if self.is_external_of_mobility():
                verbose_type = _('Mobility')

            if self.learning_container_year.container_type in (COURSE, INTERNSHIP) or \
                    self.is_external_with_co_graduation():
                verbose_type += " ({subtype})".format(subtype=self.get_subtype_display())

        return verbose_type

    def is_external_of_mobility(self):
        return self.is_external() and self.externallearningunityear.mobility

    def get_container_type_display(self):
        # FIXME :: Condition to remove when the LearningUnitYear.learning_container_year_id will be null=false
        if not self.learning_container_year:
            return ''
        if self.is_external_of_mobility():
            return _('Mobility')
        return self.learning_container_year.get_container_type_display()

    @property
    def status_verbose(self):
        return _("Active") if self.status else _("Inactive")

    @property
    def internship_subtype_verbose(self):
        if self.learning_container_year and self.learning_container_year.container_type == INTERNSHIP and \
                not self.internship_subtype:
            return _('To complete')
        return self.get_internship_subtype_display()

    @property
    def periodicity_verbose(self):
        if self.periodicity:
            return _(self.periodicity)
        return None

    def find_gt_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gt=self.academic_year.year) \
            .order_by('academic_year__year')

    def is_past(self):
        return self.academic_year.is_past

    def is_full(self):
        return self.subtype == learning_unit_year_subtypes.FULL

    def is_partim(self):
        return self.subtype == learning_unit_year_subtypes.PARTIM

    def is_for_faculty_or_partim(self) -> bool:
        return self.learning_container_year.is_type_for_faculty() or self.is_partim()

    def get_entity(self, entity_type):
        # @TODO: Remove this condition when classes will be removed from learning unit year
        if self.learning_container_year:
            entity = self.learning_container_year.get_entity_from_type(entity_type)
            return entity

    def clean(self):
        learning_unit_years = find_gte_year_acronym(self.academic_year, self.acronym)

        if getattr(self, 'learning_unit', None):
            learning_unit_years = learning_unit_years.exclude(learning_unit=self.learning_unit)

        self.clean_acronym(learning_unit_years)

    def clean_acronym(self, learning_unit_years):
        if self.acronym in learning_unit_years.values_list('acronym', flat=True):
            raise ValidationError({'acronym': _('Existing acronym')})

    @property
    def warnings(self):
        if self._warnings is None:
            self._warnings = []
            self._warnings.extend(self._check_credits_is_integer())
            self._warnings.extend(self._check_partim_parent_credits())
            self._warnings.extend(self._check_internship_subtype())
            self._warnings.extend(self._check_partim_parent_status())
            self._warnings.extend(self._check_partim_parent_periodicity())
            self._warnings.extend(self._check_learning_component_year_warnings())
            self._warnings.extend(self._check_learning_container_year_warnings())
        return self._warnings

    # TODO: Currently, we should warning user that the credits is not an integer
    def _check_credits_is_integer(self):
        warnings = []
        if self.credits and self.credits % 1 != 0:
            warnings.append(_('The credits value should be an integer'))
        return warnings

    def _check_partim_parent_credits(self):
        children = self.get_partims_related()
        return [_('The credits value of the partim %(acronym)s is greater or equal than the credits value of the '
                  'parent learning unit.') % {'acronym': child.acronym}
                for child in children if child.credits and child.credits >= (self.credits or 0)]

    def _check_internship_subtype(self):
        warnings = []
        if getattr(self, 'learning_container_year', None):
            if (self.learning_container_year.container_type == learning_container_year_types.INTERNSHIP and
                    not self.internship_subtype):
                warnings.append(_('It is necessary to indicate the internship subtype.'))
        return warnings

    def _check_partim_parent_status(self):
        warnings = []
        if self.parent:
            if not self.parent.status and self.status:
                warnings.append(_('This partim is active and the parent is inactive'))
        else:
            if self.status is False and find_partims_with_active_status(self).exists():
                warnings.append(_("The parent is inactive and there is at least one partim active"))
        return warnings

    def _check_partim_parent_periodicity(self):
        warnings = []
        if self.parent:
            if self.parent.periodicity in [BIENNIAL_EVEN, BIENNIAL_ODD] and self.periodicity != self.parent.periodicity:
                warnings.append(_("This partim is %(partim_periodicity)s and the parent is %(parent_periodicty)s")
                                % {'partim_periodicity': self.periodicity_verbose,
                                   'parent_periodicty': self.parent.periodicity_verbose})
        else:
            if self.periodicity in [BIENNIAL_EVEN, BIENNIAL_ODD] and \
                    find_partims_with_different_periodicity(self).exists():
                warnings.append(_("The parent is %(parent_periodicty)s and there is at least one partim which is not "
                                  "%(parent_periodicty)s") % {'parent_periodicty': self.periodicity_verbose})
        return warnings

    def _check_learning_component_year_warnings(self):
        _warnings = []
        components_queryset = LearningComponentYear.objects.filter(
            learning_unit_year__learning_container_year=self.learning_container_year
        )
        all_components = components_queryset.order_by('acronym') \
            .select_related('learning_unit_year')
        for learning_component_year in all_components:
            if not self.is_partim() or learning_component_year.learning_unit_year == self:
                _warnings.extend(learning_component_year.warnings)

        return _warnings

    def _check_learning_container_year_warnings(self):
        if not self.is_partim():
            return self.learning_container_year.warnings
        else:
            return get_learning_container_year_warnings(self.learning_container_year, self.id)

    def is_external(self):
        return hasattr(self, "externallearningunityear")

    def is_external_with_co_graduation(self):
        return self.is_external() and self.externallearningunityear.co_graduation

    def is_prerequisite(self):
        return PrerequisiteItem.objects.filter(
            Q(learning_unit=self.learning_unit) | Q(prerequisite__learning_unit_year=self)
        ).exists()

    def has_or_is_prerequisite(self, education_group_year):
        formations = group_element_year.find_learning_unit_roots([education_group_year])[education_group_year.id]
        return PrerequisiteItem.objects.filter(
            Q(prerequisite__learning_unit_year=self, prerequisite__education_group_year__in=formations) |
            Q(prerequisite__education_group_year__in=formations, learning_unit=self.learning_unit)
        ).exists()

    def get_absolute_url(self):
        return reverse('learning_unit', args=[self.pk])


def get_by_id(learning_unit_year_id):
    return LearningUnitYear.objects.select_related('learning_container_year__learning_container') \
        .get(pk=learning_unit_year_id)


def _is_regex(acronym):
    return set(AUTHORIZED_REGEX_CHARS).intersection(set(acronym))


def search(academic_year_id=None, acronym=None, learning_container_year_id=None, learning_unit=None,
           title=None, subtype=None, status=None, container_type=None, tutor=None,
           summary_responsible=None, requirement_entities=None, learning_unit_year_id=None, *args, **kwargs):
    queryset = LearningUnitYear.objects_with_container
    queryset = LearningUnitYearQuerySet.annotate_full_title_class_method(queryset)

    if learning_unit_year_id:
        queryset = queryset.filter(id=learning_unit_year_id)

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

    if requirement_entities:
        queryset = queryset.filter(
            learning_container_year__requirement_entity__entityversion__in=requirement_entities,
        )

    if learning_unit:
        queryset = queryset.filter(learning_unit=learning_unit)

    if title:
        queryset = queryset. \
            filter(Q(specific_title__iregex=title) | Q(learning_container_year__common_title__iregex=title))

    if subtype:
        queryset = queryset.filter(subtype=subtype)

    if status:
        queryset = queryset.filter(status=convert_status_bool(status))

    if container_type:
        queryset = queryset.filter(learning_container_year__container_type=container_type)

    if tutor:
        for name in tutor.split():
            filter_by_first_name = {_build_tutor_filter(name_type='first_name'): name}
            filter_by_last_name = {_build_tutor_filter(name_type='last_name'): name}
            queryset = queryset.filter(Q(**filter_by_first_name) | Q(**filter_by_last_name)).distinct()

    if summary_responsible:
        queryset = find_summary_responsible_by_name(queryset, summary_responsible)

    campus = kwargs.get('campus')
    city = kwargs.get('city')
    country = kwargs.get('country')

    if campus:
        queryset = queryset.filter(campus=campus)
    elif city:
        queryset = queryset.filter(campus__organization__organizationaddress__city=city)
    elif country:
        queryset = queryset.filter(campus__organization__organizationaddress__country=country)

    quadrimester = kwargs.get('quadrimester')
    if quadrimester:
        queryset = queryset.filter(quadrimester=quadrimester)

    return queryset.select_related('learning_container_year', 'academic_year')


def find_summary_responsible_by_name(queryset, name):
    for term in name.split():
        queryset = queryset.filter(
            Q(attribution__tutor__person__first_name__icontains=term) |
            Q(attribution__tutor__person__last_name__icontains=term)
        )

    return queryset.filter(attribution__summary_responsible=True).distinct()


def _build_tutor_filter(name_type):
    return '__'.join(['learningcomponentyear', 'attributionchargenew', 'attribution',
                      'tutor', 'person', name_type, 'iregex'])


def convert_status_bool(status):
    if status in (active_status.ACTIVE, active_status.INACTIVE):
        boolean = status == active_status.ACTIVE
    else:
        boolean = status
    return boolean


def find_gte_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__gte=academic_yr.year,
                                           acronym__iexact=acronym)


def find_lt_year_acronym(academic_yr, acronym):
    return LearningUnitYear.objects.filter(academic_year__year__lt=academic_yr.year,
                                           acronym__iexact=acronym).order_by('academic_year')


def find_partims_with_active_status(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().filter(status=True)


def find_partims_with_different_periodicity(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().exclude(periodicity=a_learning_unit_year.periodicity)


def find_latest_by_learning_unit(a_learning_unit):
    return search(learning_unit=a_learning_unit).order_by('academic_year').last()


def find_lt_learning_unit_year_with_different_acronym(a_learning_unit_yr):
    return LearningUnitYear.objects.filter(learning_unit__id=a_learning_unit_yr.learning_unit.id,
                                           academic_year__year__lt=a_learning_unit_yr.academic_year.year,
                                           proposallearningunit__isnull=True) \
        .order_by('-academic_year') \
        .exclude(acronym__iexact=a_learning_unit_yr.acronym).first()


def find_gt_learning_unit_year_with_different_acronym(a_learning_unit_yr):
    return LearningUnitYear.objects.filter(learning_unit__id=a_learning_unit_yr.learning_unit.id,
                                           academic_year__year__gt=a_learning_unit_yr.academic_year.year,
                                           proposallearningunit__isnull=True) \
        .order_by('academic_year') \
        .exclude(acronym__iexact=a_learning_unit_yr.acronym).first()


def find_learning_unit_years_by_academic_year_tutor_attributions(academic_year, tutor):
    """ In this function, only learning unit year with containers is visible! [no classes] """
    qs = LearningUnitYear.objects_with_container.filter(
        academic_year=academic_year,
        attribution__tutor=tutor,
    ).distinct().order_by('academic_year__year', 'acronym')
    return qs


def toggle_summary_locked(learning_unit_year_id):
    luy = LearningUnitYear.objects.get(pk=learning_unit_year_id)
    luy.summary_locked = not luy.summary_locked
    luy.save()
    return luy


@receiver(post_delete, sender=LearningUnitYear)
def _learningunityear_delete(sender, instance, **kwargs):
    TranslatedText.objects.filter(entity=LEARNING_UNIT_YEAR, reference=instance.id).delete()
