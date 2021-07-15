class CommodityDataLoader:
    """Used to map prefixes to CommodityType when migrating Commodity records."""

    def __init__(self, commodity_type_class):
        firearms = commodity_type_class.objects.get(type="Firearms and Ammunition")

        self.commodity_types = {
            **dict.fromkeys(
                ["28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"],
                commodity_type_class.objects.get(type="Chemicals"),
            ),
            **dict.fromkeys(
                ["72", "73", "76"],
                commodity_type_class.objects.get(type="Iron, Steel and Aluminium"),
            ),
            **dict.fromkeys(
                [
                    "2707",
                    "2709",
                    "2710",
                    "2711",
                    "2712",
                    "2713",
                    "2714",
                    "2715",
                    "2812",
                    "2814",
                    "2901",
                    "2902",
                    "2903",
                    "2905",
                    "2907",
                    "2909",
                    "2910",
                    "2914",
                    "2917",
                    "2926",
                    "2929",
                    "3901",
                ],
                commodity_type_class.objects.get(type="Oil and Petrochemicals"),
            ),
            **dict.fromkeys(
                [
                    "50",
                    "51",
                    "52",
                    "53",
                    "54",
                    "55",
                    "56",
                    "57",
                    "58",
                    "59",
                    "60",
                    "61",
                    "62",
                    "63",
                    "9619",
                ],
                commodity_type_class.objects.get(type="Textiles"),
            ),
            "93": firearms,
            "97": firearms,
            "87": commodity_type_class.objects.get(type="Vehicles"),
            "71": commodity_type_class.objects.get(type="Precious Metals and Stones"),
            "4403": commodity_type_class.objects.get(type="Wood"),
            "4402": commodity_type_class.objects.get(type="Wood Charcoal"),
        }

    def get_commodity_type(self, commodity_code):
        prefix_two_digits = commodity_code[:2]
        prefix_four_digits = commodity_code[:4]

        ct = self.commodity_types.get(prefix_two_digits)

        if ct is None:
            ct = self.commodity_types.get(prefix_four_digits)

        assert ct is not None, "Unable to import... failing"

        return ct
