from ponyadmin.options import QOrientedModelAdmin
from ponyadmin.site import BaseAdminSite
from ponyadmin.filters import RelatedFieldListFilter
from django.db.models.query_utils import Q

from django.conf import settings
from django.utils.encoding import smart_text
from django.utils.module_loading import import_string

underlings_plus_self = import_string(settings.UNDERLINGS_PLUS_SELF)
underlings = import_string(settings.UNDERLINGS)


class ReadOnlyMixin(object):
    def has_add_permission(self, request):
        return False


class StaffModelAdmin(QOrientedModelAdmin):
    staff_attr = 'staff'
    staff_query_attr = None

    def get_admin_perm(self):
        if hasattr(self, 'admin_perm'):
            return self.admin_perm
        return self.admin_site.admin_perm

    def has_change_permission(self, request, obj=None):
        if obj:
            if self.get_admin_perm() and request.user.has_perm(self.get_admin_perm()):
                return True
            if self.staff_attr:
                staff = getattr(obj, self.staff_attr)
                return staff == request.user or staff in request.user.supervisor_of.all()
        return True

    def get_list_filter(self, request):
        """
        Default behavior. If its a simple relationship of obj->staff, we can use staff_attr

        If its through other objects (like csr belong objects), it must be custom for now
        but staff_query_attr can be used for the filtering portion
        """
        if not self.staff_attr and not self.staff_query_attr:
            return self.list_filter
        if self.get_admin_perm() and request.user.has_perm(self.get_admin_perm()):
            return self.list_filter
        if underlings(request.user):
            return self.list_filter
        return list(self.exclude_staff_filter())

    def exclude_staff_filter(self):
        for item in self.list_filter:
            try:
                name, _ = item
            except ValueError:
                name = item
            except TypeError:
                yield item
                continue
            if name in [self.staff_attr, self.staff_query_attr]:
                continue
            yield item

    def get_staff_filters(self, request, staff):
        if len(staff) == 1:
            return [(Q(**{(self.staff_query_attr or self.staff_attr): request.user}))]
        return [(Q(**{"%s__in" % (self.staff_query_attr or self.staff_attr): staff}))]

    def get_filters(self, request):
        filters = super(StaffModelAdmin, self).get_filters(request)
        if (self.staff_attr or self.staff_query_attr) and not (
                self.get_admin_perm() and request.user.has_perm(self.get_admin_perm())):
            #  If they have the permission we can just skip all of this
            staff = underlings_plus_self(request.user)
            filters.extend(self.get_staff_filters(request, staff) or [])
        return filters


class AdminModelAdmin(StaffModelAdmin):
    def has_change_permission(self, request, obj=None):
        if request.user.has_perm(self.get_admin_perm()):
            return True
        if obj:
            if self.staff_attr:
                staff = getattr(obj, self.staff_attr)
                return staff in underlings(request.user)
        return len(underlings(request.user)) > 0

    def get_filters(self, request):
        if not request.user.has_perm(self.get_admin_perm()) and self.staff_attr:
            return [Q(**{"%s__in" % self.staff_attr: underlings(request.user)})]


class AdminOnlyModelAdmin(AdminModelAdmin):
    def has_module_permission(self, request):
        if request.user.has_perm(self.get_admin_perm()):
            return True
        return False

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def get_queryset(self, request):
        """
        Intentionally skipping super since access is totally restricted without needing querying
        """
        return super(StaffModelAdmin, self).get_queryset(request)


class StaffAdminSite(BaseAdminSite):
    def has_permission(self, request):
        if request.user.is_authenticated and request.user.is_active:
            return True
        return False


class StaffFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin, field_path, qs=None):
        """
        This is basically cribbed from django.db.models.fields

        Couldn't really see an easy way to attach the ordering without
        hacking up the User default manager or moving the whole install FK
        to some proxy model
        """
        limit_choices_to = {'pk__in': set(qs or model_admin.get_queryset(request).values_list(field_path, flat=True))}
        rel_model = field.remote_field.model
        lst = [(getattr(x, field.remote_field.get_related_field().attname),
               smart_text(x))
               for x in rel_model._default_manager.complex_filter(
                   limit_choices_to).order_by('-is_active', 'last_name')]

        return lst
