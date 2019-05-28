from django.core.serializers.json import DjangoJSONEncoder
from django.forms.formsets import BaseFormSet

import json


def forms_valid(forms):
    for name, form in forms.items():
        if not form.is_valid():
            return False

    return True


def save_forms(forms):
    """
    Invoces save() method on all given forms to save changes to db
    """
    for key, form in forms.items():
        form.save()


def save_forms_to_session(request, forms):
    """
    Saves forms given as dict object to session using dictionary keys as keys
    """
    for name, form in forms.items():
        form.is_valid()  # Call is_valid to make sure cleaned_data is populated
        if not isinstance(form, BaseFormSet):
            request.session[name] = form.serialize()
        else:
            forms_data = []
            for f in form.forms:
                forms_data.append(f.data_dict())
            request.session[name] = json.dumps(
                forms_data, cls=DjangoJSONEncoder)


def remove_from_session(request, key):
    if request.POST:
        data = request.session.pop(key)
        if data:
            return json.loads(data)

    return {}
