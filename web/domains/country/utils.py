from django.db.models import QuerySet

from .models import Country


def comma_separator(sequence: list) -> str:
    if not sequence:
        return ""
    if len(sequence) == 1:
        return sequence[0]
    return "{} and {}".format(", ".join(sequence[:-1]), sequence[-1])


def get_cptpp_countries_list() -> str:
    cptpp = Country.util.get_cptpp_countries().values_list("name", flat=True)
    return comma_separator(list(cptpp))


def get_selected_cptpp_countries(countries: QuerySet["Country"]) -> QuerySet["Country"]:
    country_pks = countries.values_list("pk", flat=True)
    return Country.util.get_cptpp_countries().filter(pk__in=country_pks)


def get_selected_cptpp_countries_list(countries: QuerySet["Country"]) -> str:
    selected_countries = get_selected_cptpp_countries(countries)
    return comma_separator(list(selected_countries.values_list("name", flat=True)))
