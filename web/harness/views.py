import decimal
import random
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView, View
from guardian.shortcuts import assign_perm

from web.models import Exporter, Importer, Office, User
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from . import forms


class L10NTestHarnessView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):  # /PS-IGNORE
    # PermissionRequiredMixin config
    permission_required = [Perms.page.view_l10n_harness]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "web/harness/l10n.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        datetime_value = timezone.now()
        date_value = datetime_value.date()
        time_value = datetime_value.time()
        int_field = 123_456_789
        float_field = 123_456_789.45
        decimal_field = decimal.Decimal(123_456_789.456)
        split_date_time_field = [date_value, time_value]

        form_data = {
            "date_field": date_value,
            "datetime_field": datetime_value,
            "time_field": time_value,
            "int_field": int_field,
            "float_field": float_field,
            "decimal_field": decimal_field,
            "split_date_time_field": split_date_time_field,
        }

        localised_form = forms.LocalizedForm(initial=form_data)
        non_localised_form = forms.NonLocalizedForm(initial=form_data)

        return context | {
            "datetime_value": datetime_value,
            "date_value": date_value,
            "time_value": time_value,
            "int_field": int_field,
            "float_field": float_field,
            "decimal_field": decimal_field,
            "localised_form": localised_form,
            "non_localised_form": non_localised_form,
        }


class PermissionTestHarnessView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.page.view_permission_harness]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "web/harness/permissions.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "importers": Importer.objects.filter(name__startswith="Dummy "),
            "exporters": Exporter.objects.filter(name__startswith="Dummy "),
            "users": _get_test_users(),
        }


def _get_test_users() -> QuerySet[User]:
    return User.objects.filter(
        username__in=["ilb_admin", "ilb_admin_2", "importer_user", "exporter_user", "agent"]
    )


class CreateHarnessDataView(PermissionRequiredMixin, LoginRequiredMixin, View):
    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin, Perms.page.view_permission_harness]

    # View config
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> Any:
        self._create_harness_data()

        return redirect("harness:permissions")

    @staticmethod
    def _create_harness_data(r: int = 100) -> None:
        prefix = Importer.objects.count()

        test_users = _get_test_users()

        for i in range(1, r, 1):
            uniq_num = prefix + i

            importer = Importer.objects.create(
                is_active=True,
                name=f"Dummy Importer {prefix}-{i}",
                registered_number=f"{uniq_num:0>15}",
                eori_number=f"GB{prefix + i:1>15}",
                type=Importer.ORGANISATION,
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"Address 1 {uniq_num}",
                address_2=f"Address 2 {uniq_num}",
                address_3=f"Address 3 {uniq_num}",
                postcode="SW1A 2HP",  # /PS-IGNORE
            )
            importer.offices.add(office)

            exporter = Exporter.objects.create(
                is_active=True,
                name=f"Dummy Exporter{prefix}-{i}",
                registered_number=f"{uniq_num:1>15}",
            )

            office = Office.objects.create(
                is_active=True,
                address_1=f"Address 1 {uniq_num}",
                address_2=f"Address 2 {uniq_num}",
                address_3=f"Address 3 {uniq_num}",
                postcode="SW1A 2HP",  # /PS-IGNORE
            )
            exporter.offices.add(office)

            for user in test_users:
                _assign_permissions_randomly(user, importer, Perms.obj.importer.values)
                _assign_permissions_randomly(user, exporter, Perms.obj.exporter.values)


def _assign_permissions_randomly(user: User, obj: Importer | Exporter, perms: list[str]) -> None:
    for perm in perms:
        if random.choice([True, False]):
            assign_perm(perm, user, obj)
