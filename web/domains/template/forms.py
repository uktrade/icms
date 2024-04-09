import re
from typing import Any

from django import forms
from django.db.models import Q, QuerySet
from django_filters import CharFilter, ChoiceFilter, FilterSet
from django_select2 import forms as s2forms

from web.domains.template.widgets import EndorsementTemplateWidget

from .context import CoverLetterTemplateContext
from .models import Template
from .utils import find_invalid_placeholders


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

    def clean_template_content(self):
        template_content = self.cleaned_data["template_content"]
        invalid_placeholders = find_invalid_placeholders(
            template_content, CoverLetterTemplateContext.valid_placeholders
        )
        if invalid_placeholders:
            self.add_error(
                "template_content",
                f"The following placeholders are invalid: {', '.join(invalid_placeholders)}",
            )

        return template_content


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
    template_name_title = CharFilter(
        method="filter_name_title", label="Template / Endorsement Name"
    )
    application_domain = ChoiceFilter(
        choices=Template.DOMAINS, lookup_expr="exact", label="Application Domain", empty_label="Any"
    )
    template_type = ChoiceFilter(
        choices=sorted(Template.TYPES),
        lookup_expr="exact",
        label="Template Type",
        empty_label="Any",
    )
    template_content = CharFilter(lookup_expr="icontains", label="Template Content")
    is_active = ChoiceFilter(choices=Template.STATUS, lookup_expr="exact", label="Template Status")

    class Meta:
        model = Template
        fields: list[Any] = []  # Django complains without fields set in the meta

    def filter_name_title(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Search templates by both template_name and template_title.

        template_title is used as the subject line for email templates, and users may want to search by that, but it's
        not necessary to have an additional search field just for template_title."""
        return queryset.filter(
            Q(template_name__icontains=value) | Q(template_title__icontains=value)
        )


class EndorsementUsageForm(forms.Form):
    def __init__(self, *args, application_type_pk=None, **kwargs):
        super().__init__(*args, **kwargs)

        if application_type_pk:
            self.fields["endorsement"].queryset = Template.objects.filter(
                template_type=Template.ENDORSEMENT
            ).exclude(endorsement_application_types=application_type_pk)

    endorsement = forms.ModelChoiceField(
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

    def clean_countries(self):
        countries = self.cleaned_data["countries"]

        # don't allow multiple non-archived translations for a given language;
        # how would the system know which one to use?

        query = Template.objects.filter(
            template_type=Template.CFS_DECLARATION_TRANSLATION, is_active=True
        )

        if self.instance.pk is not None:
            query = query.exclude(pk=self.instance.pk)

        already_translated = set(query.values_list("countries", flat=True))

        # list of country names that we need to error about
        errors = []

        for country in countries:
            if country.pk in already_translated:
                errors.append(country.name)

        if errors:
            errors_str = ", ".join(errors)

            raise forms.ValidationError(
                f"These countries already have the CFS Declaration translated: {errors_str}"
            )

        return countries

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

    class Meta:
        model = Template
        fields = ("template_name", "countries", "country_translation_set")
        widgets = {
            "countries": s2forms.Select2MultipleWidget,
        }

    def clean_countries(self):
        countries = self.cleaned_data["countries"]

        # don't allow multiple non-archived translations for a given language;
        # how would the system know which one to use?

        query = Template.objects.filter(
            template_type=Template.CFS_SCHEDULE_TRANSLATION, is_active=True
        )

        if self.instance.pk is not None:
            query = query.exclude(pk=self.instance.pk)

        already_translated = set(query.values_list("countries", flat=True))

        # list of country names that we need to error about
        errors = []

        for country in countries:
            if country.pk in already_translated:
                errors.append(country.name)

        if errors:
            errors_str = ", ".join(errors)

            raise forms.ValidationError(
                f"These countries already have the CFS Schedule translated: {errors_str}"
            )

        return countries

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.application_domain = Template.CERTIFICATE_APPLICATION
        instance.template_type = Template.CFS_SCHEDULE_TRANSLATION

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class CFSScheduleTranslationParagraphsForm(forms.Form):
    def __init__(self, english_paras, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.english_paras = english_paras

        for para in english_paras:
            self.fields[f"para_{para.name}"] = forms.CharField(
                label=para.content, widget=forms.Textarea
            )

    def clean(self):
        data = super().clean()

        # replacement patterns look like [[EXPORTER_NAME]]
        repl_re = re.compile(r"\[\[[A-Z_]+\]\]")

        for english_para in self.english_paras:
            name = f"para_{english_para.name}"
            orig = english_para.content

            translation = data.get(name)

            if translation is None:
                # all fields are required, so this is handled by django
                # automatically, no need to manually check all fields are
                # present
                continue

            orig_repls = set(repl_re.findall(orig))
            translation_repls = set(repl_re.findall(translation))

            missing = orig_repls - translation_repls
            if missing:
                missing_str = ", ".join(missing)
                self.add_error(name, f"The translation must include the fields {missing_str}")

            extra = translation_repls - orig_repls
            if extra:
                extra_str = ", ".join(extra)
                self.add_error(name, f"The translation contains invalid fields {extra_str}")

        return data
