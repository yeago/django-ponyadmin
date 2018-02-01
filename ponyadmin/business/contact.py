from django.core.exceptions import ObjectDoesNotExist


class LastContactMixin(object):
    def last_contact_date(self, obj):
        filters = dict((k.replace('contact__', '', 1), v) for k, v in self.lookup_manifest.items(
            ) if k.startswith('contact__'))
        try:
            return obj.contact_set.filter(**filters).latest('date').date
        except ObjectDoesNotExist:
            return "-"
