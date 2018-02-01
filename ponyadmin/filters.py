from django.contrib.admin.filters import (
    RelatedFieldListFilter as BaseRelFil, get_model_from_relation)
from django.contrib import admin
from django.db.models.query_utils import Q


class SingleTextInputFilter(admin.SimpleListFilter):
    """
    renders filter form with text input and submit button
    """

    parameter_name = None
    template = "admin/textinput_filter.html"
    lookup_type = "exact"

    def lookups(self, *args, **kwargs):
        return []

    def __init__(self, request, params, model, model_admin):
        super(SingleTextInputFilter, self).__init__(request, params, model, model_admin)
        if self.parameter_name is None:
            self.parameter_name = self.field.name

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "_null":
                params = dict(("%s__isnull" % k, True) for k, v in self.used_parameters.items())
            else:
                params = dict(("%s__%s" % (k, self.lookup_type), v) for k, v in self.used_parameters.items())
            return Q(**params)

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.parameter_name, None)

    def has_output(self):
        return True

    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        return [self.parameter_name]

    def choices(self, cl):
        blank_choice = {
            'selected': self.value() is "_null",
            'query_string': cl.get_query_string({self.parameter_name: '_null'}, [self.parameter_name]),
            'display': 'Blank',
        }
        all_choice = {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': 'All',
        }
        return ({
            'get_query': cl.params,
            'current_value': self.value(),
            'all_choice': all_choice,
            'blank_choice': blank_choice,
            'parameter_name': self.parameter_name
        }, )


class RelatedFieldListFilter(BaseRelFil):
    def __init__(self, field, request, params, model, model_admin, field_path, **kwargs):
        other_model = get_model_from_relation(field)
        self.lookup_kwarg = '%s__%s__exact' % (field_path, field.target_field.name)
        self.lookup_kwarg_isnull = '%s__isnull' % field_path
        self.lookup_val = request.GET.get(self.lookup_kwarg)
        self.lookup_val_isnull = request.GET.get(self.lookup_kwarg_isnull)
        try:
            self.lookup_choices = self.field_choices(field, request, model_admin, field_path, **kwargs)
        except ValueError:
            self.lookup_choices = self.field_choices(field, request, model_admin, **kwargs)
        super(BaseRelFil, self).__init__(
            field, request, params, model, model_admin, field_path)
        if hasattr(field, 'verbose_name'):
            self.lookup_title = field.verbose_name
        else:
            self.lookup_title = other_model._meta.verbose_name
        self.title = self.lookup_title
        self.empty_value_display = model_admin.get_empty_value_display()


def custom_titled_filter(title, Klass):
    class Wrapper(Klass):
        def __new__(cls, *args, **kwargs):
            instance = Klass(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper
