##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, List

from django.db.models import Subquery, OuterRef, Prefetch, QuerySet

from base.models import entity_version
from base.models.academic_year import AcademicYear as AcademicYearModelDb
from base.models.campus import Campus as CampusModelDb
from base.models.certificate_aim import CertificateAim as CertificateAimModelDb
from base.models.education_group import EducationGroup as EducationGroupModelDb
from base.models.education_group_certificate_aim \
    import EducationGroupCertificateAim as EducationGroupCertificateAimModelDb
from base.models.education_group_organization import EducationGroupOrganization as EducationGroupOrganizationModelDb
from base.models.education_group_type import EducationGroupType as EducationGroupTypeModelDb
from base.models.education_group_year import EducationGroupYear as EducationGroupYearModelDb, EducationGroupYear
from base.models.education_group_year_domain import EducationGroupYearDomain as EducationGroupYearDomainModelDb
from base.models.enums.active_status import ActiveStatusEnum
from base.models.hops import Hops as HopsModelDb
from education_group.ddd.domain.training import TrainingIdentityThroughYears
from reference.models.language import Language as LanguageModelDb
from reference.models.domain import Domain as DomainModelDb
from reference.models.domain_isced import DomainIsced as DomainIscedModelDb
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.funding_codes import FundingCodes
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from base.models.organization_address import OrganizationAddress
from education_group.ddd.business_types import *
from education_group.ddd.domain import training, exception
from education_group.ddd.domain._academic_partner import AcademicPartner, AcademicPartnerIdentity
from education_group.ddd.domain._address import Address
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._co_graduation import CoGraduation
from education_group.ddd.domain._co_organization import Coorganization, CoorganizationIdentity
from education_group.ddd.domain._diploma import Diploma, DiplomaAim, DiplomaAimIdentity
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain._funding import Funding
from education_group.ddd.domain._hops import HOPS
from education_group.ddd.domain._isced_domain import IscedDomain, IscedDomainIdentity
from education_group.ddd.domain._language import Language
from education_group.ddd.domain._study_domain import StudyDomain, StudyDomainIdentity
from education_group.ddd.domain._titles import Titles
from education_group.ddd.domain.exception import TrainingNotFoundException
from osis_common.ddd import interface


class TrainingRepository(interface.AbstractRepository):
    @classmethod
    def create(cls, training: 'Training', **_) -> 'TrainingIdentity':
        education_group_db_obj = _save_education_group(training)
        education_group_year_db_obj = _save_education_group_year(training, education_group_db_obj)
        _save_secondary_domains(training, education_group_year_db_obj)
        _save_hops(training, education_group_year_db_obj)
        _save_certificate_aims(training, education_group_year_db_obj)
        return training.entity_id

    @classmethod
    def update(cls, entity: 'Training', **_) -> 'TrainingIdentity':
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'TrainingIdentity') -> 'Training':
        qs = _get_queryset_to_fetch_data_for_training(entity_id)

        try:
            education_group_year_db = qs.get()
        except EducationGroupYearModelDb.DoesNotExist:
            raise exception.TrainingNotFoundException

        return _convert_education_group_year_to_training(entity_id, education_group_year_db)

    @classmethod
    def search(cls, entity_ids: Optional[List['TrainingIdentity']] = None, **kwargs) -> List['Training']:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'TrainingIdentity', **_) -> None:
        EducationGroupYear.objects.filter(
            acronym=entity_id.acronym,
            academic_year__year=entity_id.year
        ).delete()


def _convert_education_group_year_to_training(
        entity_id: 'TrainingIdentity',
        obj: EducationGroupYearModelDb
) -> 'Training':
    secondary_domains = __convert_study_domains_from_db(obj)

    coorganizations = __convert_coorganizations_from_db(entity_id, obj)

    certificate_aims = __convert_diploma_aims_from_db(obj)

    return training.Training(
        entity_identity=entity_id,
        entity_id=entity_id,
        identity_through_years=TrainingIdentityThroughYears(uuid=obj.education_group_id),
        type=TrainingType[obj.education_group_type.name],
        credits=obj.credits,
        schedule_type=ScheduleTypeEnum[obj.schedule_type],
        duration=obj.duration,
        start_year=obj.education_group.start_year.year,
        titles=Titles(
            title_fr=obj.title,
            partial_title_fr=obj.partial_title,
            title_en=obj.title_english,
            partial_title_en=obj.partial_title_english,
        ),
        status=ActiveStatusEnum[obj.active],
        keywords=obj.keywords,
        internship_presence=InternshipPresence[obj.internship] if obj.internship else None,
        is_enrollment_enabled=obj.enrollment_enabled,
        has_online_re_registration=obj.web_re_registration,
        has_partial_deliberation=obj.partial_deliberation,
        has_admission_exam=obj.admission_exam,
        has_dissertation=obj.dissertation,
        produce_university_certificate=obj.university_certificate,
        decree_category=DecreeCategories[obj.decree_category] if obj.decree_category else None,
        rate_code=RateCode[obj.rate_code] if obj.rate_code else None,
        main_language=Language(
            name=obj.primary_language.name,
        ),
        english_activities=ActivityPresence[obj.english_activities] if obj.english_activities else None,
        other_language_activities=ActivityPresence[
            obj.other_language_activities] if obj.other_language_activities else None,
        internal_comment=obj.internal_comment,
        main_domain=StudyDomain(
            entity_id=StudyDomainIdentity(
                decree_name=obj.main_domain.decree.name,
                code=obj.main_domain.code,
            ),
            domain_name=obj.main_domain.name,
        ) if obj.main_domain else None,
        secondary_domains=secondary_domains,
        isced_domain=IscedDomain(
            entity_id=IscedDomainIdentity(code=obj.isced_domain.code),
            title_fr=obj.isced_domain.title_fr,
            title_en=obj.isced_domain.title_en,
        ) if obj.isced_domain else None,
        management_entity=EntityValueObject(
            acronym=obj.management_entity.most_recent_acronym,
        ),
        administration_entity=EntityValueObject(
            acronym=obj.administration_entity.most_recent_acronym,
        ),
        end_year=obj.education_group.end_year.year if obj.education_group.end_year else None,
        teaching_campus=Campus(
            name=obj.main_teaching_campus.name,
            university_name=obj.main_teaching_campus.organization.name,
        ),
        enrollment_campus=Campus(
            name=obj.enrollment_campus.name,
            university_name=obj.enrollment_campus.organization.name,
        ),
        other_campus_activities=ActivityPresence[
            obj.other_campus_activities] if obj.other_campus_activities else None,
        funding=Funding(
            can_be_funded=obj.funding,
            funding_orientation=FundingCodes[obj.funding_direction] if obj.funding_direction else None,
            can_be_international_funded=obj.funding_cud,
            international_funding_orientation=FundingCodes[obj.funding_direction_cud]
            if obj.funding_direction_cud else None,
        ),
        hops=HOPS(
            ares_code=obj.hops.ares_study,
            ares_graca=obj.hops.ares_graca,
            ares_authorization=obj.hops.ares_ability,
        ) if hasattr(obj, 'hops') else None,
        co_graduation=CoGraduation(
            code_inter_cfb=obj.co_graduation,
            coefficient=obj.co_graduation_coefficient,
        ),
        co_organizations=coorganizations,
        academic_type=AcademicTypes[obj.academic_type] if obj.academic_type else None,
        duration_unit=DurationUnitsEnum[obj.duration_unit] if obj.duration_unit else None,
        diploma=Diploma(
            leads_to_diploma=obj.joint_diploma,
            printing_title=obj.diploma_printing_title,
            professional_title=obj.professional_title,
            aims=certificate_aims
        )
    )


def __convert_study_domains_from_db(obj: EducationGroupYearModelDb) -> List['StudyDomain']:
    secondary_domains = []
    for domain in obj.secondary_domains.all():
        secondary_domains.append(
            StudyDomain(
                entity_id=StudyDomainIdentity(
                    decree_name=domain.decree.name,
                    code=domain.code,
                ),
                domain_name=domain.name,
            )
        )
    return secondary_domains


def __convert_diploma_aims_from_db(obj: EducationGroupYearModelDb) -> List['DiplomaAim']:
    certificate_aims = []
    for aim in obj.educationgroupcertificateaim_set.all():
        certificate_aims.append(
            DiplomaAim(
                entity_id=DiplomaAimIdentity(section=aim.certificate_aim.section, code=aim.certificate_aim.code),
                description=aim.certificate_aim.description,
            )
        )
    return certificate_aims


def __convert_coorganizations_from_db(
        training_identity: 'TrainingIdentity',
        obj: EducationGroupYearModelDb
) -> List['Coorganization']:
    coorganizations = []
    for coorg in obj.educationgrouporganization_set.all():
        first_address = coorg.organization.organizationaddress_set.all()[0]
        coorganizations.append(
            Coorganization(
                entity_id=CoorganizationIdentity(
                    partner_name=coorg.organization.name,
                    training_acronym=training_identity.acronym,
                    training_year=training_identity.year,
                ),
                partner=AcademicPartner(
                    entity_id=AcademicPartnerIdentity(name=coorg.organization.name),
                    address=Address(
                        country_name=first_address.country.name,
                        city=first_address.city,
                    ),
                    logo_url=coorg.organization.logo.url if coorg.organization.logo else None,
                ),
                is_for_all_students=coorg.all_students,
                is_reference_institution=coorg.enrollment_place,
                certificate_type=DiplomaCoorganizationTypes[coorg.diploma] if coorg.diploma else None,
                is_producing_certificate=coorg.is_producing_cerfificate,
                is_producing_certificate_annexes=coorg.is_producing_annexe,
            )
        )
    return coorganizations


def _get_queryset_to_fetch_data_for_training(entity_id: 'TrainingIdentity') -> QuerySet:
    return EducationGroupYearModelDb.objects.filter(
        acronym=entity_id.acronym,
        academic_year__year=entity_id.year
    ).select_related(
        'education_group_type',
        'hops',
        'management_entity',
        'administration_entity',
        'administration_entity',
        'enrollment_campus__organization',
        'main_teaching_campus__organization',
        'isced_domain',
        'education_group__start_year',
        'education_group__end_year',
        'primary_language',
        'main_domain__decree',
    ).prefetch_related(
        'secondary_domains',
        Prefetch(
            'educationgrouporganization_set',
            EducationGroupOrganizationModelDb.objects.all().prefetch_related(
                Prefetch(
                    'organization__organizationaddress_set',
                    OrganizationAddress.objects.all().select_related('country')
                )
            ).order_by('all_students')
        ),
        Prefetch(
            'administration_entity',
            Entity.objects.all().annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects.filter(
                        entity__id=OuterRef('pk')
                    ).order_by('-start_date').values('acronym')[:1]
                )
            )
        ),
        Prefetch(
            'management_entity',
            Entity.objects.all().annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects.filter(
                        entity__id=OuterRef('pk')
                    ).order_by('-start_date').values('acronym')[:1]
                )
            )
        ),
        Prefetch(
            'educationgroupcertificateaim_set',
            EducationGroupCertificateAimModelDb.objects.all().select_related('certificate_aim')
        ),
    )


def _save_education_group(
        training: 'Training'
) -> EducationGroupModelDb:
    education_group_db_obj, created = EducationGroupModelDb.objects.update_or_create(
        pk=training.identity_through_years.uuid if training.identity_through_years else None,
        defaults={
            'start_year':  AcademicYearModelDb.objects.get(year=training.start_year),
            'end_year':  AcademicYearModelDb.objects.get(year=training.end_year) if training.end_year else None,
        }
    )
    return education_group_db_obj


def _save_education_group_year(
        training: 'Training',
        education_group_db_obj: EducationGroupModelDb
) -> EducationGroupYearModelDb:
    obj = EducationGroupYearModelDb(
        academic_year=AcademicYearModelDb.objects.get(year=training.entity_id.year),
        acronym=training.entity_id.acronym,
        education_group_type=EducationGroupTypeModelDb.objects.get(name=training.type.name),
        active=training.status.name,
        credits=training.credits,
        schedule_type=training.schedule_type.name if training.schedule_type else None,
        duration=training.duration,
        education_group=education_group_db_obj,
        title=training.titles.title_fr,
        partial_title=training.titles.partial_title_fr,
        title_english=training.titles.title_en,
        partial_title_english=training.titles.partial_title_en,
        keywords=training.keywords,
        internship=training.internship_presence.name if training.internship_presence else None,
        enrollment_enabled=training.is_enrollment_enabled,
        web_re_registration=training.has_online_re_registration,
        partial_deliberation=training.has_partial_deliberation,
        admission_exam=training.has_admission_exam,
        dissertation=training.has_dissertation,
        university_certificate=training.produce_university_certificate,
        decree_category=training.decree_category.name if training.decree_category else None,
        rate_code=training.rate_code.name if training.rate_code else None,
        primary_language=LanguageModelDb.objects.get(
            name=training.main_language.name
        ) if training.main_language else None,
        english_activities=training.english_activities.name if training.english_activities else None,
        other_language_activities=training.other_language_activities.name
        if training.other_language_activities else None,
        internal_comment=training.internal_comment,
        main_domain=DomainModelDb.objects.get(
            code=training.main_domain.entity_id.code,
            decree__name=training.main_domain.entity_id.decree_name,
        ) if training.main_domain else None,
        isced_domain=DomainIscedModelDb.objects.get(
            code=training.isced_domain.entity_id.code
        ) if training.isced_domain else None,
        management_entity_id=entity_version.find_by_acronym_and_year(
            acronym=training.management_entity.acronym,
            year=training.year,
        ).entity_id if training.management_entity else None,
        administration_entity_id=entity_version.find_by_acronym_and_year(
            acronym=training.administration_entity.acronym,
            year=training.year,
        ).entity_id if training.administration_entity else None,
        main_teaching_campus=CampusModelDb.objects.get(
            name=training.teaching_campus.name,
            organization__name=training.teaching_campus.university_name,
        ) if training.teaching_campus else None,
        enrollment_campus=CampusModelDb.objects.get(
            name=training.enrollment_campus.name,
            organization__name=training.enrollment_campus.university_name,
        ) if training.teaching_campus else None,
        other_campus_activities=training.other_campus_activities.name if training.other_campus_activities else None,
        funding=training.funding.can_be_funded,
        funding_direction=training.funding.funding_orientation.name
        if training.funding and training.funding.funding_orientation else '',
        funding_cud=training.funding.can_be_international_funded,
        funding_direction_cud=training.funding.international_funding_orientation.name
        if training.funding and training.funding.international_funding_orientation else '',
        co_graduation=training.co_graduation.code_inter_cfb,
        co_graduation_coefficient=training.co_graduation.coefficient,
        academic_type=training.academic_type.name if training.academic_type else None,
        duration_unit=training.duration_unit.name if training.duration_unit else None,
        joint_diploma=training.diploma.leads_to_diploma,
        diploma_printing_title=training.diploma.printing_title,
        professional_title=training.diploma.professional_title,
    )
    obj.save()
    return obj


def _save_secondary_domains(
        training: 'Training',
        education_group_year_db_obj: EducationGroupYearModelDb
) -> List[EducationGroupYearDomainModelDb]:
    saved_objs = []
    for dom in training.secondary_domains:
        obj = EducationGroupYearDomainModelDb(
            education_group_year=education_group_year_db_obj,
            domain=DomainModelDb.objects.get(code=dom.entity_id.code, decree__name=dom.decree_name),
        ).save()
        saved_objs.append(obj)
    return saved_objs


def _save_hops(
        training: 'Training',
        education_group_year_db_obj: EducationGroupYearModelDb
) -> List[HopsModelDb]:
    saved_objs = []
    if training.hops:
        obj = HopsModelDb(
            education_group_year=education_group_year_db_obj,
            ares_study=training.hops.ares_code,
            ares_graca=training.hops.ares_graca,
            ares_ability=training.hops.ares_authorization,
        ).save()
        saved_objs.append(obj)
    return saved_objs


def _save_certificate_aims(
        training: 'Training',
        education_group_year_db_obj: EducationGroupYearModelDb
) -> List[EducationGroupCertificateAimModelDb]:
    saved_objs = []
    if training.diploma:
        for aim in training.diploma.aims:
            obj = EducationGroupCertificateAimModelDb(
                education_group_year=education_group_year_db_obj,
                certificate_aim=CertificateAimModelDb.objects.get(code=aim.entity_id.code)
            ).save()
            saved_objs.append(obj)
    return saved_objs
