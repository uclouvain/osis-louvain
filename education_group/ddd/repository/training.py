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

from django.db.models import Subquery, OuterRef, Prefetch

from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.diploma_coorganization import DiplomaCoorganizationTypes
from base.models.enums.duration_unit import DurationUnits, DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.funding_codes import FundingCodes
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from base.models.organization_address import OrganizationAddress
from education_group.ddd.business_types import *
from education_group.ddd.domain import training, exception
from education_group.ddd.domain._academic_partner import AcademicPartner
from education_group.ddd.domain._address import Address
from education_group.ddd.domain._campus import Campus
from education_group.ddd.domain._co_graduation import CoGraduation
from education_group.ddd.domain._co_organization import Coorganization
from education_group.ddd.domain._diploma import Diploma, DiplomaAim
from education_group.ddd.domain._entity import Entity as EntityValueObject
from education_group.ddd.domain._funding import Funding
from education_group.ddd.domain._hops import HOPS
from education_group.ddd.domain._isced_domain import IscedDomain
from education_group.ddd.domain._language import Language
from education_group.ddd.domain._study_domain import StudyDomain
from education_group.ddd.domain._titles import Titles
from osis_common.ddd import interface


class TrainingRepository(interface.AbstractRepository):
    @classmethod
    def create(cls, entity: 'Training') -> 'TrainingIdentity':
        raise NotImplementedError

    @classmethod
    def update(cls, entity: 'Training') -> 'TrainingIdentity':
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'TrainingIdentity') -> 'Training':
        qs = EducationGroupYear.objects.filter(
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
                EducationGroupOrganization.objects.all().prefetch_related(
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
                EducationGroupCertificateAim.objects.all().select_related('certificate_aim')
            ),
        )

        try:
            obj = qs.get()
        except EducationGroupYear.DoesNotExist:
            raise exception.TrainingNotFoundException

        secondary_domains = []
        for domain in obj.secondary_domains.all():
            secondary_domains.append(
                StudyDomain(
                    decree_name=domain.decree.name,
                    code=domain.code,
                    name=domain.name,
                )
            )

        coorganizations = []
        for coorg in obj.educationgrouporganization_set.all():
            first_address = coorg.organization.organizationaddress_set.all()[0]
            coorganizations.append(
                Coorganization(
                    partner=AcademicPartner(
                        name=coorg.organization.name,
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

        certificate_aims = []
        for aim in obj.educationgroupcertificateaim_set.all():
            certificate_aims.append(
                DiplomaAim(
                    section=aim.certificate_aim.section,
                    code=aim.certificate_aim.code,
                    description=aim.certificate_aim.description,
                )
            )

        return training.Training(
            entity_identity=entity_id,
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
            keywords=obj.keywords,
            internship=InternshipPresence[obj.internship] if obj.internship else None,
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
                decree_name=obj.main_domain.decree.name,
                code=obj.main_domain.code,
                name=obj.main_domain.name,
            ) if obj.main_domain else None,
            secondary_domains=secondary_domains,
            isced_domain=IscedDomain(
                code=obj.isced_domain.code,
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

    @classmethod
    def search(cls, entity_ids: Optional[List['TrainingIdentity']] = None, **kwargs) -> List['Training']:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'TrainingIdentity') -> None:
        raise NotImplementedError
