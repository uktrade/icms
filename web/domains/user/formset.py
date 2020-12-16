from django.forms import BaseInlineFormSet, ValidationError, inlineformset_factory

from web.models import AlternativeEmail, PersonalEmail, PhoneNumber, User

from .forms import AlternativeEmailsForm, PersonalEmailForm, PhoneNumberForm


class PhoneNumbersFormSet(BaseInlineFormSet):
    def full_clean(self):
        super().full_clean()  # Populates self._non_form_errors
        for e in self._non_form_errors.as_data():
            if e.code == "too_few_forms":
                e.message = "Please add at least one telephone number"


class PersonalEmailsFormSet(BaseInlineFormSet):
    def clean(self):
        # Don' validate unless each form is valid on its own
        if any(self.errors):
            return
        primary_count = 0
        for form in self.forms:
            if form.instance.is_primary:
                primary_count += 1

        if primary_count != 1:
            raise ValidationError(
                "There must be one and only one email address set as \
                Primary for portal notification."
            )

    def full_clean(self):
        super().full_clean()  # Populates self._non_form_errors
        for e in self._non_form_errors.as_data():
            if e.code == "too_few_forms":
                e.message = "Please add at least one email address"


class AlternativeEmailsFormset(BaseInlineFormSet):
    pass


def new_user_phones_formset(request, data=None, initial=None):
    return inlineformset_factory(
        User,
        PhoneNumber,
        form=PhoneNumberForm,
        formset=PhoneNumbersFormSet,
        extra=0,
        can_delete=True,
        validate_min=True,
        min_num=1,
    )(data, prefix="phone", initial=initial, instance=request.user)


def new_alternative_emails_formset(request, data=None, initial=None):
    return inlineformset_factory(
        User,
        AlternativeEmail,
        form=AlternativeEmailsForm,
        formset=AlternativeEmailsFormset,
        extra=0,
        can_delete=True,
    )(data, prefix="alternative_email", initial=initial, instance=request.user)


def new_personal_emails_formset(request, data=None, initial=None):
    return inlineformset_factory(
        User,
        PersonalEmail,
        form=PersonalEmailForm,
        formset=PersonalEmailsFormSet,
        extra=0,
        can_delete=True,
        validate_min=True,
        min_num=1,
    )(data, prefix="personal_email", initial=initial, instance=request.user)
