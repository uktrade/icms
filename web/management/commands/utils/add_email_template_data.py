from django.conf import settings

from web.mail.constants import EmailTypes
from web.models import EmailTemplate

v1_templates = [
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


v2_templates = [
    (EmailTypes.ACCESS_REQUEST, "6d20993f-7e9f-49b5-8c74-28654e6e84d0"),
    (EmailTypes.ACCESS_REQUEST_CLOSED, "956b148a-796c-4052-b7dd-7bbfb51cc049"),  # /PS-IGNORE
    (
        EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
        "61320f80-36ec-4bdf-97f7-68bf3d9f1d9c",  # /PS-IGNORE
    ),
    (EmailTypes.APPLICATION_COMPLETE, "2e03bc8e-1d57-404d-ba53-0fbf00316a4d"),  # /PS-IGNORE
    (
        EmailTypes.APPLICATION_EXTENSION_COMPLETE,
        "68b93697-95db-4e95-a00f-5106489fd264",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_COMPLETE,
        "428fc248-d668-4f46-9522-b60b88142e36",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED,
        "4083d2ae-efd9-420c-b159-29cbfa9bf1b6",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED,
        "63d2228e-27b4-4810-957c-75ba5baae463",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED,
        "9bfe0641-bc19-4ac1-b2d8-8ec7b4011fe0",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED,
        "7b272d9b-ccc0-4ef4-8a7a-e9d7cb4eceb5",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED,
        "f9f04289-fd0a-46ed-b521-a2cd2402ca83",  # /PS-IGNORE
    ),
    (EmailTypes.APPLICATION_STOPPED, "bac90963-7e9f-4e67-8c16-99ff905b3e02"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REFUSED, "02b558e7-2902-429d-b5de-c8dac83da7b7"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REASSIGNED, "99c3103b-8bf5-470f-8624-6b7791aedb32"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_REOPENED, "179ff4fe-236a-4718-befc-56cd2c977d0c"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_UPDATE, "960f3436-a190-4f65-9e05-1fef479a7a0b"),  # /PS-IGNORE
    (EmailTypes.APPLICATION_UPDATE_RESPONSE, "f6c09508-bcc8-49e7-be2c-102d32f153ed"),  # /PS-IGNORE
    (
        EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "267b4a1c-7f61-4e76-becd-286b5252b0e7",  # /PS-IGNORE
    ),
    (
        EmailTypes.FIREARMS_SUPPLEMENTARY_REPORT,
        "55fc0197-94c8-4125-8784-1b637faa15fb",  # /PS-IGNORE
    ),
    (
        EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
        "09b7654d-26b4-49d7-967d-ca457f5f1f3a",  # /PS-IGNORE
    ),
    (EmailTypes.WITHDRAWAL_ACCEPTED, "93b464af-a0a0-479d-b69d-4ec5c6ef6966"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_CANCELLED, "8d18435a-6c8a-41ca-aa98-64f99438076e"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_OPENED, "fd0e9524-bcb8-4d3d-8fe0-09910bb2f6a2"),  # /PS-IGNORE
    (EmailTypes.WITHDRAWAL_REJECTED, "59cee5db-9f9f-4966-b46a-07743b3e9e72"),  # /PS-IGNORE
    (EmailTypes.CASE_EMAIL, "3e68fc83-ad05-4c32-826a-d950ce2dfa32"),  # /PS-IGNORE
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST,
        "7aa33950-19ac-4d1c-ad7b-e0a1b493914f",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED,
        "5e198272-1ae5-4dff-98bc-2f2f52142ee2",  # /PS-IGNORE
    ),
    (
        EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
        "c4e9e6fc-c48d-4eac-a556-a0bc9026ad58",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST,
        "683c2b2e-352c-493d-ab7f-aa08c118afb2",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED,
        "b8fa5a85-bdbf-4dcf-8eec-e23bc5c805fa",  # /PS-IGNORE
    ),
    (
        EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
        "853224f4-fb63-4d83-9a56-ee78f39ef636",  # /PS-IGNORE
    ),
    (EmailTypes.LICENCE_REVOKED, "642e8280-a6f0-4e45-89db-4cf37f9cb446"),  # /PS-IGNORE
    (EmailTypes.CERTIFICATE_REVOKED, "eb8c610c-35c9-4a47-aa5d-5bfa465b5156"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_ARCHIVED, "845c64ba-43ca-4145-a7e3-a54d1f565991"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_EXPIRING_SECTION_5, "fe064185-33ff-44c0-bef9-6e0763121974"),  # /PS-IGNORE
    (EmailTypes.AUTHORITY_EXPIRING_FIREARMS, "e1a3439c-bd1b-4553-a924-4a9db2cd6420"),  # /PS-IGNORE
    (EmailTypes.MAILSHOT, "ecf686cf-b312-4a95-b984-246fdfdbd03a"),  # /PS-IGNORE
    (EmailTypes.RETRACT_MAILSHOT, "811448a4-5cdc-4258-bd8b-734d67f6624c"),  # /PS-IGNORE
    (
        EmailTypes.CONSTABULARY_DEACTIVATED_FIREARMS,
        "e8602eab-2312-4e18-8a8e-b0d99b569bb8",  # /PS-IGNORE
    ),
    (EmailTypes.NEW_USER_WELCOME, "2880f0ec-4f33-45a8-b98c-ff383dfdb577"),  # /PS-IGNORE
    (EmailTypes.ORG_CONTACT_INVITE, "974d789b-7881-4a68-b262-c958c74567b8"),  # /PS-IGNORE
]


def add_email_gov_notify_templates():
    if settings.FEATURE_FLAG_V2_EMAIL_CONTENT:
        templates = v2_templates
    else:
        templates = v1_templates

    EmailTemplate.objects.bulk_create(
        [
            EmailTemplate(name=name, gov_notify_template_id=gov_notify_template_id)
            for name, gov_notify_template_id in templates
        ]
    )
