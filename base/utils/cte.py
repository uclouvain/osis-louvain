from django.db.models import Subquery


class CTESubquery(Subquery):
    """
    Subquery that also resolve expressions of CTE

    WARNING: This will only work in Django<3.0
    See https://github.com/dimagi/django-cte/pull/16
    """
    def resolve_expression(self, query=None, allow_joins=True, reuse=None,
                           summarize=False, for_save=False):
        """
        This is the same as SubQuery bu twe also resolve fields for CTEs
        """
        clone = self.copy()
        clone.is_summary = summarize
        clone.queryset.query.bump_prefix(query)

        # Need to recursively resolve these.
        def resolve_all(child):
            if hasattr(child, 'children'):
                [resolve_all(_child) for _child in child.children]
            if hasattr(child, 'rhs'):
                child.rhs = resolve(child.rhs)

        def resolve(child):
            if hasattr(child, 'resolve_expression'):
                resolved = child.resolve_expression(
                    query=query, allow_joins=allow_joins, reuse=reuse,
                    summarize=summarize, for_save=for_save,
                )
                # Add table alias to the parent query's aliases to prevent
                # quoting.
                if hasattr(resolved, 'alias') and \
                        resolved.alias != resolved.target.model._meta.db_table:
                    clone.queryset.query.external_aliases.add(resolved.alias)
                return resolved
            return child

        resolve_all(clone.queryset.query.where)

        for key, value in clone.queryset.query.annotations.items():
            if isinstance(value, Subquery):
                clone.queryset.query.annotations[key] = resolve(value)

        for cte in clone.queryset.query._with_ctes:
            resolve_all(cte.query.where)
            for key, value in cte.query.annotations.items():
                if isinstance(value, Subquery):
                    cte.query.annotations[key] = resolve(value)

        return clone
