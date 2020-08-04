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

from django.conf import settings
from rest_framework import serializers

from base.api.serializers.campus import CampusDetailSerializer
from base.models.academic_year import AcademicYear
from base.models.education_group_type import EducationGroupType
from base.models.enums import education_group_categories, education_group_types
from education_group.api.serializers import utils
from education_group.api.serializers.education_group_title import EducationGroupTitleSerializer
from education_group.api.serializers.utils import TrainingHyperlinkedIdentityField
from reference.models.language import Language


class TrainingBaseListSerializer(EducationGroupTitleSerializer, serializers.HyperlinkedModelSerializer):
    url = TrainingHyperlinkedIdentityField(read_only=True)
    acronym = serializers.CharField(source='offer.acronym')
    code = serializers.CharField(source='root_group.partial_acronym')
    academic_year = serializers.SlugRelatedField(
        source='offer.academic_year',
        slug_field='year',
        queryset=AcademicYear.objects.all()
    )
    education_group_type = serializers.SlugRelatedField(
        source='offer.education_group_type',
        slug_field='name',
        queryset=EducationGroupType.objects.filter(category=education_group_categories.TRAINING),
    )
    administration_entity = serializers.CharField(source='offer.administration_entity_version.acronym', read_only=True)
    administration_faculty = serializers.SerializerMethodField()
    management_entity = serializers.CharField(source='offer.management_entity_version.acronym', read_only=True)
    management_faculty = serializers.SerializerMethodField()

    # Display human readable value
    education_group_type_text = serializers.CharField(source='offer.education_group_type.get_name_display',
                                                      read_only=True)

    class Meta(EducationGroupTitleSerializer.Meta):
        fields = EducationGroupTitleSerializer.Meta.fields + (
            'url',
            'version_name',
            'acronym',
            'code',
            'education_group_type',
            'education_group_type_text',
            'academic_year',
            'administration_entity',
            'administration_faculty',
            'management_entity',
            'management_faculty',
        )

    @staticmethod
    def get_administration_faculty(obj):
        return utils.get_entity(obj.offer, 'administration')

    @staticmethod
    def get_management_faculty(obj):
        return utils.get_entity(obj.offer, 'management')


class TrainingListSerializer(TrainingBaseListSerializer):
    partial_title = serializers.SerializerMethodField()

    class Meta(TrainingBaseListSerializer.Meta):
        fields = TrainingBaseListSerializer.Meta.fields + (
            'partial_title',
        )

    def get_partial_title(self, version):
        language = self.context.get('language')
        return getattr(
            version.offer,
            'partial_title' + ('_english' if language and language not in settings.LANGUAGE_CODE_FR else '')
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.offer.education_group_type.name not in education_group_types.TrainingType.finality_types():
            data.pop('partial_title')
        return data


class TrainingDetailSerializer(TrainingListSerializer):
    primary_language = serializers.SlugRelatedField(
        source='offer.primary_language',
        slug_field='code',
        queryset=Language.objects.all()
    )
    enrollment_campus = CampusDetailSerializer(source='offer.enrollment_campus')
    main_teaching_campus = CampusDetailSerializer(source='root_group.main_teaching_campus')
    active = serializers.CharField(source='root_group.active')
    web_re_registration = serializers.BooleanField(source='offer.web_re_registration')
    co_graduation_coefficient = serializers.DecimalField(
        source='offer.co_graduation_coefficient',
        max_digits=5,
        decimal_places=2
    )
    co_graduation = serializers.CharField(source='offer.co_graduation')
    internal_comment = serializers.CharField(source='offer.internal_comment')
    rate_code = serializers.CharField(source='offer.rate_code')
    decree_category = serializers.CharField(source='offer.decree_category')
    default_learning_unit_enrollment = serializers.BooleanField(source='offer.default_learning_unit_enrollment')
    weighting = serializers.BooleanField(source='offer.weighting')
    constraint_type = serializers.CharField(source='root_group.constraint_type')
    max_constraint = serializers.IntegerField(source='root_group.max_constraint')
    min_constraint = serializers.IntegerField(source='root_group.min_constraint')
    credits = serializers.IntegerField(source='root_group.credits')
    enrollment_enabled = serializers.BooleanField(source='offer.enrollment_enabled')
    duration_unit = serializers.CharField(source='offer.duration_unit')
    duration = serializers.IntegerField(source='offer.duration')
    keywords = serializers.CharField(source='offer.keywords')
    inter_university_abroad = serializers.BooleanField(source='offer.inter_university_abroad')
    inter_university_belgium = serializers.BooleanField(source='offer.inter_university_belgium')
    inter_university_french_community = serializers.BooleanField(source='offer.inter_university_french_community')
    inter_organization_information = serializers.CharField(source='offer.inter_organization_information')
    diploma_printing_title = serializers.CharField(source='offer.diploma_printing_title')
    diploma_printing_orientation = serializers.CharField(source='offer.diploma_printing_orientation')
    joint_diploma = serializers.BooleanField(source='offer.joint_diploma')
    professional_title = serializers.CharField(source='offer.professional_title')
    other_campus_activities = serializers.CharField(source='offer.other_campus_activities')
    other_language_activities = serializers.CharField(source='offer.other_language_activities')
    english_activities = serializers.CharField(source='offer.english_activities')
    schedule_type = serializers.CharField(source='offer.schedule_type')
    internship = serializers.CharField(source='offer.internship')
    dissertation = serializers.BooleanField(source='offer.dissertation')
    university_certificate = serializers.BooleanField(source='offer.university_certificate')
    academic_type = serializers.CharField(source='offer.academic_type')
    funding_direction_cud = serializers.CharField(source='offer.funding_direction_cud')
    funding_cud = serializers.BooleanField(source='offer.funding_cud')
    funding_direction = serializers.CharField(source='offer.funding_direction')
    funding = serializers.BooleanField(source='offer.internship')
    admission_exam = serializers.BooleanField(source='offer.admission_exam')
    partial_deliberation = serializers.BooleanField(source='offer.partial_deliberation')

    # Display human readable value
    academic_type_text = serializers.CharField(source='offer.get_academic_type_display', read_only=True)
    internship_text = serializers.CharField(source='offer.get_internship_display', read_only=True)
    schedule_type_text = serializers.CharField(source='offer.get_schedule_type_display', read_only=True)
    english_activities_text = serializers.CharField(source='offer.get_english_activities_display', read_only=True)
    other_language_activities_text = serializers.CharField(
        source='offer.get_other_language_activities_display',
        read_only=True
    )
    other_campus_activities_text = serializers.CharField(source='offer.get_other_campus_activities_display',
                                                         read_only=True)
    diploma_printing_orientation_text = serializers.CharField(
        source='offer.get_diploma_printing_orientation_display',
        read_only=True,
    )
    language_association_text = serializers.CharField(source='offer.get_language_association_display', read_only=True)
    duration_unit_text = serializers.CharField(source='offer.get_duration_unit_display', read_only=True)
    constraint_type_text = serializers.CharField(source='root_group.get_constraint_type_display', read_only=True)
    decree_category_text = serializers.CharField(source='offer.get_decree_category_display', read_only=True)
    rate_code_text = serializers.CharField(source='offer.get_rate_code_display', read_only=True)
    active_text = serializers.CharField(source='offer.get_active_display', read_only=True)
    remark = serializers.SerializerMethodField()
    domain_name = serializers.CharField(read_only=True)
    domain_code = serializers.CharField(read_only=True)
    ares_study = serializers.IntegerField(source='offer.hops.ares_study', read_only=True)
    ares_graca = serializers.IntegerField(source='offer.hops.ares_graca', read_only=True)
    ares_ability = serializers.IntegerField(source='offer.hops.ares_ability', read_only=True)

    class Meta(TrainingListSerializer.Meta):
        fields = TrainingListSerializer.Meta.fields + (
            'partial_deliberation',
            'admission_exam',
            'funding',
            'funding_direction',
            'funding_cud',
            'funding_direction_cud',
            'academic_type',
            'academic_type_text',
            'university_certificate',
            'dissertation',
            'internship',
            'internship_text',
            'schedule_type',
            'schedule_type_text',
            'english_activities',
            'english_activities_text',
            'other_language_activities',
            'other_language_activities_text',
            'other_campus_activities',
            'other_campus_activities_text',
            'professional_title',
            'joint_diploma',
            'diploma_printing_orientation',
            'diploma_printing_orientation_text',
            'diploma_printing_title',
            'inter_organization_information',
            'inter_university_french_community',
            'inter_university_belgium',
            'inter_university_abroad',
            'primary_language',
            'keywords',
            'duration',
            'duration_unit',
            'duration_unit_text',
            'language_association_text',
            'enrollment_enabled',
            'credits',
            'remark',
            'min_constraint',
            'max_constraint',
            'constraint_type',
            'constraint_type_text',
            'weighting',
            'default_learning_unit_enrollment',
            'decree_category',
            'decree_category_text',
            'rate_code',
            'rate_code_text',
            'internal_comment',
            'co_graduation',
            'co_graduation_coefficient',
            'web_re_registration',
            'active',
            'active_text',
            'enrollment_campus',
            'main_teaching_campus',
            'domain_code',
            'domain_name',
            'ares_study',
            'ares_graca',
            'ares_ability'
        )

    def get_remark(self, version):
        language = self.context.get('language')
        return getattr(
            version.root_group,
            'remark_' + ('en' if language and language not in settings.LANGUAGE_CODE_FR else 'fr')
        )
