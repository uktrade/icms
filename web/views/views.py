from black import Any
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from web.auth.decorators import require_registered
from web.auth.mixins import RequireRegisteredMixin

from .actions import PostAction
from .mixins import DataDisplayConfigMixin, PageTitleMixin


@require_registered
def home(request):
    return render(request, "web/home.html")


class ModelFilterView(RequireRegisteredMixin, DataDisplayConfigMixin, ListView):
    paginate_by = 50
    paginate = True

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        actions = getattr(self.Display, "actions", [])
        for a in actions:
            if isinstance(a, PostAction) and a.action == action:
                response = a.handle(request, self, *args, **kwargs)
                if response:
                    return response

        # Render the same page
        return super().get(request, *args, **kwargs)

    def get_page(self):
        return self.request.GET.get("page")

    def _paginate(self, queryset):
        paginator = Paginator(queryset, self.paginate_by)
        page = self.get_page()

        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    def get_filterset(self, **kwargs):
        return self.filterset_class(
            self.request.GET or None, queryset=self.get_queryset(), **kwargs
        )

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        filterset = self.get_filterset()
        context["filter"] = filterset
        if self.paginate:
            context["page"] = self._paginate(filterset.qs)
        else:
            context["results"] = filterset.qs
        return context


class ModelCreateView(RequireRegisteredMixin, PageTitleMixin, SuccessMessageMixin, CreateView):
    template_name = "model/edit.html"

    def get_success_message(self, cleaned_data):
        return f"{self.object} created successfully."


class ModelUpdateView(RequireRegisteredMixin, PageTitleMixin, SuccessMessageMixin, UpdateView):
    template_name = "model/edit.html"

    def get_success_message(self, cleaned_data):
        return f"{self.object} updated successfully"

    def get_page_title(self):
        return f"Editing {self.object}"


class ModelDetailView(RequireRegisteredMixin, PageTitleMixin, DetailView):
    template_name = "model/view.html"

    def _readonly(self, form):
        for key in form.fields.keys():
            form.fields[key].disabled = True
        return form

    def get_form(self, instance=None):
        """Create new instance of form and make readonly"""
        form = self.form_class(instance=instance)
        return self._readonly(form)

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form(instance=self.get_object())
        return context

    def get_page_title(self):
        return f"Viewing {self.object}"
