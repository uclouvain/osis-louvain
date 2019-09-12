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
from gettext import ngettext

from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError
from django.db.models import Max, Subquery, OuterRef, Exists, Prefetch
from django.utils.translation import ugettext_lazy as _
from reversion.admin import VersionAdmin

from base.business.learning_unit import CMS_LABEL_PEDAGOGY
from base.models.academic_year import AcademicYear, starting_academic_year
from base.models.enums.learning_container_year_types import EXTERNAL
from base.models.enums.learning_unit_year_subtypes import PARTIM, FULL
from base.models import learning_unit_year
from base.models import teaching_material
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from osis_common.models.serializable_model import SerializableModel, \
    SerializableModelAdmin

LEARNING_UNIT_ACRONYM_REGEX_MODEL = "^[BEGLMTWX][A-Z]{2,4}\d{4}"
LEARNING_UNIT_ACRONYM_REGEX_BASE = "^[BELMWX][A-Z]{2,4}\d{4}"
LEARNING_UNIT_ACRONYM_REGEX_EXTERNAL = "^[EGLMTW][A-Z]{2,4}\d{4}$"
LETTER_OR_DIGIT = "[A-Z0-9]"
STRING_END = "$"
LEARNING_UNIT_ACRONYM_REGEX_ALL = LEARNING_UNIT_ACRONYM_REGEX_BASE + LETTER_OR_DIGIT + "{0,1}" + STRING_END
LEARNING_UNIT_ACRONYM_REGEX_FULL = LEARNING_UNIT_ACRONYM_REGEX_BASE + STRING_END
LEARNING_UNIT_ACRONYM_REGEX_PARTIM = LEARNING_UNIT_ACRONYM_REGEX_BASE + LETTER_OR_DIGIT + STRING_END

REGEX_BY_SUBTYPE = {
    PARTIM: LEARNING_UNIT_ACRONYM_REGEX_PARTIM,
    FULL: LEARNING_UNIT_ACRONYM_REGEX_FULL,
    EXTERNAL: LEARNING_UNIT_ACRONYM_REGEX_EXTERNAL
}


class LearningUnitAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('learning_container', 'acronym', 'title', 'start_year', 'end_year', 'changed')
    search_fields = ['learningunityear__acronym', 'learningunityear__specific_title', 'learning_container__external_id']
    list_filter = ('start_year',)

    actions = [
        'apply_learning_unit_year_postponement',
        'apply_pedagogy_informations_postponement'
    ]

    def apply_learning_unit_year_postponement(self, request, queryset):
        # Potential circular imports
        from base.business.learning_units.automatic_postponement import LearningUnitAutomaticPostponementToN6
        from base.views.common import display_success_messages, display_error_messages

        result, errors = LearningUnitAutomaticPostponementToN6(queryset).postpone()
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

    def apply_pedagogy_informations_postponement(self, request, queryset):
        pedagogy_information_postponement(queryset)
        teaching_material_postponement(queryset)


    apply_pedagogy_informations_postponement.short_description = _("Apply postponement on learning unit year "
                                                                   "pedagogy informations")


class LearningUnit(SerializableModel):
    existing_proposal_in_epc = models.BooleanField(default=False)
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    learning_container = models.ForeignKey('LearningContainer', blank=True, null=True, on_delete=models.CASCADE)
    changed = models.DateTimeField(null=True, auto_now=True)
    start_year = models.IntegerField(_('Starting year'))
    end_year = models.IntegerField(blank=True, null=True, verbose_name=_('End year'))

    faculty_remark = models.TextField(blank=True, null=True, verbose_name=_('Faculty remark'))

    other_remark = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Other remark')
    )

    def __str__(self):
        return self.acronym

    def save(self, *args, **kwargs):
        if self.end_year and self.end_year < self.start_year:
            raise AttributeError("Start date should be before the end date")
        super(LearningUnit, self).save(*args, **kwargs)

    @property
    def acronym(self):
        try:
            return self.most_recent_learning_unit_year().acronym
        except ObjectDoesNotExist:
            return str(self.id)

    @property
    def title(self):
        return self.most_recent_learning_unit_year().specific_title

    def delete(self, *args, **kwargs):
        if self.start_year < 2015:
            raise IntegrityError(_('Prohibition to delete a learning unit before 2015.'))
        return super().delete(*args, **kwargs)

    def is_past(self):
        return self.end_year and starting_academic_year().year > self.end_year

    def most_recent_learning_unit_year(self):
        return self.learningunityear_set.latest('academic_year__year')

    class Meta:
        permissions = (
            ("can_access_learningunit", "Can access learning unit"),
            ("can_edit_learningunit_date", "Can edit learning unit date"),
            ("can_edit_learningunit", "Can edit learning unit"),
            ("can_edit_learningunit_pedagogy", "Can edit learning unit pedagogy"),
            ("can_edit_learningunit_specification", "Can edit learning unit specification"),
            ("can_delete_learningunit", "Can delete learning unit"),
            ("can_propose_learningunit", "Can propose learning unit "),
            ("can_create_learningunit", "Can create learning unit"),
            ("can_consolidate_learningunit_proposal", "Can consolidate learning unit proposal"),
        )
        verbose_name = _("Learning unit")

    @property
    def parent(self):
        # TODO :: rename "parent" into "learning_unit_full"
        # TODO The subtype must move in learning_unit model !
        luy = self.learningunityear_set.last()
        if luy and luy.subtype == PARTIM:
            return LearningUnit.objects.filter(
                learningunityear__subtype=FULL, learning_container=self.learning_container
            ).last()
        return None

    @property
    def children(self):
        # TODO :: rename "children" into "partims"
        # TODO The subtype must move in learning_unit model !
        luy = self.learningunityear_set.last()
        if luy and luy.subtype == FULL:
            return LearningUnit.objects.filter(
                learningunityear__subtype=PARTIM, learning_container=self.learning_container
            )
        return []

    @property
    def max_end_year(self):
        """ Compute the maximal possible end_year value when the end_year is None """
        if self.end_year:
            return self.end_year

        return AcademicYear.objects.filter(learningunityear__learning_unit=self).aggregate(Max('year'))['year__max']


def get_by_acronym_with_highest_academic_year(acronym):
    return LearningUnit.objects.filter(
        learningunityear__acronym=acronym
    ).order_by(
        'learningunityear__academic_year__year'
    ).last()


def pedagogy_information_postponement(queryset):
    ac_year = starting_academic_year()
    qs = queryset.prefetch_related(
        Prefetch(
            "learningunityear_set",
            queryset=learning_unit_year.LearningUnitYear.objects.filter(
                academic_year__year__gte=ac_year.year
            ).order_by("academic_year__year"),
            to_attr="luys"
        ),
    )
    for lu in qs:
        luy = lu.luys[0]
        translated_text_qs = TranslatedText.objects.filter(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=luy.id,
            text_label__label__in=CMS_LABEL_PEDAGOGY
        )
        for tt in translated_text_qs:
            TranslatedText.objects.get_or_create(
                entity=entity_name.LEARNING_UNIT_YEAR,
                reference=lu.luys[1].id,
                text_label=tt.text_label,
                language=tt.language,
                defaults={"text": tt.text}
            )

        luy = lu.luys[1]
        translated_text_qs = TranslatedText.objects.filter(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=luy.id
        )
        for tt in translated_text_qs:
            for other_luy in lu.luys[2:]:
                TranslatedText.objects.update_or_create(
                    entity=entity_name.LEARNING_UNIT_YEAR,
                    reference=other_luy.id,
                    text_label=tt.text_label,
                    language=tt.language,
                    defaults={"text": tt.text}
                )

def teaching_material_postponement(queryset):
    ac_year = starting_academic_year()
    qs = queryset.prefetch_related(
        Prefetch(
            "learningunityear_set",
            queryset=learning_unit_year.LearningUnitYear.objects.filter(
                academic_year__year__gte=ac_year.year
            ).prefetch_related(
                Prefetch(
                    "teachingmaterial_set",
                    to_attr="materials"
                )
            ).order_by(
                "academic_year__year"
            ),
            to_attr="luys"
        ),
    )

    for lu in qs:
        luy = lu.luys[0]
        next_luy = lu.luys[1]
        if len(next_luy.materials) == 0:
            teaching_material.postpone_teaching_materials(luy)
        else:
            teaching_material.postpone_teaching_materials(next_luy)

