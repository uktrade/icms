from typing import Any

from web.forms.widgets import ICMSModelSelect2Widget
from web.models import Section5Clause


class Section5ClauseSelect(ICMSModelSelect2Widget):
    queryset = Section5Clause.objects.filter(is_active=True).order_by("clause", "description")
    search_fields = ["description__icontains"]

    def build_attrs(
        self, base_attrs: dict[str, Any], extra_attrs: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        attrs = super().build_attrs(base_attrs, extra_attrs)

        attrs["data-minimum-input-length"] = 0
        attrs["data-placeholder"] = "Please choose a subsection"

        return attrs

    def label_from_instance(self, obj: Section5Clause) -> str:
        return f"{obj.clause} {obj.description}"
