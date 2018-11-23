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

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, ngettext
from reversion.admin import VersionAdmin

from base.models import entity_container_year as mdl_entity_container_year
from base.models.academic_year import compute_max_academic_year_adjournment, AcademicYear, \
    MAX_ACADEMIC_YEAR_FACULTY, starting_academic_year
from base.models.enums import active_status, learning_container_year_types
from base.models.enums import learning_unit_year_subtypes, internship_subtypes, \
    learning_unit_year_session, entity_container_year_link_type, quadrimesters, attribution_procedure
from base.models.enums.learning_container_year_types import COURSE, INTERNSHIP
from base.models.enums.learning_unit_year_periodicity import PERIODICITY_TYPES, ANNUAL, BIENNIAL_EVEN, BIENNIAL_ODD
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit import LEARNING_UNIT_ACRONYM_REGEX_ALL, REGEX_BY_SUBTYPE
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin

AUTHORIZED_REGEX_CHARS = "$*+.^"
REGEX_ACRONYM_CHARSET = "[A-Z0-9" + AUTHORIZED_REGEX_CHARS + "]+"
MINIMUM_CREDITS = 0.0
MAXIMUM_CREDITS = 500


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
    search_fields = ['acronym', 'structure__acronym', 'external_id']
    actions = [
        'resend_messages_to_queue',
        'apply_learning_unit_year_postponement'
    ]

    def apply_learning_unit_year_postponement(self, request, queryset):
        # Potential circular imports
        from base.business.learning_units.automatic_postponement import LearningUnitAutomaticPostponement
        from base.views.common import display_success_messages, display_error_messages

        result, errors = LearningUnitAutomaticPostponement(queryset.filter(learning_container_year__isnull=False))
        count = len(result)
        display_success_messages(
            request, ngettext(
                '%(count)d learning unit has been postponed with success',
                '%(count)d learning units have been postponed with success', count
            ) % {'count': count}
        )
        if errors:
            display_error_messages(request, "{} : {}".format(
                _("The following learning units ended with error"),
                ", ".join([str(error) for error in errors])
            ))

    apply_learning_unit_year_postponement.short_description = _("Apply postponement on learning unit year")


class LearningUnitYearWithContainerManager(models.Manager):
    def get_queryset(self):
        # FIXME For the moment, the learning_unit_year without container must be hide !
        return super().get_queryset().filter(learning_container_year__isnull=False)


class ExtraManagerLearningUnitYear(models.Model):
    # This class ensure that the default manager (from serializable model) is not override by this manager
    objects_with_container = LearningUnitYearWithContainerManager()

    class Meta:
        abstract = True


class LearningUnitYear(SerializableModel, ExtraManagerLearningUnitYear):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    academic_year = models.ForeignKey(AcademicYear, verbose_name=_('Academic year'),
                                      validators=[academic_year_validator])
    learning_unit = models.ForeignKey('LearningUnit')

    learning_container_year = models.ForeignKey('LearningContainerYear', null=True)

    learning_component_years = models.ManyToManyField(
        LearningComponentYear,
        through="base.LearningUnitComponent",
        verbose_name=_("Components"),
    )

    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True, verbose_name=_('Code'),
                               validators=[RegexValidator(LEARNING_UNIT_ACRONYM_REGEX_ALL)])
    specific_title = models.CharField(max_length=255, blank=True, null=True,
                                      verbose_name=_('English title proper'))
    specific_title_english = models.CharField(max_length=250, blank=True, null=True,
                                              verbose_name=_('English title proper'))
    subtype = models.CharField(max_length=50, choices=learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
                               default=learning_unit_year_subtypes.FULL)
    credits = models.DecimalField(null=True, max_digits=5, decimal_places=2,
                                  validators=[MinValueValidator(MINIMUM_CREDITS), MaxValueValidator(MAXIMUM_CREDITS)],
                                  verbose_name=_('Credits'))
    decimal_scores = models.BooleanField(default=False)
    structure = models.ForeignKey('Structure', blank=True, null=True)
    internship_subtype = models.CharField(max_length=250, blank=True, null=True,
                                          verbose_name=_('Internship subtype'),
                                          choices=internship_subtypes.INTERNSHIP_SUBTYPES)
    status = models.BooleanField(default=False, verbose_name=_('Active'))
    session = models.CharField(max_length=50, blank=True, null=True,
                               choices=learning_unit_year_session.LEARNING_UNIT_YEAR_SESSION,
                               verbose_name=_('Session derogation'))
    quadrimester = models.CharField(max_length=9, blank=True, null=True, verbose_name=_('Quadrimester'),
                                    choices=quadrimesters.LEARNING_UNIT_YEAR_QUADRIMESTERS)

    attribution_procedure = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name=_('Procedure'),
        choices=attribution_procedure.ATTRIBUTION_PROCEDURES
    )

    summary_locked = models.BooleanField(default=False, verbose_name=_("blocked update for tutor"))

    professional_integration = models.BooleanField(default=False, verbose_name=_('professional integration'))

    campus = models.ForeignKey('Campus', null=True, verbose_name=_("Learning location"))

    language = models.ForeignKey('reference.Language', null=True, verbose_name=_('Language'))

    periodicity = models.CharField(max_length=20, choices=PERIODICITY_TYPES, default=ANNUAL,
                                   verbose_name=_('Periodicity'))
    _warnings = None

    class Meta:
        unique_together = (('learning_unit', 'academic_year'), ('acronym', 'academic_year'))

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

    @property
    def same_container_learning_unit_years(self):
        return LearningUnitYear.objects.filter(
            learning_container_year=self.learning_container_year
        ).order_by('acronym')

    @cached_property
    def allocation_entity(self):
        return self.get_entity(entity_container_year_link_type.ALLOCATION_ENTITY)

    @cached_property
    def requirement_entity(self):
        return self.get_entity(entity_container_year_link_type.REQUIREMENT_ENTITY)

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
        container_type = ''
        if self.learning_container_year:
            container_type = _(self.learning_container_year.get_container_type_display())

            if self.learning_container_year.container_type in (COURSE, INTERNSHIP):
                container_type += " ({subtype})".format(subtype=self.get_subtype_display())

        return container_type

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
    def get_previous_acronym(self):
        return find_lt_learning_unit_year_with_different_acronym(self)

    @property
    def periodicity_verbose(self):
        if self.periodicity:
            return _(self.periodicity)
        return None

    def find_gte_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gte=self.academic_year.year) \
            .order_by('academic_year__year')

    def find_gt_learning_units_year(self):
        return LearningUnitYear.objects.filter(learning_unit=self.learning_unit,
                                               academic_year__year__gt=self.academic_year.year) \
            .order_by('academic_year__year')

    def is_past(self):
        return self.academic_year.is_past()

    # FIXME move this method to business/perm file
    def can_update_by_faculty_manager(self):
        if not self.learning_container_year:
            return False

        starting_year = starting_academic_year().year
        year = self.academic_year.year
        return starting_year <= year <= starting_year + MAX_ACADEMIC_YEAR_FACULTY

    def is_full(self):
        return self.subtype == learning_unit_year_subtypes.FULL

    def is_partim(self):
        return self.subtype == learning_unit_year_subtypes.PARTIM

    def get_entity(self, entity_type):
        entity = None
        # @TODO: Remove this condition when classes will be removed from learning unit year
        if self.learning_container_year:
            entity_container_yr = mdl_entity_container_year.search(
                link_type=entity_type,
                learning_container_year=self.learning_container_year,
            ).get()
            entity = entity_container_yr.entity if entity_container_yr else None
        return entity

    def clean(self):
        learning_unit_years = find_gte_year_acronym(self.academic_year, self.acronym)

        if getattr(self, 'learning_unit', None):
            learning_unit_years = learning_unit_years.exclude(learning_unit=self.learning_unit)

        self.clean_acronym(learning_unit_years)

    def clean_acronym(self, learning_unit_years):
        if self.acronym in learning_unit_years.values_list('acronym', flat=True):
            raise ValidationError({'acronym': _('Existing acronym')})
        if not re.match(REGEX_BY_SUBTYPE[self.subtype], self.acronym):
            raise ValidationError({'acronym': _('Invalid code')})

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
            self._warnings.extend(self._check_entity_container_year_warnings())
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
                for child in children if child.credits and child.credits >= self.credits]

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
        components_queryset = self.learning_container_year.learningcomponentyear_set
        all_components = components_queryset.all().order_by('learningunitcomponent__learning_unit_year__acronym')
        for learning_component_year in all_components:
            _warnings.extend(learning_component_year.warnings)

        return _warnings

    def _check_learning_container_year_warnings(self):
        return self.learning_container_year.warnings

    def _check_entity_container_year_warnings(self):
        _warnings = []
        entity_container_years = mdl_entity_container_year.find_by_learning_container_year(self.learning_container_year)
        for entity_container_year in entity_container_years:
            _warnings.extend(entity_container_year.warnings)
        return _warnings

    def is_external(self):
        return hasattr(self, "externallearningunityear")


def get_by_id(learning_unit_year_id):
    return LearningUnitYear.objects.select_related('learning_container_year__learning_container') \
        .get(pk=learning_unit_year_id)


def find_by_acronym(acronym):
    return LearningUnitYear.objects.filter(acronym=acronym).select_related('learning_container_year')


def _is_regex(acronym):
    return set(AUTHORIZED_REGEX_CHARS).intersection(set(acronym))


def search(academic_year_id=None, acronym=None, learning_container_year_id=None, learning_unit=None,
           title=None, subtype=None, status=None, container_type=None, tutor=None,
           summary_responsible=None, requirement_entities=None, learning_unit_year_id=None, *args, **kwargs):
    queryset = LearningUnitYear.objects_with_container

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
            learning_container_year__entitycontaineryear__entity__entityversion__in=requirement_entities,
            learning_container_year__entitycontaineryear__type=entity_container_year_link_type.REQUIREMENT_ENTITY)

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

    return queryset.select_related('learning_container_year', 'academic_year')


def find_summary_responsible_by_name(queryset, name):
    for term in name.split():
        queryset = queryset.filter(
            Q(attribution__tutor__person__first_name__icontains=term) |
            Q(attribution__tutor__person__last_name__icontains=term)
        )

    return queryset.filter(attribution__summary_responsible=True).distinct()


def _build_tutor_filter(name_type):
    return '__'.join(['learningunitcomponent', 'learning_component_year', 'attributionchargenew', 'attribution',
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


def check_if_acronym_regex_is_valid(acronym):
    return isinstance(acronym, str) and \
           not acronym.startswith('*') and \
           not acronym.startswith('+') and \
           re.fullmatch(REGEX_ACRONYM_CHARSET, acronym.upper()) is not None


def find_max_credits_of_related_partims(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().aggregate(max_credits=models.Max("credits"))["max_credits"]


def find_partims_with_active_status(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().filter(status=True)


def find_partims_with_different_periodicity(a_learning_unit_year):
    return a_learning_unit_year.get_partims_related().exclude(periodicity=a_learning_unit_year.periodicity)


def find_by_learning_unit(a_learning_unit):
    return search(learning_unit=a_learning_unit)


def find_by_entities(entities):
    return LearningUnitYear.objects.filter(learning_container_year__entitycontaineryear__entity__in=entities)


def find_latest_by_learning_unit(a_learning_unit):
    return search(learning_unit=a_learning_unit).order_by('academic_year').last()


def find_lt_learning_unit_year_with_different_acronym(a_learning_unit_yr):
    return LearningUnitYear.objects.filter(learning_unit__id=a_learning_unit_yr.learning_unit.id,
                                           academic_year__year__lt=a_learning_unit_yr.academic_year.year,
                                           proposallearningunit__isnull=True) \
        .order_by('-academic_year') \
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
