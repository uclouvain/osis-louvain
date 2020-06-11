from django.contrib.postgres.fields import ArrayField
from django.db.models import Lookup


@ArrayField.register_lookup
class ArrayContainsAny(Lookup):
    lookup_name = 'contains_any'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = tuple(lhs_params) + tuple(rhs_params)
        return '%s = ANY(%s)' % (rhs, lhs), params
