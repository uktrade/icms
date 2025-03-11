from django.core.management.base import BaseCommand

from web.domains.country.types import CountryGroupName
from web.models import Country, CountryGroup


# To run: make manage args="ECIL_657_add_dfl_country_groups"
class Command(BaseCommand):
    help = """Add CommodityGroup and Commodity records relating to Nuclear materials"""

    def handle(self, *args, **options):
        for group_name in [CountryGroupName.FA_DFL_COC, CountryGroupName.FA_DFL_COO]:
            group, _ = CountryGroup.objects.get_or_create(name=group_name.value)

            # Add all real countries to the new group
            group.countries.set(Country.util.get_all_countries())
