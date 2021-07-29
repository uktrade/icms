from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from web.types import AuthenticatedHttpRequest


@login_required
def edit_ironsteel(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    # TODO: ICMSLST-881 implement edit screen
    raise NotImplementedError
