import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import islice
from typing import Type

from web.models import CommodityGroup, Country, ImportApplicationType, Usage

START_DATE = dt.date(2023, 1, 1)


@dataclass
class CommodityUsageDataLoader:
    """Creates Usage records for several application types."""

    usage: "Type[Usage]"
    import_application_type: "Type[ImportApplicationType]"
    country: "Type[Country]"
    commodity_group: "Type[CommodityGroup]"

    def create_usage_records(self) -> None:
        self.bulk_create(self.load_textiles_quota_usage())
        self.bulk_create(self.load_opt_usage())
        self.bulk_create(self.load_derogation_from_sanctions_import_ban())
        self.bulk_create(self.load_sanctions_and_adhoc_licence_application())
        self.bulk_create(self.load_iron_and_steel_quota())

    def bulk_create(self, objs: "Iterable[Usage]") -> None:
        batch_size = 1000

        while True:
            batch = list(islice(objs, batch_size))

            if not batch:
                break

            self.usage.objects.bulk_create(batch, batch_size)

    def load_textiles_quota_usage(self) -> "Iterable[Usage]":
        """Load usage records for the Textiles Quota application"""

        group_categories = {
            self.country.objects.get(name="Belarus"): [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "15",
                "20",
                "21",
                "22",
                "24",
                "26",
                "27",
                "29",
                "67",
                "73",
                "115",
                "117",
                "118",
            ],
            self.country.objects.get(name="Korea (North)"): [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "12",
                "13",
                "14",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
                "21",
                "22",
                "23",
                "24",
                "26",
                "27",
                "28",
                "29",
                "31",
                "32",
                "33",
                "34",
                "35",
                "36",
                "37",
                "39",
                "40",
                "41",
                "42",
                "49",
                "50",
                "53",
                "54",
                "55",
                "58",
                "59",
                "61",
                "62",
                "63",
                "65",
                "66",
                "67",
                "68",
                "69",
                "70",
                "72",
                "73",
                "74",
                "75",
                "76",
                "77",
                "78",
                "83",
                "84",
                "85",
                "86",
                "87",
                "88",
                "90",
                "91",
                "93",
                "97",
                "99",
                "100",
                "101",
                "109",
                "111",
                "112",
                "113",
                "114",
                "117",
                "118",
                "120",
                "121",
                "122",
                "123",
                "124",
                "133",
                "134",
                "135",
                "136",
                "137",
                "138",
                "140",
                "141",
                "142",
                "145",
                "149",
                "150",
                "153",
                "156",
                "157",
                "159",
                "160",
                "161",
                "130A",
                "130B",
                "146A",
                "146B",
                "146C",
                "151A",
                "151B",
                "38A",
                "38B",
            ],
        }

        textiles_pk = self.import_application_type.objects.get(type="TEX").pk
        groups = self.commodity_group.objects.filter(commodity_type__type_code="TEXTILES")

        for country, group_code_list in group_categories.items():
            country_group_pks = groups.filter(group_code__in=group_code_list).values_list(
                "pk", flat=True
            )

            for group_pk in country_group_pks:
                yield self.usage(
                    application_type_id=textiles_pk,
                    country_id=country.pk,
                    commodity_group_id=group_pk,
                    start_date=START_DATE,
                )

    def load_opt_usage(self) -> "Iterable[Usage]":
        """Load usage records for the Outward Processing Trade application"""

        country_pk = self.country.objects.get(name="Belarus").pk
        opt_pk = self.import_application_type.objects.get(type="OPT").pk
        group_codes = ["4", "5", "6", "7", "8", "15", "21", "24", "26", "27", "29", "73"]

        groups = self.commodity_group.objects.filter(group_code__in=group_codes).values_list(
            "pk", flat=True
        )

        for group_pk in groups:
            yield self.usage(
                application_type_id=opt_pk,
                country_id=country_pk,
                commodity_group_id=group_pk,
                start_date=START_DATE,
            )

    def load_derogation_from_sanctions_import_ban(self) -> "Iterable[Usage]":
        """Load usage records for the Derogation From Sanctions Import Ban application"""

        group_categories = {
            self.country.objects.get(name="Iran"): ["SAN2", "SAN3"],
            self.country.objects.get(name="Russian Federation"): ["SAN5"],
            self.country.objects.get(name="Somalia"): ["SAN1"],
            self.country.objects.get(name="Syria"): ["SAN2", "SAN4"],
        }

        derogation_pk = self.import_application_type.objects.get(type="SAN").pk
        groups = self.commodity_group.objects.all()

        for country, group_code_list in group_categories.items():
            country_group_pks = groups.filter(group_code__in=group_code_list).values_list(
                "pk", flat=True
            )

            for group_pk in country_group_pks:
                yield self.usage(
                    application_type_id=derogation_pk,
                    country_id=country.pk,
                    commodity_group_id=group_pk,
                    start_date=START_DATE,
                )

    def load_iron_and_steel_quota(self) -> "Iterable[Usage]":
        """Load usage records for the Iron and Steel (Quota) application."""

        iron = self.import_application_type.objects.get(type="IS")

        country = self.country.objects.get(name="Kazakhstan")

        country_group_pks = self.commodity_group.objects.filter(
            group_code__in=["SA1", "SA3"]
        ).values_list("pk", flat=True)

        for group_pk in country_group_pks:
            yield self.usage(
                application_type_id=iron.pk,
                country_id=country.pk,
                commodity_group_id=group_pk,
                start_date=START_DATE,
            )

    def load_sanctions_and_adhoc_licence_application(self) -> "Iterable[Usage]":
        """Load usage records for the Sanctions and Adhoc Licence application

        Note these are just test values that we used for Derogation From Sanctions Import Ban
        The correct records will need loading when we go live.
        """
        group_categories = {
            self.country.objects.get(name="Iran"): ["SAN2", "SAN3"],
            self.country.objects.get(name="Korea (North)"): ["SAN-AND-ADHOC-TEST"],
            self.country.objects.get(name="Russian Federation"): ["SAN5"],
            self.country.objects.get(name="Somalia"): ["SAN1"],
            self.country.objects.get(name="Syria"): ["SAN2", "SAN4"],
        }

        sanction_and_adhoc_pk = self.import_application_type.objects.get(type="ADHOC").pk
        groups = self.commodity_group.objects.all()

        for country, group_code_list in group_categories.items():
            country_group_pks = groups.filter(group_code__in=group_code_list).values_list(
                "pk", flat=True
            )

            for group_pk in country_group_pks:
                yield self.usage(
                    application_type_id=sanction_and_adhoc_pk,
                    country_id=country.pk,
                    commodity_group_id=group_pk,
                    start_date=START_DATE,
                )


def add_usage_data():
    loader = CommodityUsageDataLoader(
        usage=Usage,
        import_application_type=ImportApplicationType,
        country=Country,
        commodity_group=CommodityGroup,
    )
    loader.create_usage_records()
