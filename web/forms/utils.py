import json

import structlog as logging
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.formsets import BaseFormSet

logger = logging.getLogger(__name__)


def forms_valid(forms):
    for name, form in forms.items():
        if not form.is_valid():
            return False

    return True


def save_forms(forms):
    """
    Invokes save() method on all given forms to save changes to db
    """
    for key, form in forms.items():
        form.save()


def add_to_session(request, key, value):
    logger.debug('Adding "%s" to session:\n%s', key, value)
    request.session[key] = json.dumps(value, cls=DjangoJSONEncoder)


def save_forms_to_session(request, forms):
    """
    Saves forms given as dict object to session using dictionary keys as keys
    """
    for key, form in forms.items():
        if not isinstance(form, BaseFormSet):
            add_to_session(request, key, form.data)
        else:  # Formset
            forms_data = []
            for f in form.forms:
                forms_data.append(f.data)
            add_to_session(request, key, forms_data)


def remove_from_session(request, key):
    logger.debug('Removing "%s" from session', key)
    if request.POST:
        data = request.session.pop(key)
        if data:
            return json.loads(data)

    return {}
