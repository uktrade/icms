from django.forms import (inlineformset_factory, BaseInlineFormSet)
from web.models import (PhoneNumber, User)
from .forms import (PhoneNumberForm)


class PhoneNumbersFormSet(BaseInlineFormSet):
    def full_clean(self):
        super().full_clean()  # Populates self._non_form_errors
        for e in self._non_form_errors.as_data():
            if e.code == 'too_few_forms':
                e.message = 'Please submit at least one phone number'
            elif e.code == 'too_many_forms':
                e.message = 'You can not submit more than five phone numbers'


def new_user_phones_formset(request):
    return inlineformset_factory(
        User,
        PhoneNumber,
        form=PhoneNumberForm,
        formset=PhoneNumbersFormSet,
        extra=0,
        validate_max=True,
        max_num=5,
        can_delete=True,
        validate_min=True,
        min_num=1)(
            request.POST or None, prefix='phone', instance=request.user)
