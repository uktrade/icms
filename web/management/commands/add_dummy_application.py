from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.commodity.models import Commodity
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.flow.models import Task
from web.models import ImportApplicationType


class Command(BaseCommand):
    help = """Add dummy application. For development use only."""

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            raise CommandError("DEBUG flag is not set, refusing to run!")

        user = User.objects.get(username="admin")
        importer = Importer.objects.get(name="Dummy importer")
        office = Office.objects.filter(postcode="BT12 5QB").first()

        app_type = ImportApplicationType.objects.get(type=ImportApplicationType.Types.WOOD_QUOTA)
        model_class = WoodQuotaApplication

        application = model_class()
        application.importer = importer
        application.importer_office = office
        application.process_type = model_class.PROCESS_TYPE
        application.created_by = user
        application.last_updated_by = user
        application.submitted_by = user
        application.application_type = app_type

        application.contact = user
        application.shipping_year = 2022
        application.exporter_name = "dummy name"
        application.exporter_address = "dummy address"
        application.exporter_vat_nr = "dummy VAT"
        application.commodity = Commodity.objects.get(is_active=True, commodity_code="4403211000")
        application.goods_description = "dummy description"
        application.goods_qty = 42.00
        application.goods_unit = "cubic metres"

        application.save()

        Task.objects.create(process=application, task_type=Task.TaskType.PREPARE, owner=user)

        self.stdout.write("Created dummy application")
