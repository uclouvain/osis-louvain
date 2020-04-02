from django_filters import OrderingFilter
from django_filters.constants import EMPTY_VALUES


class OrderingFilterWithDefault(OrderingFilter):
    """
    This filter override OrderingFilter in order to provide the default ordering capability
    """
    def __init__(self, *args, **kwargs):
        self.default_ordering = kwargs.pop('default_ordering', None)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in EMPTY_VALUES and self.default_ordering:
            return qs.order_by(*self.default_ordering)
        return super().filter(qs, value)
