import datetime
from dataclasses import dataclass
from uuid import uuid4

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.decorators import method_decorator

from web.domains.case._import.forms import CreateWoodQuotaApplicationForm
from web.domains.case._import.views import _get_paper_licence_only
from web.domains.case._import.wood.forms import (
    PrepareWoodQuotaForm,
    WoodQuotaChecklistForm,
)
from web.domains.case._import.wood.models import (
    WOOD_UNIT_CHOICES,
    WoodQuotaApplication,
    WoodQuotaChecklist,
)
from web.domains.case.utils import get_application_current_task
from web.domains.commodity.models import Commodity
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.flow.models import Task
from web.middleware.common import ICMSMiddlewareContext
from web.models import ImportApplicationType
from web.models.shared import YesNoNAChoices


@method_decorator(transaction.atomic, name="_create_in_progress_app")
@method_decorator(transaction.atomic, name="_create_submitted_wood_app")
@method_decorator(transaction.atomic, name="_create_managed_wood_app")
class Command(BaseCommand):
    """Example usage:

    export DJANGO_SETTINGS_MODULE=config.settings.local
    docker-compose run --rm web python ./manage.py add_dummy_application \
      --in-progress 0 \
      --submitted 0 \
      --managed 10
    """

    help = """Add dummy applications. For development use only."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--in-progress",
            help="Number of in-progress apps to create (Defaults to 1)",
            default=3,
            type=int,
        )

        parser.add_argument(
            "--submitted",
            help="Number of submitted apps to create (Defaults to 1)",
            default=1,
            type=int,
        )

        parser.add_argument(
            "--managed",
            help="Number of managed apps to create (Defaults to 1)",
            default=1,
            type=int,
        )

    def handle(self, *args, in_progress: int, submitted: int, managed: int, **options):
        if not settings.DEBUG:
            raise CommandError("DEBUG flag is not set, refusing to run!")

        self.ilb_admin_user = User.objects.get(username="ilb_admin")
        self.importer_user = User.objects.get(username="importer_user")
        self.importer = Importer.objects.get(name="Dummy importer")
        self.importer_office = self.importer.offices.get(postcode="BT12 5QB")
        self.today = datetime.date.today()

        try:
            for _ in range(in_progress):
                in_progress_app = self._create_in_progress_app()
                self.success_msg(f"Created in progress application: {in_progress_app!r}")

            for _ in range(submitted):
                submitted_app = self._create_submitted_wood_app()
                self.success_msg(f"Created submitted application: {submitted_app!r}")

            for _ in range(managed):
                managed_app = self._create_managed_wood_app()
                self.success_msg(f"Created managed application: {managed_app!r}")

        except CommandError as e:
            self.error_msg(f"Failed with the following reason: {e}")

    def _create_in_progress_app(self):
        app_type = ImportApplicationType.objects.get(type=ImportApplicationType.Types.WOOD_QUOTA)
        model_class = WoodQuotaApplication

        # Create the application
        form = CreateWoodQuotaApplicationForm(
            data={
                "importer": str(self.importer.pk),
                "importer_office": str(self.importer_office.pk),
            },
            user=self.importer_user,
        )

        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.agent = form.cleaned_data["agent"]
            application.agent_office = form.cleaned_data["agent_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = self.importer_user
            application.last_updated_by = self.importer_user
            application.application_type = app_type
            application.issue_paper_licence_only = _get_paper_licence_only(app_type)

            application.save()
            Task.objects.create(
                process=application, task_type=Task.TaskType.PREPARE, owner=self.importer_user
            )

        else:
            raise CommandError(f"Can't create application: {form.errors}")

        # Fill out the main form
        form = PrepareWoodQuotaForm(
            instance=application,
            data={
                "contact": self.importer_user.pk,
                "applicant_reference": f"Application reference: {self.today}-{uuid4()}",
                "shipping_year": self.today.year,
                "exporter_name": "dummy name",
                "exporter_address": "Dummy exporter address",
                "exporter_vat_nr": "Dummy exporter vat number",
                "commodity": Commodity.objects.get(is_active=True, commodity_code="4403211000").pk,
                "goods_description": "Dummy Description",
                "goods_qty": 42,
                "goods_unit": WOOD_UNIT_CHOICES[0][0],
                "additional_comments": "No additional comments",
            },
        )

        if form.is_valid():
            form.save()
        else:
            raise CommandError(f"Can't populate the edit wood form: {form.errors}")

        return application

    @transaction.atomic()
    def _create_submitted_wood_app(self):
        application = self._create_in_progress_app()
        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        @dataclass
        class DummyRequest:
            icms: ICMSMiddlewareContext
            user: User

        req = DummyRequest(ICMSMiddlewareContext(), self.importer_user)

        application.submit_application(req, task)

        return application

    def _create_managed_wood_app(self):
        # Take ownership (no form so just copy the logic)
        application = self._create_submitted_wood_app()
        application.get_task(WoodQuotaApplication.Statuses.SUBMITTED, Task.TaskType.PROCESS)
        application.case_owner = self.ilb_admin_user
        application.status = WoodQuotaApplication.Statuses.PROCESSING
        application.licence_start_date = self.today
        application.save()

        # Populate checklist
        checklist, created = WoodQuotaChecklist.objects.get_or_create(
            import_application=application
        )
        form = WoodQuotaChecklistForm(
            instance=checklist,
            data={
                "case_update": YesNoNAChoices.yes,
                "fir_required": YesNoNAChoices.yes,
                "response_preparation": True,
                "validity_period_correct": YesNoNAChoices.yes,
                "endorsements_listed": YesNoNAChoices.yes,
                "authorisation": True,
                "sigl_wood_application_logged": True,
            },
        )
        if form.is_valid():
            form.save()
        else:
            raise CommandError(f"Failed to create checklist: {form.errors}")

        return application

    def _create_authorised_wood_app(self):
        ...

    def _create_completed_wood_app(self):
        ...

    def success_msg(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def error_msg(self, msg):
        self.stdout.write(self.style.ERROR(msg))
