from web.ecil.gds import forms as gds_forms
from web.models import User


class OneLoginNewUserUpdateForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = User
        fields = ("first_name", "last_name")
        labels = {
            "first_name": "First name",  # /PS-IGNORE
            "last_name": "Last name",  # /PS-IGNORE
        }
        # TODO: Add extra config for fomm fields (half width)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = True
