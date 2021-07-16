from django_select2 import forms as s2forms


class CommodityWidget(s2forms.ModelSelect2MultipleWidget):
    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    def label_from_instance(self, commodity):
        return "{code} {code_type} {start_date} {end_date}".format(
            code=commodity.commodity_code,
            code_type=commodity.commodity_type,
            start_date=commodity.validity_start_date or "",
            end_date=commodity.validity_end_date or "",
        )


class CommodityGroupCommodityWidget(CommodityWidget):
    """Used when creating / editing commodity groups"""

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"commodity_type": "commodity_type"}
