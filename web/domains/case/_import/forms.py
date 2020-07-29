from django.db.models import Q
from django.forms import ModelChoiceField
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.forms import ModelEditForm

from .models import ImportApplication, ImportApplicationType


class NewImportApplicationForm(ModelEditForm):

    application_type = ModelChoiceField(
        queryset=ImportApplicationType.objects.filter(is_active=True),
        help_text="Imports of textiles and clothing or iron and steel of value \
        less than £120 do not need and import license. \
        This does NOT apply to firearms or sanctions derogations.",
    )

    importer = ModelChoiceField(
        queryset=Importer.objects.none(),
        help_text="For Derogations from Sanctions applications, \
        you must be a main importer, \
        and will not be able to select and agent importer.",
    )

    importer_office = ModelChoiceField(
        queryset=Office.objects.none(), help_text="The office that this licence will be issued to."
    )

    def _get_agent_importer_ids(self, user):
        """ Get ids for main importers of given agents"""
        agents = (
            Importer.objects.filter(is_active=True)
            .filter(members=user)
            .filter(main_importer__isnull=False)
        )
        ids = []
        for agent in agents:
            ids.append(agent.main_importer_id)
        return ids

    def _update_agents(self, user, application_type, importer):
        if application_type.type == "Derogation from Sanctions Import Ban":
            return

        # User is a member of main importer's team, no agent.
        if user in importer.members.all():
            return

        agents = importer.agents.filter(is_active=True).filter(members=user)
        field = ModelChoiceField(queryset=agents)
        # Add field configuration to agent as it is a dynamic field
        # and configuration won't be applied as the other fields.
        field.config = self.fields["importer"].config
        self.fields["agent"] = field
        self.Meta.fields.append("agent")

    def _update_offices(self, importer):
        if importer in self.fields["importer"].queryset:
            self.fields["importer_office"].queryset = importer.offices.filter(is_active=True)

    def _update_importers(self, request, application_type):
        importers = Importer.objects.filter(is_active=True)
        main_importers = Q(members=request.user, main_importer__isnull=True)
        agent_importers = Q(pk__in=self._get_agent_importer_ids(request.user))

        if application_type.type == "Derogation from Sanctions Import Ban":
            importers = importers.filter(main_importers)
        else:
            importers = importers.filter(main_importers | agent_importers)
        self.fields["importer"].queryset = importers

    def _update_form(self, request):
        type_pk = self.data.get("application_type", None)
        if type_pk:
            type = ImportApplicationType.objects.get(pk=type_pk)
            self._update_importers(request, type)
            importer_pk = self.data.get("importer", None)
            if importer_pk:
                importer = Importer.objects.get(pk=importer_pk)
                self._update_offices(importer)
                self._update_agents(request.user, type, importer)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_form(request)

    class Meta:
        model = ImportApplication
        fields = ["application_type", "importer", "importer_office"]
        config = {"__all__": {"show_optional_indicator": False}}
