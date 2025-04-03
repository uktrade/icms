from web.models import NuclearMaterialEmail, SanctionEmail

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
                email=f"sanction-{i}@example.com",  # /PS-IGNORE
                is_active=is_active,
            )
            for i, (name, is_active) in enumerate(sanction_email_data)
        ]
    )


def add_nuclear_material_data():
    NuclearMaterialEmail.objects.bulk_create(
        [
            NuclearMaterialEmail(
                name=name,
                email=f"nuclear-material-{i}@example.com",  # /PS-IGNORE
                is_active=is_active,
            )
            for i, (name, is_active) in enumerate(
                [
                    ("Nuclear first contact", True),
                    ("Nuclear second contact", True),
                    ("Nuclear deactivated contact", False),
                ]
            )
        ]
    )
