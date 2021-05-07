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
from ckeditor.fields import RichTextField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, When, Q, Value, CharField
from django.db.models.functions import Concat
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.models import entity_version
from base.models.campus import Campus
from base.models.entity import Entity
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType, MiniTrainingType
from education_group.models.enums.constraint_type import ConstraintTypes
from osis_common.models.osis_model_admin import OsisModelAdmin


def fill_from_past_year(modeladmin, request, queryset):
    from program_management.ddd.command import FillProgramTreeContentFromLastYearCommand
    from program_management.ddd.service.write import bulk_fill_program_tree_content_service_from_past_year
    cmds = []
    qs = queryset.select_related("academic_year")
    for obj in qs:
        cmd = FillProgramTreeContentFromLastYearCommand(
            to_year=obj.academic_year.year,
            to_code=obj.partial_acronym
        )
        cmds.append(cmd)
    result = bulk_fill_program_tree_content_service_from_past_year.bulk_fill_program_tree_content_from_last_year(cmds)
    modeladmin.message_user(request, "{} programs have been filled".format(len(result)))


fill_from_past_year.short_description = _("Fill program tree content from last year")


class GroupYearManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'group'
        )


class GroupYearVersionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(educationgroupversion__isnull=False).select_related(
            'group', 'educationgroupversion'
        )


class GroupYearQuerySet(models.QuerySet):
    def annotate_full_titles(self):
        return self.annotate(
            full_title_fr=Case(
                When(
                    Q(education_group_type__category__in=Categories.training_categories())
                    & Q(educationgroupversion__title_fr__isnull=False) & ~Q(educationgroupversion__title_fr=''),
                    then=Concat(
                        'educationgroupversion__offer__title',
                        Value(' ['),
                        'educationgroupversion__title_fr',
                        Value(']')
                    )
                ),
                When(
                    Q(education_group_type__category__in=Categories.training_categories()),
                    then='educationgroupversion__offer__title'
                ),
                default='title_fr',
                output_field=CharField(),
            ),
            full_title_en=Case(
                When(
                    Q(education_group_type__category__in=Categories.training_categories())
                    & Q(educationgroupversion__title_en__isnull=False) & ~Q(educationgroupversion__title_en=''),
                    then=Concat(
                        'educationgroupversion__offer__title_english',
                        Value(' ['),
                        'educationgroupversion__title_en',
                        Value(']')
                    )
                ),
                When(
                    Q(education_group_type__category__in=Categories.training_categories()),
                    then='educationgroupversion__offer__title_english'
                ),
                default='title_en',
                output_field=CharField(),
            )
        )


class GroupYearAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('acronym', 'partial_acronym', 'title_fr', 'group', 'education_group_type', 'academic_year',
                    'changed')
    list_filter = ('education_group_type', 'academic_year')
    search_fields = ['acronym', 'partial_acronym', 'title_fr', 'group__pk', 'id']
    raw_id_fields = (
        'education_group_type', 'academic_year', 'group', 'main_teaching_campus',
    )
    actions = [fill_from_past_year]


class GroupYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    partial_acronym = models.CharField(
        max_length=15,
        db_index=True,
        null=True,
        verbose_name=_("code"),
    )

    acronym = models.CharField(
        max_length=40,
        db_index=True,
        verbose_name=_("Acronym/Short title"),
    )
    education_group_type = models.ForeignKey(
        'base.EducationGroupType',
        verbose_name=_("Type of training"),
        on_delete=models.CASCADE,
        db_index=True
    )
    credits = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("credits"),
    )
    constraint_type = models.CharField(
        max_length=20,
        choices=ConstraintTypes.choices(),
        default=None,
        blank=True,
        null=True,
        verbose_name=_("type of constraint")
    )
    min_constraint = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("minimum constraint"),
        validators=[MinValueValidator(1)]
    )
    max_constraint = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("maximum constraint"),
        validators=[MinValueValidator(1)]
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE
    )

    title_fr = models.CharField(
        max_length=255,
        verbose_name=_("Title in French")
    )

    title_en = models.CharField(
        max_length=240,
        blank=True,
        default="",
        verbose_name=_("Title in English")
    )
    remark_fr = RichTextField(
        blank=True,
        default="",
        verbose_name=_("remark")
    )
    remark_en = RichTextField(
        blank=True,
        default="",
        verbose_name=_("remark in english")
    )

    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('Academic year'),
        on_delete=models.PROTECT
    )

    management_entity = models.ForeignKey(
        Entity,
        verbose_name=_("Management entity"),
        null=True,
        related_name="group_management_entity",
        on_delete=models.PROTECT
    )

    main_teaching_campus = models.ForeignKey(
        Campus,
        blank=True,
        null=True,
        related_name='teaching_campus',
        verbose_name=_("Learning location"),
        on_delete=models.PROTECT
    )

    objects = GroupYearManager.from_queryset(GroupYearQuerySet)()
    objects_version = GroupYearVersionManager.from_queryset(GroupYearQuerySet)()

    class Meta:
        unique_together = ("partial_acronym", "academic_year")
        index_together = [
            ("partial_acronym", "academic_year"),
        ]

    def __str__(self):
        return "{} ({})".format(self.acronym,
                                self.academic_year)

    def save(self, *args, **kwargs):
        if self.academic_year.year < self.group.start_year.year:
            raise AttributeError(
                _('Please enter an academic year greater or equal to group start year.')
            )
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        result = super().delete(using, keep_parents)

        has_group_anymore_children = self.group.groupyear_set.all().exists()
        if not has_group_anymore_children:
            result = self.group.delete()
        return result

    def get_full_title_fr(self):
        if self.education_group_type.category in Categories.training_categories():
            full_title_fr = self.educationgroupversion.offer.title
            if self.educationgroupversion.title_fr:
                full_title_fr += "[ " + self.educationgroupversion.title_fr + " ]"
            return full_title_fr
        return self.title_fr

    def get_full_title_en(self):
        if self.education_group_type.category in Categories.training_categories():
            full_title_en = self.educationgroupversion.offer.title_english
            if self.educationgroupversion.title_en:
                full_title_en += "[ " + self.educationgroupversion.title_en + " ]"
            return full_title_en
        return self.title_fr

    @property
    def is_minor_major_option_list_choice(self):
        return self.education_group_type.name in GroupType.minor_major_option_list_choice()

    @property
    def is_mini_training(self):
        return self.education_group_type.name in MiniTrainingType.get_names()

    @cached_property
    def management_entity_version(self):
        return entity_version.find_entity_version_according_academic_year(
            self.management_entity, self.academic_year
        )
