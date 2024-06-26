from web.forms.widgets import ICMSModelSelect2MultipleWidget
from web.models import Commodity


class OptCompensatingProductsCommodityWidget(ICMSModelSelect2MultipleWidget):
    queryset = Commodity.objects.filter(commoditygroup__commodity_type__type_code="TEXTILES")

    # The value entered by the user is used to search the commodity code
    search_fields = ["commodity_code__contains"]

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"cp_category": "commoditygroup__group_code"}

    def label_from_instance(self, commodity):
        return commodity.commodity_code
