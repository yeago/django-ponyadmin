from functools import update_wrapper
from django.conf.urls import url, include
from django.urls import reverse
from django.contrib import admin
from django.contrib.contenttypes import views as contenttype_views


class BaseAdminSite(admin.AdminSite):
    """
    A few subtle things here, but basically it attaches an instance of itself
    to the view objects, so that later admin functions can refer back to
    self.admin_site

    Also relaxes some URLs so that we can do things such as enabling
    additional url arguments to be passed to an admin site. From there
    we can create scenarios such as a changelist of all objects related to a particular
    person, with say that person's ID in the querystring
    """
    site_url = None
    site_header = ""

    def get_breadcrumbs(self):
        return [
            ("/", "Home"),
            (reverse("%s:index" % self.name), self.name),
        ]

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        # Admin-site-wide views.
        urlpatterns = [
            url(r'^$', wrap(self.index), name='index'),
            url(r'^admin/$', wrap(self.index), name='index'),
            url(r'^login/$', self.login, name='login'),
            url(r'^logout/$', wrap(self.logout), name='logout'),
            url(r'^password_change/$', wrap(self.password_change, cacheable=True), name='password_change'),
            url(r'^password_change/done/$', wrap(self.password_change_done, cacheable=True),
                name='password_change_done'),
            url(r'^jsi18n/$', wrap(self.i18n_javascript, cacheable=True), name='jsi18n'),
            url(r'^r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$', wrap(contenttype_views.shortcut),
                name='view_on_site'),
        ]

        # Add in each model's views, and create a list of valid URLS for the
        # app_index
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            urlpatterns += [
                url(r'^%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.urls)),
            ]
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        # If there were ModelAdmins registered, we should have a list of app
        # labels for which we need to allow access to the app_index view,
        if valid_app_labels:
            regex = r'^(?P<app_label>' + '|'.join(valid_app_labels) + ')/$'
            urlpatterns += [
                url(regex, wrap(self.app_index), name='app_list'),
            ]
        return urlpatterns
