import random
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from guardian.shortcuts import assign_perm

from web.models import Exporter, Importer, Office, User
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest


class PermissionTestHarnessView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    # PermissionRequiredMixin config
    permission_required = [Perms.page.view_permission_harness.value]  # type: ignore[attr-defined]

    # TemplateView config
    http_method_names = ["get"]
    template_name = "web/perm_harness/index.html"

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
    permission_required = [
        Perms.sys.ilb_admin.value,  # type: ignore[attr-defined]
        Perms.page.view_permission_harness.value,  # type: ignore[attr-defined]
    ]

    # View config
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs) -> Any:
        self._create_harness_data()

        return redirect("perm_test:harness")

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
