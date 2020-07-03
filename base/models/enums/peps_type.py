from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class PepsTypes(ChoiceEnum):
    NOT_DEFINED = _('Not defined')
    DISABILITY = _('DDI')
    SPORT = _('Sport')
    ARTIST = _('Artist')
    ENTREPRENEUR = _('Entrepreneur')
    ARRANGEMENT_JURY = _('Educational facilities accepted by Jury')


class HtmSubtypes(ChoiceEnum):
    REDUCED_MOBILITY = _('Person with reduced mobility')
    OTHER_DISABILITY = _('Other special needs')


class SportSubtypes(ChoiceEnum):
    PROMISING_ATHLETE_HL = _('High Level Promising athlete')
    PROMISING_ATHLETE = _('Promising athlete')
