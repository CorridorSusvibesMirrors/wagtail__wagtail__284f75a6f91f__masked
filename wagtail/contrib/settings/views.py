from functools import lru_cache

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    extract_panel_definitions_from_model_class,
)
from wagtail.admin.views import generic
from wagtail.models import Site

from .forms import SiteSwitchForm
from .models import BaseGenericSetting, BaseSiteSetting
from .registry import registry


def get_model_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid setting type
    """
    model = registry.get_by_natural_key(app_name, model_name)
    if model is None:
        raise Http404
    return model


@lru_cache(maxsize=None)
def get_setting_edit_handler(model):
    if hasattr(model, "edit_handler"):
        edit_handler = model.edit_handler
    else:
        if issubclass(model, BaseSiteSetting):
            panels = extract_panel_definitions_from_model_class(model, ["site"])
        elif issubclass(model, BaseGenericSetting):
            panels = extract_panel_definitions_from_model_class(model)
        else:
            raise NotImplementedError

        edit_handler = ObjectList(panels)
    return edit_handler.bind_to_model(model)


def redirect_to_relevant_instance(request, app_name, model_name):
    model = get_model_from_url_params(app_name, model_name)

    if issubclass(model, BaseSiteSetting):
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site in the list)
        site_request = Site.find_for_request(request)
        site = site_request or Site.objects.first()
        if not site:
            messages.error(
                request,
                _("This setting could not be opened because there is no site defined."),
            )
            return redirect("wagtailadmin_home")
        return redirect(
            "wagtailsettings:edit",
            app_name,
            model_name,
            site.pk,
        )
    elif issubclass(model, BaseGenericSetting):
        return redirect(
            "wagtailsettings:edit",
            app_name,
            model_name,
            model.load(request_or_site=request).id,
        )
    else:
        raise NotImplementedError
