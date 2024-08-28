from web.mail.constants import EmailTypes
from web.models import EmailTemplate


def test_all_name_are_valid(db):
    for name in EmailTypes:
        EmailTemplate.objects.get(name=name)
