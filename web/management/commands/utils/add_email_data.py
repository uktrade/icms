from django.conf import settings

from web.mail.constants import EmailTypes
from web.models import EmailTemplate, Template

EMAIL_TEMPLATES = [
    (EmailTypes.ACCESS_REQUEST, "6d20993f-7e9f-49b5-8c74-28654e6e84d0"),
    (EmailTypes.ACCESS_REQUEST_CLOSED, "956b148a-796c-4052-b7dd-7bbfb51cc049"),  # /PS-IGNORE
    (
        EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
        "61320f80-36ec-4bdf-97f7-68bf3d9f1d9c",  # /PS-IGNORE
    ),
    (EmailTypes.APPLICATION_COMPLETE, "68b93697-95db-4e95-a00f-5106489fd264"),  # /PS-IGNORE
    (
        EmailTypes.APPLICATION_EXTENSION_COMPLETE,
        "cdabbddd-5c80-44a4-ad7c-5f9624325d66",  # /PS-IGNORE
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
    (EmailTypes.APPLICATION_UPDATE_WITHDRAWN, "67924e6b-299c-415b-a654-095ab662b159"),  # /PS-IGNORE
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
    (EmailTypes.CASE_EMAIL_WITH_DOCUMENTS, "d208a30a-f03d-447a-89cf-c29f192b3cc4"),  # /PS-IGNORE
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

APPLICATION_UPDATE_IMPORTER_BODY = f"""Dear [[IMPORTER_NAME]]

You need to update your application with the following information for Import Licencing Branch (ILB) to process your application.
[DESCRIBE WHAT UPDATES ARE NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT]

Your application will not be processed further until you submit these updates.

The application will be closed if the requested updates are not received within 1 working day of this email.

Contact {settings.ILB_CONTACT_EMAIL} if you have any questions about your application.

Include case reference number [[CASE_REFERENCE]] in your email, so we know which application you are contacting us about.

Yours sincerely,

[[CASE_OFFICER_NAME]]
"""

APPLICATION_UPDATE_EXPORTER_BODY = f"""Dear [[EXPORTER_NAME]]

You need to update your application with the following information for the Import Licencing Branch (ILB) to process your application.
[DESCRIBE WHAT UPDATES ARE NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT].

Select the responsible person statement if you have placed the product on the EU market. This only applies to cosmetics. [DELETE IF NOT APPLICABLE]

The application will not be processed further until you submit the updates.

The application will be closed if the requested updates are not received within 1 working day of this email.

Contact {settings.ILB_GSI_CONTACT_EMAIL} if you have any questions about your application.
Include the case reference number [[CASE_REFERENCE]] in your email, so we know which application you are contacting us about.

Yours sincerely,

[[CASE_OFFICER_NAME]]
"""

BEIS_EMAIL_BODY = """Dear colleagues

[[CASE_REFERENCE]

We have received a [[APPLICATION_TYPE]] application from:

Exporter details:
[[EXPORTER_NAME]]
[[EXPORTER_ADDRESS]]

Please review and advise whether Import Licencing Branch can issue a GMP certificate for this request.

Manufacturer:
[[MANUFACTURER_NAME]]
[[MANUFACTURER_ADDRESS]]
[[MANUFACTURER_POSTCODE]]

Responsible person:
[[RESPONSIBLE_PERSON_NAME]]
[[RESPONSIBLE_PERSON_ADDRESS]]
[[RESPONSIBLE_PERSON_POSTCODE]]

Name of brand:
[[BRAND_NAME]]

Yours sincerely

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]
"""

FIREARMS_CONSTABULARY_BODY = """Dear colleagues

We have received an import licence application from:
[[IMPORTER_NAME]]
[[IMPORTER_ADDRESS]]

The application is for:
[[GOODS_DESCRIPTION]]

[DELETE BELOW AS APPLICABLE]

Grateful if the Police can advise on the validity of the RFD/Firearms/Shotgun Certificate, and whether
 there are any objections to the issuing of the import licence.

Grateful if the Police can validate the RFD / and Section 1 and 2 authority/authorities on the applicants apply for an import licence.

Grateful if the Home Office can validate the Section 5 authority on the applicants apply for an import licence.

The Home Office have validated the Section 5 authority on the applicants apply for an import licence. (Delete if not Section 5)

Grateful if you can check the attached deactivation certificate and advise as to whether or not it is valid and matches your records.
(DELETE IF NOT DEACTIVATED)

The import licence will not be issued until your response to this e-mail has been received.

Yours sincerely

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]
"""

IMA_RFI_BODY = f"""Dear [[IMPORTER_NAME]],

You need to provide some more information for Import Licencing Branch (ILB) to process your application.
[DESCRIBE WHAT INFORMATION OR CLARIFICATION IS NEEDED. INCLUDE SUGGESTIONS IF RELEVANT]
 regarding [DESCRIBE WHAT FURTHER INFORMATION IS NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT].

Your application will not be processed further until you respond to this request.

The application will be closed if the requested response is not received within 1 working day of this email.

Contact {settings.ILB_GSI_CONTACT_EMAIL} if you have any questions about your application.

Include case reference number [[CASE_REFERENCE]] in your email, so we know which application you are contacting us about.

Yours sincerely,

[[CASE_OFFICER_NAME]]
"""

CA_RFI_BODY = f"""Dear [[EXPORTER_NAME]],

Some more information is needed for the Import Licencing Branch (ILB) to process your application.
[DESCRIBE WHAT INFORMATION OR CLARIFICATION IS NEEDED. INCLUDE SUGGESTIONS IF RELEVANT].

Your application will not be processed further until you respond to this request.

The application will be closed if the requested response is not received 1 working day of this email.

Contact {settings.ILB_GSI_CONTACT_EMAIL} if you have any questions about your application.

Include case reference number [[CASE_REFERENCE]] in your email, so we know which application you are contacting us about.

Yours sincerely,

[[CASE_OFFICER_NAME]]
"""

HSE_BODY = """Dear colleagues

[[CASE_REFERENCE]]

We have received a [[APPLICATION_TYPE]] application from:
[[EXPORTER_NAME]]
[[EXPORTER_ADDRESS]]
[[CONTACT_EMAIL]]

The application is for countries:

[[CERT_COUNTRIES]]

The application is for biocidal products:

[[SELECTED_PRODUCTS]]

We would be grateful for your guidance on the items listed.

Yours sincerely,

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]
"""

IAR_RFI_BODY = f"""Dear [[REQUESTER_NAME]],

Some more information is needed for the Import Licencing Branch (ILB) to process your request to access apply for an import licence or export certificate.
[DESCRIBE WHAT INFORMATION OR CLARIFICATION IS NEEDED. INCLUDE SUGGESTIONS IF RELEVANT].

Use this link [Link to case in apply for an import licence or export certificate] to your access request in apply for an import licence or export certificate.

Contact {settings.ILB_GSI_CONTACT_EMAIL} if you have any questions.
Include the case reference number [[REQUEST_REFERENCE]] in your email

Yours sincerely,

[[CURRENT_USER_NAME]]
"""

PUBLISH_MAILSHOT_BODY = """Dear [[FIRST_NAME]],

A new mailshot has been published.

Yours sincerely,

Import Licencing Branch
"""

RETRACT_MAILSHOT_BODY = """Dear [[FIRST_NAME]],

A published mailshot has been retracted.

Yours sincerely,

Import Licencing Branch
"""

SANCTIONS_BODY = """Dear colleagues

We have received an import licence application from:
[[IMPORTER_NAME]]
[[IMPORTER_ADDRESS]]

The application is for:

[[GOODS_DESCRIPTION]]

Yours sincerely,

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]
"""


EMAIL_CONTENT = [
    (
        Template.Codes.IMA_APP_UPDATE,
        "Request for updates to your application [[CASE_REFERENCE]]",
        APPLICATION_UPDATE_IMPORTER_BODY,
    ),
    (
        Template.Codes.CA_APPLICATION_UPDATE_EMAIL,
        "Request for updates to your application [[CASE_REFERENCE]]",
        APPLICATION_UPDATE_EXPORTER_BODY,
    ),
    (
        Template.Codes.CA_BEIS_EMAIL,
        "Good manufacturing practice (GMP) application enquiry [[CASE_REFERENCE]]",
        BEIS_EMAIL_BODY,
    ),
    (
        Template.Codes.IMA_CONSTAB_EMAIL,
        "Import licence Registered Firearms Dealer (RFD) enquiry [[CASE_REFERENCE]]",
        FIREARMS_CONSTABULARY_BODY,
    ),
    (Template.Codes.IMA_RFI, "Request for more information [[CASE_REFERENCE]]", IMA_RFI_BODY),
    (Template.Codes.CA_RFI_EMAIL, "Request for more information [[CASE_REFERENCE]]", CA_RFI_BODY),
    (Template.Codes.CA_HSE_EMAIL, "Biocidal product enquiry [[CASE_REFERENCE]]", HSE_BODY),
    (
        Template.Codes.IAR_RFI_EMAIL,
        "Request for more information [[REQUEST_REFERENCE]]",
        IAR_RFI_BODY,
    ),
    (Template.Codes.PUBLISH_MAILSHOT, "New mailshot", PUBLISH_MAILSHOT_BODY),
    (Template.Codes.RETRACT_MAILSHOT, "Retracted mailshot", RETRACT_MAILSHOT_BODY),
    (
        Template.Codes.IMA_SANCTIONS_EMAIL,
        "Import sanctions and adhoc licence [[CASE_REFERENCE]]",
        SANCTIONS_BODY,
    ),
]


def update_database_email_templates():
    for template_code, subject, body in EMAIL_CONTENT:
        template = Template.objects.get(template_code=template_code)
        template.template_title = subject
        template.template_content = body
        template.save(update_fields=["template_title", "template_content", "start_datetime"])


def archive_database_email_templates():
    templates = [
        Template.Codes.STOP_CASE,
        Template.Codes.CASE_REOPEN,
        Template.Codes.LICENCE_REVOKE,
        Template.Codes.CERTIFICATE_REVOKE,
    ]
    Template.objects.filter(template_code__in=templates).update(is_active=False)


def add_gov_notify_templates():
    EmailTemplate.objects.bulk_create(
        [
            EmailTemplate(name=name, gov_notify_template_id=gov_notify_template_id)
            for name, gov_notify_template_id in EMAIL_TEMPLATES
        ]
    )


def add_user_management_email_templates():
    Template.objects.create(
        template_title="Your [[PLATFORM]] account has been deactivated",
        template_name="User account deactivated",
        template_code=Template.Codes.DEACTIVATE_USER,
        template_type="EMAIL_TEMPLATE",
        application_domain="UM",
        template_content="""Dear [[FIRST_NAME]],

Your [[PLATFORM]] account has been deactivated.

Contact [[CASE_OFFICER_EMAIL]] if you have any questions.

Yours sincerely

Import Licensing Branch
""",
    )
    Template.objects.create(
        template_title="Your [[PLATFORM]] account has been reactivated",
        template_name="User account reactivated",
        template_code=Template.Codes.REACTIVATE_USER,
        template_type="EMAIL_TEMPLATE",
        application_domain="UM",
        template_content="""Dear [[FIRST_NAME]],

Welcome back to [[PLATFORM]].

Your account has been reactivated.

You can now sign in to your account here [[PLATFORM_LINK]]

Contact [[CASE_OFFICER_EMAIL]] if you have any questions.

Yours sincerely,

Import Licencing Branch
""",
    )
