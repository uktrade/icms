from django.utils import timezone


def activation_management_form_data():
    """Return form data required for viewflow task executions to post with
       test client."""
    return {"_viewflow_activation-started": timezone.now().strftime("%d-%b-%Y %H:%M:%S")}
