from web.models import FirearmsAct


def add_firearms_act_data():
    # Add some Firearm acts (Copied from data migration)
    FirearmsAct.objects.bulk_create(
        [
            FirearmsAct(created_by_id=0, act=act)
            for act in [
                "Section 1 Firearms",
                "Section 1 Shotguns",
                "Section 2 Shotguns",
                "Section 1 Component Parts",
                "Section 1 Ammunition",
                "Expanding Ammunition 5(1A)(f)",
                "Suppressors",
            ]
        ]
    )
