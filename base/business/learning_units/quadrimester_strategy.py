import abc

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class LearningComponentYearQuadriStrategy(metaclass=abc.ABCMeta):
    def __init__(self, lcy):
        self.lcy = lcy

    @abc.abstractmethod
    def is_valid(self):
        raise NotImplementedError


class LearningComponentYearQuadriNoStrategy(LearningComponentYearQuadriStrategy):
    def is_valid(self):
        return True


class LearningComponentYearQ1Strategy(LearningComponentYearQuadriStrategy):
    def is_valid(self):
        if not self.lcy.hourly_volume_partial_q1 or self.lcy.hourly_volume_partial_q2:
            raise ValidationError(_('Only the volume Q1 must have a value'))
        return True


class LearningComponentYearQ2Strategy(LearningComponentYearQuadriStrategy):
    def is_valid(self):
        if not self.lcy.hourly_volume_partial_q2 or self.lcy.hourly_volume_partial_q1:
            raise ValidationError(_('Only the volume Q2 must have a value'))
        return True


class LearningComponentYearQ1and2Strategy(LearningComponentYearQuadriStrategy):
    def is_valid(self):
        if not self.lcy.hourly_volume_partial_q1 or not self.lcy.hourly_volume_partial_q2:
            raise ValidationError(_('The volumes Q1 and Q2 must have a value'))
        return True


class LearningComponentYearQ1or2Strategy(LearningComponentYearQuadriStrategy):
    def is_valid(self):
        if (self.lcy.hourly_volume_partial_q1 and self.lcy.hourly_volume_partial_q2) or\
                (not self.lcy.hourly_volume_partial_q1 and not self.lcy.hourly_volume_partial_q2):
            raise ValidationError(_('The volume Q1 or Q2 must have a value but not both'))
        return True
