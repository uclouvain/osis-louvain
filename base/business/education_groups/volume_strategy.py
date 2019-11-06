import abc

from django.utils.translation import gettext_lazy as _


class VolumeEditionStrategy(metaclass=abc.ABCMeta):
    def __init__(self, obj, input_names):
        self.obj = obj
        self.input_names = input_names
        self.raw_volume_q1 = self.obj.cleaned_data.get(input_names['volume_q1'])
        self.volume_q1 = self.raw_volume_q1 or 0
        self.raw_volume_q2 = self.obj.cleaned_data.get(input_names['volume_q2'])
        self.volume_q2 = self.raw_volume_q2 or 0
        self.volume_total = self.obj.cleaned_data.get(input_names['volume_total']) or 0
        self.planned_classes = self.obj.cleaned_data.get(input_names['planned_classes']) or 0
        self.raw_volume_requirement_entity = self.obj.cleaned_data.get(input_names['volume_requirement_entity'])
        self.volume_requirement_entity = self.raw_volume_requirement_entity or 0
        self.raw_volume_additional_requirement_entity_1 = self.obj.cleaned_data.get(
            input_names['volume_additional_requirement_entity_1'])
        self.volume_additional_requirement_entity_1 = self.raw_volume_additional_requirement_entity_1 or 0
        self.raw_volume_additional_requirement_entity_2 = self.obj.cleaned_data.get(
            input_names['volume_additional_requirement_entity_2'])
        self.volume_additional_requirement_entity_2 = self.raw_volume_additional_requirement_entity_2 or 0
        self.is_fac = None
        self.initial_volume_q1 = None
        self.initial_volume_q2 = None

    @abc.abstractmethod
    def is_valid(self):
        # TODO: reduce cognitive complexity (at 29 now)
        if self.raw_volume_q1 is not None or self.raw_volume_q2 is not None:
            if self.volume_total != self.volume_q1 + self.volume_q2:
                self.obj.add_error(self.input_names['volume_total'],
                                   _('The annual volume must be equal to the sum of the volumes Q1 and Q2'))
                if self.raw_volume_q1 is not None:
                    self.obj.add_error(self.input_names['volume_q1'], "")
                if self.raw_volume_q2 is not None:
                    self.obj.add_error(self.input_names['volume_q2'], "")

        if self.planned_classes > 0 and self.volume_total == 0:
            self.obj.add_error(self.input_names['planned_classes'],
                               _('planned classes cannot be greather than 0 while volume is equal to 0'))
        if self.planned_classes == 0 and self.volume_total > 0:
            self.obj.add_error(self.input_names['planned_classes'],
                               _('planned classes cannot be 0 while volume is greater than 0'))

        if self.raw_volume_requirement_entity is not None or \
                self.raw_volume_additional_requirement_entity_1 is not None or \
                self.raw_volume_additional_requirement_entity_2 is not None:
            if self.volume_total * self.planned_classes != self.volume_requirement_entity + \
                    self.volume_additional_requirement_entity_1 + \
                    self.volume_additional_requirement_entity_2:
                if self.raw_volume_additional_requirement_entity_1 is None and \
                        self.raw_volume_additional_requirement_entity_2 is None:
                    self.obj.add_error(self.input_names['volume_requirement_entity'],
                                       _('The volume of the entity must be equal to the global volume'))
                else:
                    self.obj.add_error(self.input_names['volume_requirement_entity'],
                                       _('The sum of the volumes of the entities must be equal to the global volume'))
                    if self.raw_volume_additional_requirement_entity_1 is not None:
                        self.obj.add_error(self.input_names['volume_additional_requirement_entity_1'], '')
                    if self.raw_volume_additional_requirement_entity_2 is not None:
                        self.obj.add_error(self.input_names['volume_additional_requirement_entity_2'], '')


class SimpleVolumeEditionFacultyStrategy(VolumeEditionStrategy):
    def __init__(self, obj, input_names):
        super(SimpleVolumeEditionFacultyStrategy, self).__init__(obj, input_names)
        self.initial_volume_q1 = self.obj.instance.hourly_volume_partial_q1
        self.initial_volume_q2 = self.obj.instance.hourly_volume_partial_q2

    def is_valid(self):
        super().is_valid()
        if 0 in [self.initial_volume_q1, self.initial_volume_q2]:
            if 0 not in [self.raw_volume_q1, self.raw_volume_q2]:
                self.obj.add_error(self.input_names['volume_q1'],
                                   _("One of the partial volumes must have a value to 0."))
                self.obj.add_error(self.input_names['volume_q2'],
                                   _("One of the partial volumes must have a value to 0."))

        else:
            if self.raw_volume_q1 == 0:
                self.obj.add_error(self.input_names['volume_q1'], _("The volume can not be set to 0."))
            if self.raw_volume_q2 == 0:
                self.obj.add_error(self.input_names['volume_q2'], _("The volume can not be set to 0."))


class CompleteVolumeEditionFacultyStrategy(VolumeEditionStrategy):
    def __init__(self, obj, input_names):
        super(CompleteVolumeEditionFacultyStrategy, self).__init__(obj, input_names)
        self.initial_volume_q1 = self.obj.initial.get(self.input_names['volume_q1'])
        self.initial_volume_q2 = self.obj.initial.get(self.input_names['volume_q2'])

    def is_valid(self):
        super().is_valid()
        if 0 in [self.initial_volume_q1, self.initial_volume_q2]:
            if 0 not in [self.raw_volume_q1, self.raw_volume_q2]:
                self.obj.add_error(self.input_names['volume_q1'],
                                   _("One of the partial volumes must have a value to 0."))
                self.obj.add_error(self.input_names['volume_q2'],
                                   _("One of the partial volumes must have a value to 0."))

        else:
            if self.raw_volume_q1 == 0:
                self.obj.add_error(self.input_names['volume_q1'], _("The volume can not be set to 0."))
            if self.raw_volume_q2 == 0:
                self.obj.add_error(self.input_names['volume_q2'], _("The volume can not be set to 0."))


class VolumeEditionNoFacultyStrategy(VolumeEditionStrategy):
    def is_valid(self):
        super().is_valid()
        return True
