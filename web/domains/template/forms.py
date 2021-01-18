from django import forms
from django_filters import CharFilter, ChoiceFilter, FilterSet
from django_select2 import forms as s2forms

from web.domains.template.widgets import EndorsementTemplateWidget

from .models import Template


class DeclarationTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ("template_name", "template_content")
        labels = {
            "template_name": "Declaration Title",
            "template_content": "Declaration Text",
        }


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ("template_name", "template_title", "template_content")
        labels = {
            "template_name": "Email Template Name",
            "template_title": "Email Subject",
            "template_content": "Email Body",
        }


class EndorsementTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ("template_name", "template_content")
        labels = {
            "template_name": "Endorsement Name",
            "template_content": "Endorsement Text",
        }


class LetterTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ("template_name", "template_content")
        labels = {
            "template_name": "Letter Template Name",
            "template_content": "Letter",
        }
        widgets = {"template_content": forms.Textarea(attrs={"lang": "html"})}


class LetterFragmentForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ("template_name", "template_content")
        labels = {
            "template_name": "Fragment Name",
            "template_content": "Fragment Text",
        }
        widgets = {"template_content": forms.Textarea(attrs={"lang": "html"})}


class TemplatesFilter(FilterSet):
    # Fields of the model that can be filtered
    template_name = CharFilter(lookup_expr="icontains", label="Template Name")
    application_domain = ChoiceFilter(
        choices=Template.DOMAINS, lookup_expr="exact", label="Application Domain"
    )
    template_type = ChoiceFilter(
        choices=sorted(Template.TYPES), lookup_expr="exact", label="Template Type"
    )
    template_title = CharFilter(lookup_expr="icontains", label="Template Title")
    template_content = CharFilter(lookup_expr="icontains", label="Template Content")
    is_active = ChoiceFilter(choices=Template.STATUS, lookup_expr="exact", label="Template Status")

    class Meta:
        model = Template
        fields = []  # Django complains without fields set in the meta


class EndorsementUsageForm(forms.Form):
    linked_endorsement = forms.ModelChoiceField(
        label="",
        help_text="""
            Search an endorsement to add. Endorsements returned are matched against
            name and content.
        """,
        queryset=Template.objects.filter(template_type=Template.ENDORSEMENT),
        widget=EndorsementTemplateWidget,
    )


class CFSDeclarationTranslationForm(forms.ModelForm):
    template_name = forms.CharField(label="CFS Declaration Translation Name")
    template_content = forms.CharField(label="Translation", widget=forms.Textarea)

    class Meta:
        model = Template
        fields = ("template_name", "countries", "template_content")
        widgets = {
            "countries": s2forms.Select2MultipleWidget,
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.application_domain = Template.CERTIFICATE_APPLICATION
        instance.template_type = Template.CFS_DECLARATION_TRANSLATION
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class CFSScheduleTranslationForm(forms.ModelForm):
    template_name = forms.CharField(label="CFS Schedule Translation Name")

    # TODO: limit countries/country_translation_set by not allowing duplicates
    # of stuff already in DB. either do it in the query or in clean

    class Meta:
        model = Template
        fields = ("template_name", "countries", "country_translation_set")
        widgets = {
            "countries": s2forms.Select2MultipleWidget,
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.application_domain = Template.CERTIFICATE_APPLICATION
        instance.template_type = Template.CFS_SCHEDULE_TRANSLATION

        if commit:
            instance.save()
            self.save_m2m()

        return instance
