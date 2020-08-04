from osis_common.ddd.interface import BusinessException
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from education_group.ddd.business_types import *


class TrainingNotFoundException(Exception):
    pass


class MiniTrainingNotFoundException(Exception):
    pass


class GroupNotFoundException(Exception):
    pass


class GroupCodeAlreadyExistException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Code already exists")
        super().__init__(message, **kwargs)


class MiniTrainingCodeAlreadyExistException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Code already exists")
        super().__init__(message, **kwargs)


class AcademicYearNotFound(Exception):
    pass


class TypeNotFound(Exception):
    pass


class ManagementEntityNotFound(Exception):
    pass


class TeachingCampusNotFound(Exception):
    pass


class ContentConstraintTypeMissing(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("You should precise constraint type")
        super().__init__(message, **kwargs)


class ContentConstraintMinimumMaximumMissing(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("You should precise at least minimum or maximum constraint")
        super().__init__(message, **kwargs)


class ContentConstraintMaximumShouldBeGreaterOrEqualsThanMinimum(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("%(max)s must be greater or equals than %(min)s") % {
                    "max": _("maximum constraint").title(),
                    "min": _("minimum constraint").title(),
                 }
        super().__init__(message, **kwargs)


class StartYearGreaterThanEndYearException(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Validity cannot be greater than last year of organization")
        super().__init__(message, **kwargs)


class CreditShouldBeGreaterOrEqualsThanZero(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Credits must be greater or equals than 0")
        super().__init__(message, **kwargs)


class AcronymRequired(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Acronym/Short title is required")
        super().__init__(message, **kwargs)


class AcronymAlreadyExist(BusinessException):
    def __init__(self, abbreviated_title: str, *args, **kwargs):
        message = _("Acronym/Short title '{}' already exists").format(abbreviated_title)
        super().__init__(message, **kwargs)


class CannotCopyTrainingDueToEndDate(BusinessException):
    def __init__(self, training: 'Training', *args, **kwargs):
        message = _(
            "You can't copy the training '{acronym}' from {from_year} to {to_year} because it ends in {end_year}"
        ).format(
            acronym=training.acronym,
            from_year=training.year,
            to_year=training.year + 1,
            end_year=training.end_year,
        )
        super().__init__(message, **kwargs)


class CannotCopyMiniTrainingDueToEndDate(BusinessException):
    def __init__(self, mini_training: 'MiniTraining', *args, **kwargs):
        message = _(
            "You can't copy the mini-training '{code}' from {from_year} to {to_year} because it ends in {end_year}"
        ).format(
            code=mini_training.code,
            from_year=mini_training.year,
            to_year=mini_training.year + 1,
            end_year=mini_training.end_year,
        )
        super().__init__(message, **kwargs)


class StartYearGreaterThanEndYear(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _('End year must be greater than the start year, or equal')
        super().__init__(message, **kwargs)


class MaximumCertificateAimType2Reached(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("There can only be one type 2 expectation")
        super().__init__(message, **kwargs)


class TrainingHaveEnrollments(BusinessException):
    def __init__(self, enrollment_count: int, **kwargs):
        message = ngettext_lazy(
            "%(count_enrollment)d student is enrolled in the training.",
            "%(count_enrollment)d students are enrolled in the training.",
            enrollment_count
        ) % {"count_enrollment": enrollment_count}
        super().__init__(message, **kwargs)


class TrainingHaveLinkWithEPC(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Linked with EPC")
        super().__init__(message, **kwargs)


class MiniTrainingHaveEnrollments(BusinessException):
    def __init__(self, enrollment_count: int, **kwargs):
        message = ngettext_lazy(
            "%(count_enrollment)d student is enrolled in the mini-training.",
            "%(count_enrollment)d students are enrolled in the mini-training.",
            enrollment_count
        ) % {"count_enrollment": enrollment_count}
        super().__init__(message, **kwargs)


class MiniTrainingHaveLinkWithEPC(BusinessException):
    def __init__(self, *args, **kwargs):
        message = _("Linked with EPC")
        super().__init__(message, **kwargs)
