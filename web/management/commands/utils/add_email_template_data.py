from web.mail.constants import EmailTypes
from web.models import EmailTemplate

templates = [
    (EmailTypes.ACCESS_REQUEST, "d8905fee-1f7d-48dc-bc11-aee71c130b3e"),
    (EmailTypes.ACCESS_REQUEST_CLOSED, "6cfc34cc-7e61-4f30-b73c-e7f5d5ae95ae"),  # /PS-IGNORE
    (
        EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
        "387f3709-2c65-4352-b30e-0345f7d460d1",  # /PS-IGNORE
    ),
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
        EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED,
        "827b7070-62ea-4325-8fb3-e35e0d554c47",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED,
        "35c6d0b6-2030-4d31-9ea8-c35682a5876b",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED,
        "e9e519ab-f5d0-41b5-90da-d5af6da23a38",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED,
        "568f5e0e-8b28-44de-9a25-f5535306b7b4",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED,
        "a1d8ed94-2d04-4b97-9380-fc331b94f700",  # /PS-IGNORE
    ),
    (EmailTypes.APPLICATION_STOPPED, "13b68bc7-99a5-4402-8794-e49992da54a9"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REFUSED, "347cbb92-03d2-495e-a8f7-f3c94ea2bf45"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REASSIGNED, "43b35460-caa4-4080-a350-fabd30c913f6"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REOPENED, "cab2ef22-def1-47f7-b76e-76ed77eb47bb"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_UPDATE, "6eae5393-ab3d-4387-8761-9562a151816a"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_UPDATE_RESPONSE, "8622ebd7-a597-473c-8890-1bc04138cbfa"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_UPDATE_WITHDRAWN, "67924e6b-299c-415b-a654-095ab662b159"),  # /PS-IGNORE
    (
        EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "812e532c-b617-4cf9-917d-01f49ff10964",  # /PS-IGNORE
    ),
    (
        EmailTypes.FIREARMS_SUPPLEMENTARY_REPORT,
        "f7ae3f06-fad2-4835-99e1-c573b4478bc4",  # /PS-IGNORE
    ),
    (
        EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "01d616e8-c2df-4fb2-aa6d-4feeb3c38eea",  # /PS-IGNORE
    ),
    (EmailTypes.WITHDRAWAL_ACCEPTED, "ea1a9341-8608-4af8-8eec-9c40beddd978"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_CANCELLED, "0d6060c0-519d-4404-9d22-e510ff355186"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_OPENED, "e3499a7c-ad6e-4ceb-bed3-d0a9a137f6a9"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_REJECTED, "ffbed03f-bebc-4f87-a602-e83df0c72890"),  # /PS-IGNORE
    (EmailTypes.CASE_EMAIL, "657aa427-8dda-496a-b933-fa7be10f16fd"),  # /PS-IGNORE
    (EmailTypes.CASE_EMAIL_WITH_DOCUMENTS, "d208a30a-f03d-447a-89cf-c29f192b3cc4"),  # /PS-IGNORE
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST,
        "fc26629c-51bd-427a-bd7d-81322f669f65",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED,
        "da80be69-ea12-4529-95ed-b79c7e9b1f52",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
        "21851ee5-5541-4c01-b961-caec57d8dfda",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST,
        "08f3e82d-2246-4dff-9784-369c601bcf11",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED,
        "3dda4e25-cd32-43ef-a038-9fd78beb1087",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
        "2cadfb82-0888-4c43-bc58-ffce9b6055d5",  # /PS-IGNORE
    ),
    (EmailTypes.LICENCE_REVOKED, "fd150e67-ac38-47e8-b7fd-b0fdd8e131b2"),  # /PS-IGNORE
    (EmailTypes.CERTIFICATE_REVOKED, "c82e2599-d8fb-4cbe-9bf5-ef92ab2b54cd"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_ARCHIVED, "69f08523-3f45-40b0-bfcb-c7aac3fca547"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_EXPIRING_SECTION_5, "a42891e5-5bad-4911-bdbe-af71737e8756"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_EXPIRING_FIREARMS, "750157e0-36a8-4f2c-9e6e-d37d11a41eff"),  # /PS-IGNORE
    (EmailTypes.MAILSHOT, "0bd18673-37f1-4fd3-9103-ae156cd95e88"),  # /PS-IGNORE
    (EmailTypes.RETRACT_MAILSHOT, "5646a26a-f855-4826-a3b4-f1ca588ba309"),  # /PS-IGNORE
    (
        EmailTypes.CONSTABULARY_DEACTIVATED_FIREARMS,
        "fc56ddb3-b918-480d-b209-82ef99733ed2",  # /PS-IGNORE
    ),
    (EmailTypes.NEW_USER_WELCOME, "53cdc837-947f-408d-a87b-ef5664e48617"),  # /PS-IGNORE
    (EmailTypes.ORG_CONTACT_INVITE, "cc80a541-2628-4bc2-99a5-4fba28dde123"),  # /PS-IGNORE
]


def add_email_gov_notify_templates():
    EmailTemplate.objects.bulk_create(
        [
            EmailTemplate(name=name, gov_notify_template_id=gov_notify_template_id)
            for name, gov_notify_template_id in templates
        ]
    )
