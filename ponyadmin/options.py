from ponyadmin.views import QChangeList
from django.contrib import messages
from django.contrib import admin

from ponyadmin.mixins.alturl import AltUrlMixin
from ponyadmin.mixins.csv_export import CsvMixin


class QOrientedModelAdmin(CsvMixin, AltUrlMixin, admin.ModelAdmin):
    """
    This deep override of the modeladmin solves for a querying restriction
    of the approach which current django admin suffers.

    Admin filter objects receive a queryset, filter upon it, and then pass
    the newly filtered queryset down the chain for further querying by other
    similar objects. Sadly, each can only effectively chain filter() clauses,
    which when it comes to joins is a well documented limitation of the current
    ORM.
    """
    def get_filters(self, request):
        return []

    def get_breadcrumbs(self):
        return self.admin_site.get_breadcrumbs()

    def add_view(self, *args, **kwargs):
        kwargs['extra_context'] = {'modeladmin': self}
        return super(QOrientedModelAdmin, self).add_view(*args, **kwargs)

    def change_view(self, *args, **kwargs):
        kwargs['extra_context'] = {'modeladmin': self}
        return super(QOrientedModelAdmin, self).change_view(*args, **kwargs)

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = {'modeladmin': self}
        return super(QOrientedModelAdmin, self).changelist_view(*args, **kwargs)

    def get_actions(self, request):
        actions = super(QOrientedModelAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_changelist(self, request):
        return QChangeList

    def headers(self, request, qs):
        raise NotImplementedError

    def get_search_results(self, request, *args):
        qs, use_distinct = super(QOrientedModelAdmin, self).get_search_results(request, *args)

        try:
            headers = self.headers(request, qs)
            for key, value in headers.items():
                messages.info(request, "%s: %s" % (key, value))
        except NotImplementedError:
            pass

        return qs, use_distinct
