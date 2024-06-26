from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode

from web.permissions import Perms
from web.views import ModelFilterView, actions

from . import filters, forms, models


class SanctionEmailsListView(ModelFilterView):
    template_name = "web/domains/sanction-emails/list.html"
    model = models.SanctionEmail
    filterset_class = filters.SanctionEmailsFilter
    permission_required = Perms.sys.manage_sanction_contacts
    page_title = "Maintain Sanction Emails"

    class Display:
        fields = ["name", "email"]
        fields_config = {
            "name": {"header": "Name"},
            "email": {"header": "Email Address"},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [
            actions.Edit(hide_if_archived_object=True, **opts),
            actions.Archive(**opts),
            actions.Unarchive(*opts),
        ]


@login_required
@permission_required(Perms.sys.manage_sanction_contacts, raise_exception=True)
def create_sanction_email(request):
    if request.method == "POST":
        form = forms.SanctionEmailForm(request.POST)
        if form.is_valid():
            sanction_email: models.SanctionEmail = form.save()
            messages.info(request, "New sanction email created successfully.")
            return redirect(
                reverse("sanction-emails:list") + "?" + urlencode({"name": sanction_email.name})
            )

    else:
        form = forms.SanctionEmailForm()

    context = {
        "page_title": "Create Sanction Email",
        "form": form,
    }

    return render(request, "web/domains/sanction-emails/create.html", context)


@login_required
@permission_required(Perms.sys.manage_sanction_contacts, raise_exception=True)
def edit_sanction_email(request, pk):
    sanction_email = get_object_or_404(models.SanctionEmail, pk=pk)

    if request.method == "POST":
        form = forms.SanctionEmailForm(request.POST, instance=sanction_email)
        if form.is_valid():
            sanction_email = form.save()
            messages.info(request, "Sanction email details saved.")
            return redirect(
                reverse("sanction-emails:list") + "?" + urlencode({"name": sanction_email.name})
            )
    else:
        form = forms.SanctionEmailForm(instance=sanction_email)

    context = {
        "page_title": "Edit Sanction Email",
        "form": form,
    }

    return render(request, "web/domains/sanction-emails/edit.html", context)
