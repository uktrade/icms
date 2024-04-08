from django.apps import AppConfig


class WebConfig(AppConfig):
    name = "web"

    def ready(self) -> None:
        from django.db.models import Field

        from web.models.lookups import ILike

        Field.register_lookup(ILike)
