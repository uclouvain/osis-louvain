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
from base.ddd.utils import business_validator
from education_group.ddd.business_types import *
from education_group.ddd.validators._abbreviated_title_already_exist import AcronymAlreadyExistValidator
from education_group.ddd.validators._acronym_required import AcronymRequiredValidator
from education_group.ddd.validators._certificate_aim_type_2 import CertificateAimType2Validator
from education_group.ddd.validators._content_constraint import ContentConstraintValidator
from education_group.ddd.validators._copy_check_mini_training_end_date import CheckMiniTrainingEndDateValidator
from education_group.ddd.validators._copy_check_training_end_date import CheckTrainingEndDateValidator
from education_group.ddd.validators._credits import CreditsValidator
from education_group.ddd.validators._enrollments import TrainingEnrollmentsValidator, MiniTrainingEnrollmentsValidator
from education_group.ddd.validators._link_with_epc import TrainingLinkWithEPCValidator, MiniTrainingLinkWithEPCValidator
from education_group.ddd.validators._start_year_end_year import StartYearEndYearValidator
from education_group.ddd.validators.start_and_end_year_validator import StartAndEndYearValidator


class CreateGroupValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            group: 'Group'
    ):
        self.validators = [
            ContentConstraintValidator(group.content_constraint),
            CreditsValidator(group.credits),
        ]
        super().__init__()


class UpdateGroupValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            group: 'Group'
    ):
        self.validators = [
            ContentConstraintValidator(group.content_constraint),
            CreditsValidator(group.credits),
        ]
        super().__init__()


class CreateMiniTrainingValidatorList(business_validator.BusinessListValidator):
    def __init__(self, mini_training_domain_obj: 'MiniTraining'):
        self.validators = [
            AcronymRequiredValidator(mini_training_domain_obj.acronym),
            AcronymAlreadyExistValidator(mini_training_domain_obj.acronym),
            StartAndEndYearValidator(mini_training_domain_obj.start_year, mini_training_domain_obj.end_year)
        ]
        super().__init__()


class CreateTrainingValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            training: 'Training'
    ):
        self.validators = [
            AcronymRequiredValidator(training.acronym),
            AcronymAlreadyExistValidator(training.acronym),
            StartYearEndYearValidator(training),
            CertificateAimType2Validator(training),
        ]
        super().__init__()


class CopyTrainingValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            training_from: 'Training'
    ):
        self.validators = [
            CheckTrainingEndDateValidator(training_from),
        ]
        super().__init__()


class CopyMiniTrainingValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            mini_training_from: 'MiniTraining'
    ):
        self.validators = [
            CheckMiniTrainingEndDateValidator(mini_training_from),
        ]
        super().__init__()


class DeleteOrphanGroupValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            group: 'Group',
    ):
        self.validators = []
        super().__init__()


class DeleteOrphanTrainingValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            training: 'Training',
    ):
        self.validators = [
            TrainingEnrollmentsValidator(training.entity_id),
            TrainingLinkWithEPCValidator(training.entity_id)
        ]
        super().__init__()


class DeleteOrphanMiniTrainingValidatorList(business_validator.BusinessListValidator):

    def __init__(
            self,
            mini_training: 'MiniTraining',
    ):
        self.validators = [
            MiniTrainingEnrollmentsValidator(mini_training.entity_id),
            MiniTrainingLinkWithEPCValidator(mini_training.entity_id)
        ]
        super().__init__()
