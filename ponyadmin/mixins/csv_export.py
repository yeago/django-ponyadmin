import unicodecsv as csv

from django.shortcuts import render
from django.http import HttpResponse

from html.parser import HTMLParser


class HTMLRemover(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def printable(modeladmin, request, queryset):
    try:
        headers = modeladmin.headers(request, queryset)
    except NotImplementedError:
        headers = {}

    items = [modeladmin.csv_header(request)]
    for item in queryset:
        items.append(modeladmin.csv_row(request, item))

    return render(request, "printable.html", {
        "headers": headers,
        "items": items,
    })


printable.short_description = "Printable"


def csv_export(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    try:
        export_name = modeladmin.export_name
    except AttributeError:
        export_name = queryset.model._meta.verbose_name
    finally:
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % export_name
    writer = csv.writer(response)

    try:
        headers = modeladmin.headers(request, queryset)
        for key, value in headers.iteritems():
            writer.writerow((key, value))
        writer.writerow([])
    except NotImplementedError:
        pass

    writer.writerow(modeladmin.csv_header(request))
    for item in queryset:
        writer.writerow(modeladmin.csv_row(request, item))
    return response


csv_export.short_description = "Export to Excel"


class CsvMixin(object):
    csv_ignore = ['action_checkbox']
    actions = [csv_export, printable]

    def csv_header(self, request):
        header = []
        for item in self.get_list_display(request):
            if not callable(item):  # list_display = ['category_display']
                item = getattr(self, item, item)
            if callable(item):  # list_display = [category_display]
                try:
                    header.append(item.short_description)
                except AttributeError:
                    header.append(item.__name__)
                continue
            header.append(item)
        return header

    def csv_row(self, request, obj):
        def clean(val):
            val = '%s' % val
            htmlremover = HTMLRemover()
            htmlremover.feed('%s' % val)
            val = htmlremover.get_data()
            return val.replace('&nbsp;', '').encode("utf-8")
        row = []
        for item in self.get_list_display(request):
            if item in self.csv_ignore:
                continue
            text = None
            if not callable(item) and hasattr(self, item):
                """
                item could be 'loan_date' with SomeAdmin.loan_date
                this flattens that to always be the method
                """
                if callable(getattr(self, item)):
                    item = getattr(self, item)
            if callable(item):
                if item.__name__ in self.csv_ignore:
                    continue
                text = item(obj)
            else:
                attr = getattr(obj, item)  # Let this fail if it must
                if callable(attr):
                    text = attr()
                else:
                    try:
                        text = getattr(obj, 'get_%s_display' % item)()
                    except AttributeError:
                        text = attr
            row.append(clean(text or "-"))

        try:
            row.extend(map(clean, self.csv_extra_items(request, obj)))
        except NotImplementedError:
            pass
        return row

    def csv_extra_items(self, request, obj):
        raise NotImplementedError
