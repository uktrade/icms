from web.mail.constants import EmailTypes
from web.models import EmailTemplate

templates = [
    (EmailTypes.ACCESS_REQUEST, "d8905fee-1f7d-48dc-bc11-aee71c130b3e"),
    (EmailTypes.ACCESS_REQUEST_CLOSED, "6cfc34cc-7e61-4f30-b73c-e7f5d5ae95ae"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_COMPLETE, "2e03bc8e-1d57-404d-ba53-0fbf00316a4d"),  # /PS-IGNORE
    (
        EmailTypes.APPLICATION_EXTENSION_COMPLETE,
        "a91fc429-f6d6-472c-88de-e86bb4debcab",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_COMPLETE,
        "dc5ced0f-53fb-45b2-9284-b9b241aa4696",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_STOPPED,
        "13b68bc7-99a5-4402-8794-e49992da54a9",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_REFUSED,
        "347cbb92-03d2-495e-a8f7-f3c94ea2bf45",  # /PS-IGNORE
    ),
    (
        EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "812e532c-b617-4cf9-917d-01f49ff10964",  # /PS-IGNORE
    ),
    (
        EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "01d616e8-c2df-4fb2-aa6d-4feeb3c38eea",  # /PS-IGNORE
    ),
]


def add_email_gov_notify_templates():
    EmailTemplate.objects.bulk_create(
        [
            EmailTemplate(name=name, gov_notify_template_id=gov_notify_template_id)
            for name, gov_notify_template_id in templates
        ]
    )
