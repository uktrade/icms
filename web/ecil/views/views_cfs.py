from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from markupsafe import Markup, escape

from web.domains.case.services import case_progress
from web.ecil.forms import forms_cfs as forms
from web.ecil.gds import component_serializers as serializers
from web.ecil.gds import forms as gds_forms
from web.ecil.gds.views import BackLinkMixin
from web.models import (
    CertificateOfFreeSaleApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest


def check_can_edit_application(user: User, application: CertificateOfFreeSaleApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


class CFSInProgressViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationStatusTaskMixin,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: CertificateOfFreeSaleApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


class CFSInProgressRelatedObjectViewBase(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    case_progress.InProgressApplicationRelatedObjectStatusTaskMixin,
):
    permission_required = [Perms.sys.exporter_access, Perms.sys.view_ecil_prototype]

    # Extra typing for clarity
    application: CertificateOfFreeSaleApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True


@method_decorator(transaction.atomic, name="post")
class CFSApplicationReferenceUpdateView(CFSInProgressViewBase, BackLinkMixin, UpdateView):
    # UpdateView config
    form_class = forms.CFSApplicationReferenceForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse("workbasket")

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.application.pk}
        )


@method_decorator(transaction.atomic, name="post")
class CFSApplicationContactUpdateView(CFSInProgressViewBase, BackLinkMixin, UpdateView):
    # UpdateView config
    form_class = forms.CFSApplicationContactForm
    template_name = "ecil/gds_form.html"

    def form_valid(self, form: forms.CFSApplicationContactForm) -> HttpResponseRedirect:
        contact = form.cleaned_data["contact"]

        if contact == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            self.application.contact = None
            self.application.save()

            return redirect(reverse("ecil:export-application:another-contact"))

        self.application.contact = contact
        self.application.save()

        return redirect(self.get_success_url())

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:application-reference", kwargs={"application_pk": self.application.pk}
        )

    def get_success_url(self) -> str:
        if self.application.countries.exists():
            redirect_to = "ecil:export-application:countries-add-another"
        else:
            redirect_to = "ecil:export-application:countries"

        return reverse(redirect_to, kwargs={"application_pk": self.application.pk})


@method_decorator(transaction.atomic, name="post")
class CFSScheduleCreateView(CFSInProgressViewBase, BackLinkMixin, TemplateView):
    # TemplateView config
    http_method_names = ["get", "post"]
    template_name = "ecil/cfs/schedule_create.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["create_schedule_btn_kwargs"] = serializers.button.ButtonKwargs(
            text="Create a product schedule",
            type="submit",
            isStartButton=True,
            preventDoubleClick=True,
        ).model_dump(exclude_defaults=True)

        return context

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        self.set_application_and_task()

        # TODO: When the cfs app is created it already creates a schedule.
        #       Decide how this should work (V2 isn't the same as v3).
        new_schedule = CFSSchedule.objects.create(
            application=self.application, created_by=request.user
        )

        return redirect(
            reverse(
                "ecil:export-cfs:schedule-exporter-status",
                kwargs={"application_pk": self.application.pk, "schedule_pk": new_schedule.pk},
            )
        )

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.application.pk}
        )


#
# Views relating to editing CFS Schedule fields
#
class CFSScheduleBaseView(CFSInProgressRelatedObjectViewBase, BackLinkMixin, SingleObjectMixin):
    # SingleObjectMixin | UpdateView config
    pk_url_kwarg = "schedule_pk"
    model = CFSSchedule

    # Classes using this mixin will have an application instance attribute
    application: CertificateOfFreeSaleApplication

    def get_queryset(self) -> QuerySet[CFSSchedule]:
        """Restrict the available schedules to the ones linked to the application."""
        return self.application.schedules.all()

    def get_object(self, queryset: QuerySet[CFSSchedule] | None = None) -> CFSSchedule:
        return super().get_object(queryset)


@method_decorator(transaction.atomic, name="post")
class CFSScheduleBaseUpdateView(CFSScheduleBaseView, UpdateView):
    """Common base class for all in progres CFS Schedule update views."""

    ...


@method_decorator(transaction.atomic, name="post")
class CFSScheduleBaseFormView(CFSScheduleBaseView, FormView):
    """Common base class for all in progres CFS Schedule related form views."""

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class CFSScheduleBaseTemplateView(CFSScheduleBaseView, TemplateView):
    """Common base class for all in progres CFS Schedule related template views."""

    ...


class CFSScheduleExporterStatusUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleExporterStatusForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.application.pk}
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleManufacturerAddressUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleManufacturerAddressForm
    template_name = "ecil/cfs/schedule_manufacturer_address.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schedule_number"] = forms.get_schedule_number(self.object)

        return context

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-exporter-status",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleBrandNameHolderUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleBrandNameHolderForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-country-of-manufacture",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleCountryOfManufactureUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleCountryOfManufactureForm
    template_name = "ecil/cfs/schedule_country_of_manufacture.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        if self.object.legislations.exists():
            redirect_to = "ecil:export-cfs:schedule-legislation-add-another"
        else:
            redirect_to = "ecil:export-cfs:schedule-legislation"

        return reverse(
            redirect_to,
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleAddLegislationUpdateView(CFSScheduleBaseUpdateView):
    """View to add a legislation to the set of legislations linked to the schedule.

    Logic to add the legislation is in the form save method.
    """

    # UpdateView config
    form_class = forms.CFSScheduleAddLegislationForm
    template_name = "ecil/cfs/schedule_legislation.html"

    def get_back_link_url(self) -> str | None:
        match self.get_referrer_view():
            case "ecil:export-cfs:schedule-legislation-add-another":
                return reverse(
                    "ecil:export-cfs:schedule-legislation-add-another",
                    kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
                )

            case _:
                return reverse(
                    "ecil:export-cfs:schedule-country-of-manufacture",
                    kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
                )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleAddAnotherLegislationFormView(CFSScheduleBaseFormView):
    # FormView config
    form_class = forms.CFSScheduleAddAnotherLegislationForm
    template_name = "ecil/cfs/schedule_legislation_add_another.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        schedule_legislations = self.object.legislations.all()
        legislation_count = schedule_legislations.count()

        if legislation_count == 1:
            legislation_heading = "You have added 1 legislation"
        else:
            # Correct message for 0 or greater than 1
            legislation_heading = f"You have added {legislation_count} legislations"

        context["legislation_heading"] = legislation_heading

        rows = []
        for legislation in schedule_legislations:
            rows.append(
                serializers.list_with_actions.ListRow(
                    name=legislation.name,
                    actions=[
                        serializers.list_with_actions.ListRowAction(
                            label="Remove",
                            url=reverse(
                                "ecil:export-cfs:schedule-legislation-remove",
                                kwargs={
                                    "application_pk": self.application.pk,
                                    "schedule_pk": self.object.pk,
                                    "legislation_pk": legislation.pk,
                                },
                            ),
                        ),
                    ],
                )
            )

        context["list_with_actions_kwargs"] = serializers.list_with_actions.ListWithActionsKwargs(
            rows=rows
        ).model_dump(exclude_defaults=True)

        context["schedule_number"] = forms.get_schedule_number(self.object)

        return context

    def form_valid(self, form: forms.CFSScheduleAddAnotherLegislationForm) -> HttpResponseRedirect:
        add_another = form.cleaned_data["add_another"]

        if add_another == YesNoChoices.yes:
            redirect_to = reverse(
                "ecil:export-cfs:schedule-legislation",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )
        else:
            redirect_to = reverse(
                "ecil:export-cfs:schedule-product-standard",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )

        return redirect(redirect_to)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleConfirmRemoveLegislationFormView(CFSScheduleBaseFormView):
    # FormView config
    form_class = forms.CFSScheduleRemoveLegislationForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.object
        kwargs["legislation"] = get_object_or_404(
            self.object.legislations, pk=self.kwargs["legislation_pk"]
        )

        return kwargs

    def form_valid(self, form: forms.CFSScheduleRemoveLegislationForm) -> HttpResponseRedirect:
        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            self.object.legislations.remove(form.legislation)

        return super().form_valid(form)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        if self.object.legislations.count() == 0:
            view_name = "ecil:export-cfs:schedule-legislation"
        else:
            view_name = "ecil:export-cfs:schedule-legislation-add-another"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        )


class CFSScheduleProductStandardUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleProductStandardForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        if self.object.legislations.count() == 0:
            view_name = "ecil:export-cfs:schedule-legislation"
        else:
            view_name = "ecil:export-cfs:schedule-legislation-add-another"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        )

    def get_success_url(self) -> str:
        if has_eu_cosmetic_regulation(self.object):
            view_name = "ecil:export-cfs:schedule-is-responsible-person"
        else:
            view_name = "ecil:export-cfs:schedule-accordance-with-standards"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        )


class CFSScheduleStatementIsResponsiblePersonUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleStatementIsResponsiblePersonForm
    template_name = "ecil/gds_form.html"

    def has_object_permission(self) -> bool:
        has_op = super().has_object_permission()
        return has_op and has_eu_cosmetic_regulation(self.get_object())

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-standard",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-accordance-with-standards",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


def has_eu_cosmetic_regulation(schedule: CFSSchedule) -> bool:
    schedule_legislations = schedule.legislations.filter(is_active=True)

    has_cosmetics = schedule_legislations.filter(is_eu_cosmetics_regulation=True).exists()
    not_export_only = schedule.goods_export_only == YesNoChoices.no

    return has_cosmetics and not_export_only


class CFSScheduleStatementAccordanceWithStandardsUpdateView(CFSScheduleBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleStatementAccordanceWithStandardsForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        if has_eu_cosmetic_regulation(self.object):
            view_name = "ecil:export-cfs:schedule-is-responsible-person"
        else:
            view_name = "ecil:export-cfs:schedule-product-standard"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk}
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-product-start",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


#
# Schedule product views
#
class CFSScheduleProductStartTemplateView(CFSScheduleBaseTemplateView):
    # TemplateView config
    template_name = "ecil/cfs/schedule_product_start.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)

        context["schedule_number"] = forms.get_schedule_number(self.object)
        context["next_url"] = reverse(
            "ecil:export-cfs:schedule-product-add-method",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )
        context["details_kwargs"] = serializers.details.DetailsKwargs(
            summaryText="The product is part of a kit",
            text=(
                "Products included in kits need to be listed individually."
                " Some products may need different legislations."
                " For example, if a kit includes toner, moisturiser and a hairbrush, the hairbrush"
                " would require a separate legislation as it is not a cosmetic product."
            ),
        ).model_dump(exclude_defaults=True)

        return context

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-accordance-with-standards",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


class CFSScheduleProductAddMethodFormView(CFSScheduleBaseFormView):
    # FormView config
    form_class = forms.CFSScheduleAddProductMethodForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.object

        return kwargs

    def form_valid(self, form: forms.CFSScheduleAddProductMethodForm) -> HttpResponseRedirect:
        method = form.cleaned_data["method"]

        if method == forms.CFSScheduleAddProductMethodForm.MANUAL:
            redirect_to = reverse(
                "ecil:export-cfs:schedule-product-add",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )
        else:
            redirect_to = reverse(
                "export:cfs-schedule-edit",
                kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
            )

        return redirect(redirect_to)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-start",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductCreateView(CFSScheduleBaseView, CreateView):
    # CreateView config
    form_class = forms.CFSScheduleProductForm
    template_name = "ecil/cfs/schedule_product_add.html"

    # Once the form is saved the view will have access to self.object
    object: CFSProduct

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schedule_number"] = forms.get_schedule_number(self.get_object())

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.get_object()

        return kwargs

    def get_back_link_url(self) -> str | None:
        schedule = self.get_object()

        return reverse(
            "ecil:export-cfs:schedule-product-add-method",
            kwargs={"application_pk": self.application.pk, "schedule_pk": schedule.pk},
        )

    def get_success_url(self) -> str:
        schedule = self.get_object()

        return reverse(
            "ecil:export-cfs:schedule-product-end-use",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": schedule.pk,
                "product_pk": self.object.pk,
            },
        )


class CFSScheduleProductAddAnotherFormView(CFSScheduleBaseFormView):
    # FormView config
    form_class = forms.CFSScheduleProductAddAnotherForm
    template_name = "ecil/cfs/schedule_product_add_another.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        schedule_products = self.object.products.order_by("product_name")
        product_count = schedule_products.count()

        if product_count == 1:
            product_heading = "You have added 1 product"
        else:
            # Correct message for 0 or greater than 1
            product_heading = f"You have added {product_count} products"

        context["product_heading"] = product_heading

        rows = []

        for product in schedule_products:
            name = f"<strong>{escape(product.product_name)}</strong>"
            if product.product_end_use:
                name += f"<br>{escape(product.product_end_use)}"
            if product.is_raw_material:
                name += "<br>Raw material"

            rows.append(
                serializers.list_with_actions.ListRow(
                    name=Markup(name),
                    actions=[
                        serializers.list_with_actions.ListRowAction(
                            label="Remove",
                            url=reverse(
                                "ecil:export-cfs:schedule-product-remove",
                                kwargs={
                                    "application_pk": self.application.pk,
                                    "schedule_pk": self.object.pk,
                                    "product_pk": product.pk,
                                },
                            ),
                        ),
                        serializers.list_with_actions.ListRowAction(
                            label="Change",
                            url=reverse(
                                "ecil:export-cfs:schedule-product-edit",
                                kwargs={
                                    "application_pk": self.application.pk,
                                    "schedule_pk": self.object.pk,
                                    "product_pk": product.pk,
                                },
                            ),
                        ),
                    ],
                )
            )

        context["list_with_actions_kwargs"] = serializers.list_with_actions.ListWithActionsKwargs(
            rows=rows
        ).model_dump(exclude_defaults=True)

        context["schedule_number"] = forms.get_schedule_number(self.object)

        return context

    def form_valid(self, form: forms.CFSScheduleAddAnotherLegislationForm) -> HttpResponseRedirect:
        kwargs = {"application_pk": self.application.pk, "schedule_pk": self.object.pk}

        if form.cleaned_data["add_another"] == YesNoChoices.yes:
            redirect_to = reverse("ecil:export-cfs:schedule-product-add", kwargs=kwargs)
        else:
            redirect_to = reverse("export:cfs-schedule-edit", kwargs=kwargs)

        return redirect(redirect_to)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-add-method",
            kwargs={"application_pk": self.application.pk, "schedule_pk": self.object.pk},
        )


#
# Views relating to editing CFS Schedule product fields.
#
class CFSScheduleProductBaseView(
    CFSInProgressRelatedObjectViewBase, BackLinkMixin, SingleObjectMixin
):
    pk_url_kwarg = "product_pk"
    model = CFSProduct

    # Extra typing for clarity
    object: CFSProduct

    def get_schedule(self) -> CFSSchedule:
        return get_object_or_404(self.application.schedules, pk=self.kwargs["schedule_pk"])

    def get_queryset(self) -> QuerySet[CFSProduct]:
        """Filter the queryset used in SingleObjectMixin that fetches the correct product."""
        return self.get_schedule().products.all()

    def get_object(self, queryset: QuerySet[CFSProduct] | None = None) -> CFSProduct:
        return super().get_object(queryset)


class CFSScheduleProductBaseUpdateView(CFSScheduleProductBaseView, UpdateView):
    """Common base class for all in progres CFS Schedule product update views."""

    ...


class CFSScheduleProductBaseFormView(CFSScheduleProductBaseView, FormView):
    """Common base class for all in progres CFS Schedule product related form views."""

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        self.set_application_and_task()
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductUpdateView(CFSScheduleProductBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleProductForm
    # Reuse xxx_add.html template for now (it may change in next design)
    template_name = "ecil/cfs/schedule_product_add.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["schedule_number"] = forms.get_schedule_number(self.object.schedule)

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["schedule"] = self.object.schedule

        return kwargs

    def get_back_link_url(self) -> str | None:
        schedule = self.object.schedule

        return reverse(
            "ecil:export-cfs:schedule-product-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": schedule.pk},
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-product-end-use",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.object.schedule.pk,
                "product_pk": self.object.pk,
            },
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductEndUseUpdateView(CFSScheduleProductBaseUpdateView):
    # UpdateView config
    form_class = forms.CFSScheduleProductEndUseForm
    template_name = "ecil/gds_form.html"

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-edit",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.object.schedule.pk,
                "product_pk": self.object.pk,
            },
        )

    def get_success_url(self) -> str:
        schedule = self.object.schedule

        if has_biocidal_legislation(schedule):
            if self.object.product_type_numbers.exists():
                return reverse(
                    "ecil:export-cfs:schedule-product-type-add-another",
                    kwargs={
                        "application_pk": self.application.pk,
                        "schedule_pk": schedule.pk,
                        "product_pk": self.object.pk,
                    },
                )
            else:
                return reverse(
                    "ecil:export-cfs:schedule-product-type-add",
                    kwargs={
                        "application_pk": self.application.pk,
                        "schedule_pk": schedule.pk,
                        "product_pk": self.object.pk,
                    },
                )

        return reverse(
            "ecil:export-cfs:schedule-product-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": schedule.pk},
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductConfirmRemoveFormView(CFSScheduleProductBaseView, DeleteView):
    # DeleteView config
    form_class = forms.CFSScheduleProductConfirmRemoveForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.get_object()

        return kwargs

    def form_valid(self, form: forms.CFSScheduleProductConfirmRemoveForm) -> HttpResponseRedirect:
        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            self.object.delete()

        return redirect(self.get_success_url())

    def get_back_link_url(self) -> str | None:
        schedule = self.get_schedule()

        return reverse(
            "ecil:export-cfs:schedule-product-add-another",
            kwargs={"application_pk": self.application.pk, "schedule_pk": schedule.pk},
        )

    def get_success_url(self) -> str:
        schedule = self.get_schedule()

        if schedule.products.count() == 0:
            view_name = "ecil:export-cfs:schedule-product-add"
        else:
            view_name = "ecil:export-cfs:schedule-product-add-another"

        return reverse(
            view_name, kwargs={"application_pk": self.application.pk, "schedule_pk": schedule.pk}
        )


#
# CFS Product Type views.
#
@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductTypeCreateView(CFSScheduleProductBaseView, CreateView):
    # CreateView config
    form_class = forms.CFSScheduleProductTypeForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    # Once the form is saved the view will have access to self.object
    object: CFSProductType

    def has_object_permission(self) -> bool:
        has_op = super().has_object_permission()
        return has_op and has_biocidal_legislation(self.get_schedule())

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.get_object()

        return kwargs

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-end-use",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": self.get_object().pk,
            },
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-product-type-add-another",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": self.get_object().pk,
            },
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductTypeAddAnotherFormView(CFSScheduleProductBaseFormView):
    # FormView config
    form_class = forms.CFSScheduleProductTypeAddAnotherForm
    template_name = "ecil/cfs/schedule_product_type_add_another.html"

    def has_object_permission(self) -> bool:
        has_op = super().has_object_permission()
        return has_op and has_biocidal_legislation(self.get_schedule())

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        product = self.object

        product_type_numbers = product.product_type_numbers.order_by("product_type_number")
        ptn_count = product_type_numbers.count()

        if ptn_count == 1:
            sub_heading = f"You have added 1 product type number for {escape(product.product_name)}"
        else:
            # Correct message for 0 or greater than 1
            sub_heading = f"You have added {ptn_count} product type numbers for {escape(product.product_name)}"

        context["sub_heading"] = sub_heading
        rows = []

        for ptn in product_type_numbers:
            rows.append(
                serializers.list_with_actions.ListRow(
                    name=f"PT {ptn.product_type_number}",
                    actions=[
                        serializers.list_with_actions.ListRowAction(
                            label="Remove",
                            url=reverse(
                                "ecil:export-cfs:schedule-product-type-remove",
                                kwargs={
                                    "application_pk": self.application.pk,
                                    "schedule_pk": self.get_schedule().pk,
                                    "product_pk": product.pk,
                                    "product_type_pk": ptn.pk,
                                },
                            ),
                        ),
                    ],
                )
            )

        context["list_with_actions_kwargs"] = serializers.list_with_actions.ListWithActionsKwargs(
            rows=rows
        ).model_dump(exclude_defaults=True)

        context["schedule_number"] = forms.get_schedule_number(self.object.schedule)

        return context

    def form_valid(self, form: forms.CFSScheduleAddAnotherLegislationForm) -> HttpResponseRedirect:
        kwargs = {
            "application_pk": self.application.pk,
            "schedule_pk": self.get_schedule().pk,
            "product_pk": self.object.pk,
        }

        if form.cleaned_data["add_another"] == YesNoChoices.yes:
            redirect_to = reverse("ecil:export-cfs:schedule-product-type-add", kwargs=kwargs)
        else:
            redirect_to = reverse(
                "ecil:export-cfs:schedule-product-active-ingredient-add", kwargs=kwargs
            )

        return redirect(redirect_to)

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-end-use",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": self.get_object().pk,
            },
        )


@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductTypeConfirmRemoveFormView(
    CFSInProgressRelatedObjectViewBase, BackLinkMixin, DeleteView
):
    # DeleteView config
    pk_url_kwarg = "product_type_pk"
    model = CFSProductType
    form_class = forms.CFSScheduleProductTypeConfirmRemoveForm
    template_name = "ecil/gds_form.html"
    http_method_names = ["get", "post"]

    # Extra typing for clarity
    object: CFSProductType

    def has_object_permission(self) -> bool:
        has_op = super().has_object_permission()
        return has_op and has_biocidal_legislation(self.get_schedule())

    def get_schedule(self) -> CFSSchedule:
        return get_object_or_404(self.application.schedules, pk=self.kwargs["schedule_pk"])

    def get_product(self) -> CFSProduct:
        return get_object_or_404(self.get_schedule().products, pk=self.kwargs["product_pk"])

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["product_type"] = self.get_object()

        return kwargs

    def form_valid(self, form: forms.CFSScheduleProductConfirmRemoveForm) -> HttpResponseRedirect:
        if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
            self.object.delete()

        return redirect(self.get_success_url())

    def get_back_link_url(self) -> str | None:
        schedule = self.get_schedule()
        product = self.get_product()

        return reverse(
            "ecil:export-cfs:schedule-product-type-add-another",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": schedule.pk,
                "product_pk": product.pk,
            },
        )

    def get_success_url(self) -> str:
        product = self.get_product()

        if product.product_type_numbers.count() == 0:
            view_name = "ecil:export-cfs:schedule-product-type-add"
        else:
            view_name = "ecil:export-cfs:schedule-product-type-add-another"

        return reverse(
            view_name,
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": product.pk,
            },
        )


#
# CFS Product Active Ingredient views.
#
@method_decorator(transaction.atomic, name="post")
class CFSScheduleProductActiveIngredientCreateView(CFSScheduleProductBaseView, CreateView):
    # CreateView config
    form_class = forms.CFSScheduleProductActiveIngredientForm
    template_name = "ecil/cfs/schedule_product_active_ingredient_add.html"
    http_method_names = ["get", "post"]

    # Once the form is saved the view will have access to self.object
    object: CFSProductActiveIngredient

    def has_object_permission(self) -> bool:
        has_op = super().has_object_permission()
        return has_op and has_biocidal_legislation(self.get_schedule())

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        product = self.get_object()

        context = super().get_context_data(**kwargs)
        context["schedule_number"] = forms.get_schedule_number(product.schedule)
        context["sub_heading"] = (
            f"What are the active ingredients for {escape(product.product_name)}?"
        )

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["product"] = self.get_object()

        return kwargs

    def get_back_link_url(self) -> str | None:
        return reverse(
            "ecil:export-cfs:schedule-product-end-use",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": self.get_object().pk,
            },
        )

    def get_success_url(self) -> str:
        return reverse(
            "ecil:export-cfs:schedule-product-active-ingredient-add-another",
            kwargs={
                "application_pk": self.application.pk,
                "schedule_pk": self.get_schedule().pk,
                "product_pk": self.get_object().pk,
            },
        )


# @method_decorator(transaction.atomic, name="post")
# class CFSScheduleProductActiveIngredientAddAnotherFormView(CFSScheduleProductBaseFormView):
#     # FormView config
#     form_class = forms.CFSScheduleProductActiveIngredientAddAnotherForm
#     template_name = "ecil/cfs/schedule_product_type_add_another.html"
#
#     def has_object_permission(self) -> bool:
#         has_op = super().has_object_permission()
#         return has_op and has_biocidal_legislation(self.get_schedule())
#
#     def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
#         context = super().get_context_data(**kwargs)
#
#         product = self.object
#
#         product_type_numbers = product.product_type_numbers.order_by("product_type_number")
#         ptn_count = product_type_numbers.count()
#
#         if ptn_count == 1:
#             sub_heading = f"You have added 1 product type number for {escape(product.product_name)}"
#         else:
#             # Correct message for 0 or greater than 1
#             sub_heading = f"You have added {ptn_count} product type numbers for {escape(product.product_name)}"
#
#         context["sub_heading"] = sub_heading
#         rows = []
#
#         for ptn in product_type_numbers:
#             rows.append(
#                 serializers.list_with_actions.ListRow(
#                     name=f"PT {ptn.product_type_number}",
#                     actions=[
#                         serializers.list_with_actions.ListRowAction(
#                             label="Remove",
#                             url=reverse(
#                                 "ecil:export-cfs:schedule-product-active-ingredient-remove",
#                                 kwargs={
#                                     "application_pk": self.application.pk,
#                                     "schedule_pk": self.get_schedule().pk,
#                                     "product_pk": product.pk,
#                                     "active_ingredient_pk": ptn.pk,
#                                 },
#                             ),
#                         ),
#                     ],
#                 )
#             )
#
#         context["list_with_actions_kwargs"] = serializers.list_with_actions.ListWithActionsKwargs(
#             rows=rows
#         ).model_dump(exclude_defaults=True)
#
#         context["schedule_number"] = forms.get_schedule_number(self.object.schedule)
#
#         return context
#
#     def form_valid(self, form: forms.CFSScheduleAddAnotherLegislationForm) -> HttpResponseRedirect:
#         kwargs = {"application_pk": self.application.pk, "schedule_pk": self.get_schedule().pk}
#
#         if form.cleaned_data["add_another"] == YesNoChoices.yes:
#             kwargs["product_pk"] = self.object.pk
#             redirect_to = reverse("ecil:export-cfs:schedule-product-active-ingredient-add", kwargs=kwargs)
#         else:
#             redirect_to = reverse("export:cfs-schedule-edit", kwargs=kwargs)
#
#         return redirect(redirect_to)
#
#     def get_back_link_url(self) -> str | None:
#         return reverse(
#             "ecil:export-cfs:schedule-product-end-use",
#             kwargs={
#                 "application_pk": self.application.pk,
#                 "schedule_pk": self.get_schedule().pk,
#                 "product_pk": self.get_object().pk,
#             },
#         )
#
#
# @method_decorator(transaction.atomic, name="post")
# class CFSScheduleProductActiveIngredientConfirmRemoveFormView(
#     CFSInProgressRelatedObjectViewBase, BackLinkMixin, DeleteView
# ):
#     # DeleteView config
#     pk_url_kwarg = "active_ingredient_pk"
#     model = CFSProductActiveIngredient
#     form_class = forms.CFSScheduleProductActiveIngredientConfirmRemoveForm
#     template_name = "ecil/gds_form.html"
#     http_method_names = ["get", "post"]
#
#     # Extra typing for clarity
#     object: CFSProductActiveIngredient
#
#     def has_object_permission(self) -> bool:
#         has_op = super().has_object_permission()
#         return has_op and has_biocidal_legislation(self.get_schedule())
#
#     def get_schedule(self) -> CFSSchedule:
#         return get_object_or_404(self.application.schedules, pk=self.kwargs["schedule_pk"])
#
#     def get_product(self) -> CFSProduct:
#         return get_object_or_404(self.get_schedule().products, pk=self.kwargs["product_pk"])
#
#     def get_form_kwargs(self) -> dict[str, Any]:
#         kwargs = super().get_form_kwargs()
#         kwargs["product_type"] = self.get_object()
#
#         return kwargs
#
#     def form_valid(self, form: forms.CFSScheduleProductConfirmRemoveForm) -> HttpResponseRedirect:
#         if form.cleaned_data["are_you_sure"] == YesNoChoices.yes:
#             self.object.delete()
#
#         return redirect(self.get_success_url())
#
#     def get_back_link_url(self) -> str | None:
#         schedule = self.get_schedule()
#         product = self.get_product()
#
#         return reverse(
#             "ecil:export-cfs:schedule-product-active-ingredient-add-another",
#             kwargs={
#                 "application_pk": self.application.pk,
#                 "schedule_pk": schedule.pk,
#                 "product_pk": product.pk,
#             },
#         )
#
#     def get_success_url(self) -> str:
#         product = self.get_product()
#
#         if product.product_type_numbers.count() == 0:
#             view_name = "ecil:export-cfs:schedule-product-active-ingredient-add"
#         else:
#             view_name = "ecil:export-cfs:schedule-product-active-ingredient-add-another"
#
#         return reverse(
#             view_name,
#             kwargs={
#                 "application_pk": self.application.pk,
#                 "schedule_pk": self.get_schedule().pk,
#                 "product_pk": product.pk,
#             },
#         )


def has_biocidal_legislation(schedule: CFSSchedule) -> bool:
    return schedule.legislations.filter(is_active=True, is_biocidal=True).exists()
