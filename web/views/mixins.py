from typing import Any

from django.views.generic.base import View
from django.views.generic.list import ListView


class PageTitleMixin(View):
    """Adds page title attribute of view to context"""

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Try get_page_title method first which takes precedence
        page_title = getattr(self, "get_page_title", None)
        if page_title:
            page_title = page_title()
        else:
            # Get page_title attribute if get_page_title doesn't exist
            page_title = getattr(self, "page_title", None)
        context["page_title"] = page_title
        return context


class DataDisplayConfigMixin(PageTitleMixin, ListView):
    """Adds display configuration for listed object"""

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        display = getattr(self, "Display", None)
        if display:
            context["display"] = display
        return context


class PostActionMixin:
    """Handle post requests with action variable: Calls method with the same
    name as action variable to handle action"""

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action:
            if hasattr(self, action):
                return getattr(self, action)(request, *args, **kwargs)

        # If action does not exist continue with regular post request
        return super().post(request, *args, **kwargs)  # type: ignore[misc]
