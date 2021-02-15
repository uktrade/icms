from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_wood_quota(request, pk):
    # TODO: implement (ICMSLST-516)
    from django.http import HttpResponse

    return HttpResponse(f"editing wood quota application {pk}")
