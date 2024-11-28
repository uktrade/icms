import pytest
from django.urls import reverse

from web.domains.template.widgets import EndorsementTemplateWidget
from web.models import Template


@pytest.mark.parametrize("term,count", [("op", 2), ("open individual", 1)])
def test_endorsement_template_widget(term, count, ilb_admin_client):
    widget = EndorsementTemplateWidget(
        queryset=Template.objects.filter(is_active=True, template_type=Template.ENDORSEMENT)
    )
    request = ilb_admin_client.get(reverse("login-required-select2-view"))
    qs = widget.filter_queryset(request=request, term=term)
    assert qs.count() == count
