import datetime as dt

from django.core.management.base import BaseCommand

from web.models import Commodity, CommodityGroup, CommodityType


# To run: make manage args="ECIL_652_add_nuclear_commodities"
class Command(BaseCommand):
    help = """Add CommodityGroup and Commodity records relating to Nuclear materials"""

    def handle(self, *args, **options):

        # TODO: Revisit in ECIL-661 - Set correct CommodityType
        #   Add Chapter 26 - Ores, slag and ash
        commodity_type = CommodityType.objects.get(type_code="CHEMICALS")

        # https://www.trade-tariff.service.gov.uk/headings/2612?day=10&month=3&year=2025
        heading_2612_commodities = [
            "2612101000",
            "2612109000",
            "2612201000",
            "2612209000",
        ]
        for commodity in heading_2612_commodities:
            Commodity.objects.get_or_create(
                commodity_code=commodity,
                commodity_type=commodity_type,
                defaults={"validity_start_date": dt.date.today()},
            )

        group, created = CommodityGroup.objects.get_or_create(
            group_type=CommodityGroup.CATEGORY,
            group_code="2612",
            group_name="Uranium or thorium ores and concentrates",
            commodity_type=commodity_type,
        )

        group.commodities.set(Commodity.objects.filter(commodity_code__in=heading_2612_commodities))

        # TODO: Revisit in ECIL-661 - Set correct CommodityType
        #   Chapter 28 - Inorganic chemicals; organic or inorganic compounds of precious metals,
        #   of rare-earth metals, of radioactive elements or of isotopes
        commodity_type = CommodityType.objects.get(type_code="CHEMICALS")
        # https://www.trade-tariff.service.gov.uk/headings/2844?day=10&month=3&year=2025
        heading_2844_commodities = [
            "2844101000",
            "2844103000",
            "2844105000",
            "2844109000",
            "2844202500",
            "2844203500",
            "2844205100",
            "2844205900",
            "2844209900",
            "2844301110",
            "2844301190",
            "2844301900",
            "2844305110",
            "2844305190",
            "2844305500",
            "2844306100",
            "2844306900",
            "2844309100",
            "2844309900",
            "2844411000",
            "2844419000",
            "2844421000",
            "2844429000",
            "2844431000",
            "2844432000",
            "2844438000",
            "2844440000",
            "2844500000",
        ]

        for commodity in heading_2844_commodities:
            Commodity.objects.get_or_create(
                commodity_code=commodity,
                commodity_type=commodity_type,
                defaults={"validity_start_date": dt.date.today()},
            )

        group, created = CommodityGroup.objects.get_or_create(
            group_type=CommodityGroup.CATEGORY,
            group_code="2844",
            group_name=(
                "Radioactive chemical elements and radioactive isotopes"
                " (including the fissile or fertile chemical elements and isotopes)"
                " and their compounds; mixtures and residues containing these products"
            ),
            commodity_type=commodity_type,
        )

        group.commodities.set(Commodity.objects.filter(commodity_code__in=heading_2844_commodities))
