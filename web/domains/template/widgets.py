from web.forms.widgets import ICMSModelSelect2Widget


class EndorsementTemplateWidget(ICMSModelSelect2Widget):
    search_fields = [
        "template_name__icontains",
        "versions__content__icontains",
    ]

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        qs = super().filter_queryset(request, term, queryset, **dependent_fields)
        return qs.filter(versions__is_active=True)
