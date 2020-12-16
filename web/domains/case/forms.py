from django.forms import ChoiceField, ClearableFileInput, FileField, ModelForm

from web.domains.case.models import CASE_NOTE_STATUSES, CaseNote


class CaseNoteForm(ModelForm):
    status = ChoiceField(choices=CASE_NOTE_STATUSES)
    files = FileField(
        required=False,
        label="Upload New Documents",
        widget=ClearableFileInput(attrs={"multiple": True, "onchange": "updateList()"}),
    )

    class Meta:
        model = CaseNote
        fields = ["status", "note", "files"]

    def clean(self):
        data = super().clean()
        data.pop("files", None)
        return data
