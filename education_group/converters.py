from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType


class GroupTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in GroupType.get_names():
            raise ValueError("%s value: is not a valid group type")
        return value

    def to_url(self, value):
        return value


class MiniTrainingTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in MiniTrainingType.get_names():
            raise ValueError("%s value: is not a valid mini-training type")
        return value

    def to_url(self, value):
        return value


class TrainingTypeConverter:
    regex = r'\w+'

    def to_python(self, value):
        if value not in TrainingType.get_names():
            raise ValueError("%s value: is not a valid training type")
        return value

    def to_url(self, value):
        return value
