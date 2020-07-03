from base.models.enums.education_group_types import GroupType


class GroupTypeConverter:
    regex = '\w+'

    def to_python(self, value):
        if value not in GroupType.get_names():
            raise ValueError("%s value: is not a valid group type")
        return value

    def to_url(self, value):
        return value
