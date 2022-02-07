from web.models import SanctionEmail

sanction_email_data = [
    ("Sanction first contact", True),
    ("Sanction second contact", True),
    ("Sanction third contact", True),
    ("Sanction deactivated contact", False),
]


def add_sanction_data():
    SanctionEmail.objects.bulk_create(
        [
            SanctionEmail(
                name=name,
                email=f"sanction-{i}@example.com",
                is_active=is_active,
            )
            for i, (name, is_active) in enumerate(sanction_email_data)
        ]
    )
