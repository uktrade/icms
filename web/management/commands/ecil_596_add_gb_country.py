from django.core.management.base import BaseCommand

from web.domains.country.types import CountryGroupName
from web.models import Country, CountryGroup, OverseasRegion


class Command(BaseCommand):
    help = """Add GB Country and update FA_SIL_COC country group.

    See https://uktrade.atlassian.net/browse/ECIL-601 as to why this command exists.
    Right now there isn't a consistent way to update data for all required scenarios.
    As it stands the new country and modified country group have been added to the fixture data.
    This command needs running in every deployed environment to add the new data.
    """

    def handle(self, *args, **options):
        europe = OverseasRegion.objects.get(name="Europe")

        gb = Country.objects.create(
            name="Great Britain",
            # Copy the United Kingdom values unless ILB say otherwise.
            type="SOVEREIGN_TERRITORY",
            commission_code="6",
            hmrc_code="GB",
            overseas_region=europe,
        )

        # Add GB to the FA-SIl COC group
        fa_sil_coc = CountryGroup.objects.get(name=CountryGroupName.FA_SIL_COC)

        fa_sil_coc.countries.add(gb)
