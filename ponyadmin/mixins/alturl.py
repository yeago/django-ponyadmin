from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http import HttpResponseRedirect
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR, escape
from django.utils.translation import ugettext as _
from django.template.response import SimpleTemplateResponse


class AltUrlMixin(object):
    change_form_template = "admin/change_form_alt.html"
    change_list_template = "admin/change_list_alt.html"
    object_history_template = "admin/history_alt.html"

    def response_delete(self, request, obj_display, obj_id):
        """
        Determines the HttpResponse for the delete_view stage.
        """

        opts = self.model._meta

        if IS_POPUP_VAR in request.POST:
            return SimpleTemplateResponse('admin/popup_response.html', {
                'action': 'delete',
                'value': escape(obj_id),
            })

        self.message_user(
            request,
            _('The %(name)s "%(obj)s" was deleted successfully.') % {
                'name': force_text(opts.verbose_name),
                'obj': force_text(obj_display),
            }, messages.SUCCESS)

        if self.has_change_permission(request, None):
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts}, self.admin_changelist_url()
            )
        else:
            post_url = self.admin_index_url()
        return HttpResponseRedirect(post_url)

    def admin_add_url(self):
        return reverse('admin:%s_%s_add' %
                       (self.model._meta.app_label, self.model._meta.model_name),
                       current_app=self.admin_site.name)

    def admin_delete_url(self, obj=None):
        pk_value = obj._get_pk_val()
        return reverse('admin:%s_%s_delete' % (
            self.model._meta.app_label, self.model._meta.model_name),
            args=(pk_value,),
            current_app=self.admin_site.name)

    def admin_change_url(self, obj=None):
        pk_value = obj._get_pk_val()
        return reverse('admin:%s_%s_change' % (
            self.model._meta.app_label, self.model._meta.model_name),
            args=(pk_value,),
            current_app=self.admin_site.name)

    def admin_index_url(self):
        return reverse('admin:index', current_app=self.admin_site.name)

    def admin_changelist_url(self):
        return reverse('admin:%s_%s_changelist' %
                       (self.model._meta.app_label, self.model._meta.model_name),
                       current_app=self.admin_site.name)

    def response_post_save_add(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        opts = self.model._meta
        if self.has_change_permission(request, None):
            post_url = self.admin_changelist_url()
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url)
        else:
            post_url = self.admin_index_url()
        return HttpResponseRedirect(post_url)

    def response_post_save_change(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when editing an existing object.
        """
        opts = self.model._meta

        if self.has_change_permission(request, None):
            post_url = self.admin_changelist_url()
            preserved_filters = self.get_preserved_filters(request)
            post_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, post_url)
        else:
            post_url = self.admin_index_url()
        return HttpResponseRedirect(post_url)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determines the HttpResponse for the add_view stage.
        """
        opts = obj._meta
        preserved_filters = self.get_preserved_filters(request)
        msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
        # Here, we distinguish between different save types by checking for
        # the presence of keys in request.POST.

        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            return SimpleTemplateResponse('admin/popup_response.html', {
                'value': value,
                'obj': obj,
            })

        elif "_continue" in request.POST:
            msg = _('The %(name)s "%(obj)s" was added successfully. You may edit it again below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            if post_url_continue is None:
                post_url_continue = self.admin_change_url(obj)
            post_url_continue = add_preserved_filters(
                {'preserved_filters': preserved_filters, 'opts': opts},
                post_url_continue
            )
            return HttpResponseRedirect(post_url_continue)

        elif "_addanother" in request.POST:
            msg = _('The %(name)s "%(obj)s" was added successfully. You may add another %(name)s below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        else:
            msg = _('The %(name)s "%(obj)s" was added successfully.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_add(request, obj)

    def response_change(self, request, obj):
        """
        Determines the HttpResponse for the change_view stage.
        """

        if IS_POPUP_VAR in request.POST:
            to_field = request.POST.get(TO_FIELD_VAR)
            attr = str(to_field) if to_field else obj._meta.pk.attname
            # Retrieve the `object_id` from the resolved pattern arguments.
            value = request.resolver_match.args[0]
            new_value = obj.serializable_value(attr)
            return SimpleTemplateResponse('admin/popup_response.html', {
                'action': 'change',
                'value': value,
                'obj': obj,
                'new_value': new_value,
            })

        opts = self.model._meta
        preserved_filters = self.get_preserved_filters(request)

        msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
        if "_continue" in request.POST:
            msg = _('The %(name)s "%(obj)s" was changed successfully. You may edit it again below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = request.path
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif "_saveasnew" in request.POST:
            msg = _('The %(name)s "%(obj)s" was added successfully. You may edit it again below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = self.admin_change_url(obj)
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        elif "_addanother" in request.POST:
            msg = _('The %(name)s "%(obj)s" was changed successfully. You may add another %(name)s below.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = self.admin_add_url()
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        else:
            msg = _('The %(name)s "%(obj)s" was changed successfully.') % msg_dict
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_change(request, obj)
