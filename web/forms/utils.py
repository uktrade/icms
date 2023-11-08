import re


def clean_postcode(postcode: str) -> str:
    return re.sub(r"\s+", "", postcode).upper()


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
