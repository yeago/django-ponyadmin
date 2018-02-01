from django.contrib.admin.views.main import (
    ChangeList, SuspiciousOperation, ImproperlyConfigured, IncorrectLookupParameters)
from django.db.models.query_utils import Q


class QChangeList(ChangeList):
    """
    Mostly explained and options.py, this changelist override is necessary
    because here the behavior of django filter objects dramatically changes
    from objects which receive, process, and return s queryset, to objects
    which simply return a Q object to later be processed by the changelist
    object all within one filter() clause here
    """

    def get_queryset(self, request):
        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params,
         filters_use_distinct) = self.get_filters(request)

        # Then, we let every list filter modify the queryset to its liking.
        # or return a Q-like will be applied all together afterwards
        qs = self.root_queryset
        qlikes = []  # filterspec: [q, l, i, k, e, s]
        self.model_admin.lookup_manifest = {}
        for filter_spec in self.filter_specs:
            new_qs_or_q = filter_spec.queryset(request, qs)
            if new_qs_or_q is not None:
                if hasattr(filter_spec, 'lookup_val') and hasattr(filter_spec, 'lookup_kwarg'):
                    if getattr(filter_spec, 'lookup_val'):
                        qlikes.append(Q(**{filter_spec.lookup_kwarg: filter_spec.lookup_val}))
                        continue
                if isinstance(new_qs_or_q, Q):
                    qlikes.append(new_qs_or_q)
                else:
                    qs = new_qs_or_q

        if hasattr(self.model_admin, 'get_filters'):
            qlikes.extend(self.model_admin.get_filters(request) or [])
        if qlikes:
            q_base = Q()
            for item in qlikes:
                for lookup, val in item.children:
                    self.model_admin.lookup_manifest[lookup] = val
                q_base &= item
            qs = qs.filter(q_base)

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_use_distinct = self.model_admin.get_search_results(request, qs, self.query)

        # Remove duplicates from results, if necessary
        if filters_use_distinct | search_use_distinct:
            return qs.distinct()
        else:
            return qs
