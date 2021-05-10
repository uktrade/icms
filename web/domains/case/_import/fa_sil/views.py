from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit(request: HttpRequest, pk: int) -> HttpResponse:
    return render(request, "web/domains/case/import/fa-sil/edit.html", {})
