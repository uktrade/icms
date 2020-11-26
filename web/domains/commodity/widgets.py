from django_select2 import forms as s2forms

from web.domains.commodity.models import CommodityType


class CommodityWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "commodity_code__contains",
        "commodity_type__type__icontains",
    ]

    dependent_fields = {"commodity_type": "commodity_type"}

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        type_pk = dependent_fields.pop("commodity_type", None)
        if type_pk:
            dependent_fields["commodity_type__type"] = CommodityType.objects.get(pk=type_pk).type

        return super().filter_queryset(request, term, queryset, **dependent_fields)

    def label_from_instance(self, commodity):
        return "{code} {code_type} {start_date} {end_date}".format(
            code=commodity.commodity_code,
            code_type=commodity.commodity_type.type,
            start_date=commodity.validity_start_date or "",
            end_date=commodity.validity_end_date or "",
        )
