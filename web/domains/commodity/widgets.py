from django_select2 import forms as s2forms


class CommodityWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = ["commodity_code__contains"]

    def label_from_instance(self, commodity):
        return "{code} {code_type} {start_date} {end_date}".format(
            code=commodity.commodity_code,
            code_type=commodity.commodity_type,
            start_date=commodity.validity_start_date or "",
            end_date=commodity.validity_end_date or "",
        )
