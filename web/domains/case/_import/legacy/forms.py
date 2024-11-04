from web.domains.case._import.forms import ChecklistBaseForm
from web.models import OPTChecklist, TextilesChecklist


class OPTChecklistForm(ChecklistBaseForm):
    class Meta:
        model = OPTChecklist

        fields = (
            "operator_requests_submitted",
            "authority_to_issue",
        ) + tuple(f for f in ChecklistBaseForm.Meta.fields if f != "endorsements_listed")


class OPTChecklistOptionalForm(OPTChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class TextilesChecklistForm(ChecklistBaseForm):
    class Meta:
        model = TextilesChecklist
        fields = ("within_maximum_amount_limit",) + ChecklistBaseForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["within_maximum_amount_limit"].required = True


class TextilesChecklistOptionalForm(TextilesChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False
