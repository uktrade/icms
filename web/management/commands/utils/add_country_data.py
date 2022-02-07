import pathlib
from typing import Any, Type

from web.management.commands.countries import read_country_csv
from web.models import Country, CountryGroup, CountryTranslation, CountryTranslationSet

COUNTRY_GROUP_CSV_FILENAME = "countries-groups.csv"


class DataLoader:
    def __init__(self, country_class, translation_set_class):
        self.country_class = country_class
        self.translation_set_class = translation_set_class
        self.country_map = {}
        self.translation_set = {}

    def get_country(self, name):
        if name not in self.country_map:
            self.country_map[name] = self.country_class.objects.get(name=name)

        return self.country_map[name]

    def get_translation_set(self, name):
        if name not in self.translation_set:
            self.translation_set[name] = self.translation_set_class.objects.get(name=name)

        return self.translation_set[name]


def load_country_data():
    # Data spreadsheet, in the web/management/commands/utils directory.
    filename = pathlib.Path(__file__).parent / COUNTRY_GROUP_CSV_FILENAME

    with open(filename) as fh:
        country_data, _ = read_country_csv(fh)

    Country.objects.bulk_create(
        [
            Country(
                name=row["name"],
                is_active=(row["is_active"].upper() == "TRUE"),
                type=row["type"],
                commission_code=row["commission_code"],
                hmrc_code=row["hmrc_code"],
            )
            for row in country_data
        ]
    )


def load_country_group_data():
    filename = pathlib.Path(__file__).parent / COUNTRY_GROUP_CSV_FILENAME

    with open(filename) as fh:
        country_data, group_data = read_country_csv(fh)

    # First we bulk create the groups themselves (without membership).
    CountryGroup.objects.bulk_create(
        [CountryGroup(name=row["name"], comments=row["comments"]) for row in group_data]
    )

    # Now we can find the Country database objects and populate the groups.
    groups_map: dict[str, "Type[CountryGroup]"] = {g.name: g for g in CountryGroup.objects.all()}
    countries_map: dict[str, "Type[Country]"] = {c.name: c for c in Country.objects.all()}
    # We will build a map with the key being a group name, and the value a list
    # of Country objects.
    membership: dict[str, list[Any]] = {g: [] for g in groups_map}

    for row in country_data:
        country = countries_map[row["name"]]

        for gname in row["groups"]:
            membership[gname].append(country)

    for gname, countries in membership.items():
        group = groups_map[gname]
        group.countries.add(*countries)


def add_country_translation_set():
    CountryTranslationSet.objects.get_or_create(name="French", is_active=True)
    CountryTranslationSet.objects.get_or_create(name="Portuguese", is_active=True)
    CountryTranslationSet.objects.get_or_create(name="Russian", is_active=True)
    CountryTranslationSet.objects.get_or_create(name="Spanish", is_active=True)
    CountryTranslationSet.objects.get_or_create(name="Turkish", is_active=True)


def add_country_translation():
    data = DataLoader(Country, CountryTranslationSet)
    CountryTranslation.objects.bulk_create(
        [
            CountryTranslation(**dict(zip(["translation", "country", "translation_set"], row)))
            for row in [
                [
                    "Экваториальная Гвинея",
                    data.get_country(name="Equatorial Guinea"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Эстония",
                    data.get_country(name="Estonia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Эфиопия",
                    data.get_country(name="Ethiopia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "ЮАР",
                    data.get_country(name="South Africa"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Ямайка",
                    data.get_country(name="Jamaica"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Япония",
                    data.get_country(name="Japan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "о-в Св. Елены",
                    data.get_country(name="Saint Helena"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Afganistán",
                    data.get_country(name="Afghanistan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Albania",
                    data.get_country(name="Albania"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Alemania",
                    data.get_country(name="Germany"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Angola",
                    data.get_country(name="Angola"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Arabia Saudí",
                    data.get_country(name="Saudi Arabia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Argelia",
                    data.get_country(name="Algeria"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Argentina",
                    data.get_country(name="Argentina"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Armenia",
                    data.get_country(name="Armenia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Aruba", data.get_country(name="Aruba"), data.get_translation_set(name="Spanish")],
                [
                    "Australia",
                    data.get_country(name="Australia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Austria",
                    data.get_country(name="Austria"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Azerbaiyán",
                    data.get_country(name="Azerbaijan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bahamas",
                    data.get_country(name="Bahamas"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bangladés",
                    data.get_country(name="Bangladesh"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Barbados",
                    data.get_country(name="Barbados"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Baréin",
                    data.get_country(name="Bahrain"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Belice",
                    data.get_country(name="Belize"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Benín", data.get_country(name="Benin"), data.get_translation_set(name="Spanish")],
                [
                    "Bermudas",
                    data.get_country(name="Bermuda"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bielorrusia",
                    data.get_country(name="Belarus"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bolivia",
                    data.get_country(name="Bolivia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bosnia-Herzegovina",
                    data.get_country(name="Bosnia and Herzegovina"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Botsuana",
                    data.get_country(name="Botswana"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Brasil",
                    data.get_country(name="Brazil"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Brunéi",
                    data.get_country(name="Brunei"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bulgaria",
                    data.get_country(name="Bulgaria"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bután",
                    data.get_country(name="Bhutan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Bélgica",
                    data.get_country(name="Belgium"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Camboya",
                    data.get_country(name="Cambodia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Canadá",
                    data.get_country(name="Canada"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Catar", data.get_country(name="Qatar"), data.get_translation_set(name="Spanish")],
                [
                    "Chequia",
                    data.get_country(name="the Czech Republic"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Chile", data.get_country(name="Chile"), data.get_translation_set(name="Spanish")],
                ["China", data.get_country(name="China"), data.get_translation_set(name="Spanish")],
                [
                    "Chipre",
                    data.get_country(name="Cyprus"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Colombia",
                    data.get_country(name="Colombia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Corea del Norte",
                    data.get_country(name="Korea (North)"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Corea del Sur",
                    data.get_country(name="Korea (South)"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Costa Rica",
                    data.get_country(name="Costa Rica"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Croacia",
                    data.get_country(name="Croatia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Cuba", data.get_country(name="Cuba"), data.get_translation_set(name="Spanish")],
                [
                    "Côte d’Ivoire",
                    data.get_country(name="Cote d'Ivoire"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Dinamarca",
                    data.get_country(name="Denmark"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Dominica",
                    data.get_country(name="Dominica"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Ecuador",
                    data.get_country(name="Ecuador"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Egipto",
                    data.get_country(name="Egypt"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "El Salvador",
                    data.get_country(name="El Salvador"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Emiratos Árabes Unidos",
                    data.get_country(name="United Arab Emirates"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Eslovaquia",
                    data.get_country(name="the Slovak Republic"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Eslovenia",
                    data.get_country(name="Slovenia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "España",
                    data.get_country(name="Spain"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Estados Unidos",
                    data.get_country(name="USA"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Estonia",
                    data.get_country(name="Estonia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Etiopía",
                    data.get_country(name="Ethiopia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Filipinas",
                    data.get_country(name="Philippines"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Finlandia",
                    data.get_country(name="Finland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Francia",
                    data.get_country(name="France"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Gabón", data.get_country(name="Gabon"), data.get_translation_set(name="Spanish")],
                [
                    "Gambia",
                    data.get_country(name="Gambia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Georgia",
                    data.get_country(name="Georgia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Ghana", data.get_country(name="Ghana"), data.get_translation_set(name="Spanish")],
                [
                    "Gibraltar",
                    data.get_country(name="Gibraltar"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Grecia",
                    data.get_country(name="Greece"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Groenlandia",
                    data.get_country(name="Greenland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Guatemala",
                    data.get_country(name="Guatemala"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Guernesey",
                    data.get_country(name="Guernsey"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Guinea",
                    data.get_country(name="Guinea"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Guinea Ecuatorial",
                    data.get_country(name="Equatorial Guinea"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Guyana",
                    data.get_country(name="Guyana"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Haití", data.get_country(name="Haiti"), data.get_translation_set(name="Spanish")],
                [
                    "Honduras",
                    data.get_country(name="Honduras"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Hungría",
                    data.get_country(name="Hungary"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["India", data.get_country(name="India"), data.get_translation_set(name="Spanish")],
                [
                    "Indonesia",
                    data.get_country(name="Indonesia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Irak", data.get_country(name="Iraq"), data.get_translation_set(name="Spanish")],
                [
                    "Irlanda",
                    data.get_country(name="Irish Republic"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Irán", data.get_country(name="Iran"), data.get_translation_set(name="Spanish")],
                [
                    "Islandia",
                    data.get_country(name="Iceland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Islas Feroe",
                    data.get_country(name="Faroe Islands"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Islas Malvinas",
                    data.get_country(name="Falkland Islands"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Islas Salomón",
                    data.get_country(name="Soloman Islands"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Islas Vírgenes Británicas",
                    data.get_country(name="British Virgin Islands"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Israel",
                    data.get_country(name="Israel"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Italia",
                    data.get_country(name="Italy"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Jamaica",
                    data.get_country(name="Jamaica"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Japón", data.get_country(name="Japan"), data.get_translation_set(name="Spanish")],
                [
                    "Jersey",
                    data.get_country(name="Jersey"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Jordania",
                    data.get_country(name="Jordan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Kazajistán",
                    data.get_country(name="Kazakhstan"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Kenia", data.get_country(name="Kenya"), data.get_translation_set(name="Spanish")],
                [
                    "Kirguistán",
                    data.get_country(name="Kyrgyzstan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Kosovo",
                    data.get_country(name="Kosovo"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Kuwait",
                    data.get_country(name="Kuwait"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Laos", data.get_country(name="Laos"), data.get_translation_set(name="Spanish")],
                [
                    "Letonia",
                    data.get_country(name="Latvia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Liberia",
                    data.get_country(name="Liberia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Libia", data.get_country(name="Libya"), data.get_translation_set(name="Spanish")],
                [
                    "Liechtenstein",
                    data.get_country(name="Liechtenstein"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Lituania",
                    data.get_country(name="Lithuania"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Luxemburgo",
                    data.get_country(name="Luxembourg"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Líbano",
                    data.get_country(name="Lebanon"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Macedonia",
                    data.get_country(name="Macedonia, Former Yugoslav Republic of"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Madagascar",
                    data.get_country(name="Madagascar"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Malasia",
                    data.get_country(name="Malaysia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Maldivas",
                    data.get_country(name="Maldives"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Mali", data.get_country(name="Mali"), data.get_translation_set(name="Spanish")],
                ["Malta", data.get_country(name="Malta"), data.get_translation_set(name="Spanish")],
                [
                    "Marruecos",
                    data.get_country(name="Morocco"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Mauricio",
                    data.get_country(name="Mauritius"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Mauritania",
                    data.get_country(name="Mauritania"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Micronesia",
                    data.get_country(name="Micronesia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Moldavia",
                    data.get_country(name="Moldova"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Mongolia",
                    data.get_country(name="Mongolia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Montenegro",
                    data.get_country(name="Montenegro"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Mozambique",
                    data.get_country(name="Mozambique"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Myanmar (Birmania)",
                    data.get_country(name="Myanmar (Burma)"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "México",
                    data.get_country(name="Mexico"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Namibia",
                    data.get_country(name="Namibia"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Nauru", data.get_country(name="Nauru"), data.get_translation_set(name="Spanish")],
                ["Nepal", data.get_country(name="Nepal"), data.get_translation_set(name="Spanish")],
                [
                    "Nicaragua",
                    data.get_country(name="Nicaragua"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Nigeria",
                    data.get_country(name="Nigeria"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Noruega",
                    data.get_country(name="Norway"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Nueva Zelanda",
                    data.get_country(name="New Zealand"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Omán", data.get_country(name="Oman"), data.get_translation_set(name="Spanish")],
                [
                    "Pakistán",
                    data.get_country(name="Pakistan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Panamá",
                    data.get_country(name="Panama"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Papúa Nueva Guinea",
                    data.get_country(name="Papua New Guinea"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Paraguay",
                    data.get_country(name="Paraguay"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Países Bajos",
                    data.get_country(name="Netherlands"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Perú", data.get_country(name="Peru"), data.get_translation_set(name="Spanish")],
                [
                    "Polonia",
                    data.get_country(name="Poland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Portugal",
                    data.get_country(name="Portugal"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Puerto Rico",
                    data.get_country(name="Puerto Rico"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "RAE de Hong Kong (China)",
                    data.get_country(name="Hong Kong"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "RAE de Macao (China)",
                    data.get_country(name="Macao"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Reino Unido",
                    data.get_country(name="United Kingdom"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "República Democrática del Congo",
                    data.get_country(name="Congo (Dem. Republic)"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "República Dominicana",
                    data.get_country(name="Dominican Republic"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "República del Congo",
                    data.get_country(name="Congo"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Ruanda",
                    data.get_country(name="Rwanda"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Rumanía",
                    data.get_country(name="Romania"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Rusia",
                    data.get_country(name="Russian Federation"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Santa Elena",
                    data.get_country(name="Saint Helena"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Senegal",
                    data.get_country(name="Senegal"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Serbia",
                    data.get_country(name="Serbia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Seychelles",
                    data.get_country(name="Seychelles"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Singapur",
                    data.get_country(name="Singapore"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Siria", data.get_country(name="Syria"), data.get_translation_set(name="Spanish")],
                [
                    "Somalia",
                    data.get_country(name="Somalia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Sri Lanka",
                    data.get_country(name="Sri Lanka"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Suazilandia",
                    data.get_country(name="Swaziland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Sudáfrica",
                    data.get_country(name="South Africa"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Sudán", data.get_country(name="Sudan"), data.get_translation_set(name="Spanish")],
                [
                    "Suecia",
                    data.get_country(name="Sweden"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Suiza",
                    data.get_country(name="Switzerland"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Surinam",
                    data.get_country(name="Suriname"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Tailandia",
                    data.get_country(name="Thailand"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Taiwán",
                    data.get_country(name="Taiwan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Tanzania",
                    data.get_country(name="Tanzania"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Tayikistán",
                    data.get_country(name="Tajikistan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Territorios Palestinos",
                    data.get_country(name="Occupied Palestinian Territories"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Trinidad y Tobago",
                    data.get_country(name="Trinidad & Tobago"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Turkmenistán",
                    data.get_country(name="Turkmenistan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Turquía",
                    data.get_country(name="Turkey"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Túnez",
                    data.get_country(name="Tunisia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Ucrania",
                    data.get_country(name="Ukraine"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Uruguay",
                    data.get_country(name="Uruguay"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Uzbekistán",
                    data.get_country(name="Uzbekistan"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Venezuela",
                    data.get_country(name="Venezuela"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Vietnam",
                    data.get_country(name="Vietnam"),
                    data.get_translation_set(name="Spanish"),
                ],
                ["Yemen", data.get_country(name="Yemen"), data.get_translation_set(name="Spanish")],
                [
                    "Zambia",
                    data.get_country(name="Zambia"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Zimbabue",
                    data.get_country(name="Zimbabwe"),
                    data.get_translation_set(name="Spanish"),
                ],
                [
                    "Afganistan",
                    data.get_country(name="Afghanistan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Almanya",
                    data.get_country(name="Germany"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Amerika Birleşik Devletleri",
                    data.get_country(name="USA"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Angola",
                    data.get_country(name="Angola"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Arjantin",
                    data.get_country(name="Argentina"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Arnavutluk",
                    data.get_country(name="Albania"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Aruba", data.get_country(name="Aruba"), data.get_translation_set(name="Turkish")],
                [
                    "Avustralya",
                    data.get_country(name="Australia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Avusturya",
                    data.get_country(name="Austria"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Azerbaycan",
                    data.get_country(name="Azerbaijan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bahamalar",
                    data.get_country(name="Bahamas"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bahreyn",
                    data.get_country(name="Bahrain"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bangladeş",
                    data.get_country(name="Bangladesh"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Barbados",
                    data.get_country(name="Barbados"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Belarus",
                    data.get_country(name="Belarus"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Belize",
                    data.get_country(name="Belize"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Belçika",
                    data.get_country(name="Belgium"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Benin", data.get_country(name="Benin"), data.get_translation_set(name="Turkish")],
                [
                    "Bermuda",
                    data.get_country(name="Bermuda"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Birleşik Arap Emirlikleri",
                    data.get_country(name="United Arab Emirates"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Birleşik Krallık",
                    data.get_country(name="United Kingdom"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bolivya",
                    data.get_country(name="Bolivia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bosna-Hersek",
                    data.get_country(name="Bosnia and Herzegovina"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Botsvana",
                    data.get_country(name="Botswana"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Brezilya",
                    data.get_country(name="Brazil"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Britanya Virjin Adaları",
                    data.get_country(name="British Virgin Islands"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Brunei",
                    data.get_country(name="Brunei"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Bulgaristan",
                    data.get_country(name="Bulgaria"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Butan",
                    data.get_country(name="Bhutan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Cebelitarık",
                    data.get_country(name="Gibraltar"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Cezayir",
                    data.get_country(name="Algeria"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Danimarka",
                    data.get_country(name="Denmark"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Dominik Cumhuriyeti",
                    data.get_country(name="Dominican Republic"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Dominika",
                    data.get_country(name="Dominica"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ekvador",
                    data.get_country(name="Ecuador"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ekvator Ginesi",
                    data.get_country(name="Equatorial Guinea"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "El Salvador",
                    data.get_country(name="El Salvador"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Endonezya",
                    data.get_country(name="Indonesia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ermenistan",
                    data.get_country(name="Armenia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Estonya",
                    data.get_country(name="Estonia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Etiyopya",
                    data.get_country(name="Ethiopia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Falkland Adaları",
                    data.get_country(name="Falkland Islands"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Faroe Adaları",
                    data.get_country(name="Faroe Islands"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Fas", data.get_country(name="Morocco"), data.get_translation_set(name="Turkish")],
                [
                    "Fildişi Sahili",
                    data.get_country(name="Cote d'Ivoire"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Filipinler",
                    data.get_country(name="Philippines"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Filistin Bölgeleri",
                    data.get_country(name="Occupied Palestinian Territories"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Finlandiya",
                    data.get_country(name="Finland"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Fransa",
                    data.get_country(name="France"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Gabon", data.get_country(name="Gabon"), data.get_translation_set(name="Turkish")],
                [
                    "Gambiya",
                    data.get_country(name="Gambia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Gana", data.get_country(name="Ghana"), data.get_translation_set(name="Turkish")],
                ["Gine", data.get_country(name="Guinea"), data.get_translation_set(name="Turkish")],
                [
                    "Grönland",
                    data.get_country(name="Greenland"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Guatemala",
                    data.get_country(name="Guatemala"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Guernsey",
                    data.get_country(name="Guernsey"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Guyana",
                    data.get_country(name="Guyana"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Güney Afrika",
                    data.get_country(name="South Africa"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Güney Kore",
                    data.get_country(name="Korea (South)"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Gürcistan",
                    data.get_country(name="Georgia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Haiti", data.get_country(name="Haiti"), data.get_translation_set(name="Turkish")],
                [
                    "Hindistan",
                    data.get_country(name="India"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Hollanda",
                    data.get_country(name="Netherlands"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Honduras",
                    data.get_country(name="Honduras"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Hırvatistan",
                    data.get_country(name="Croatia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Irak", data.get_country(name="Iraq"), data.get_translation_set(name="Turkish")],
                [
                    "Jamaika",
                    data.get_country(name="Jamaica"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Japonya",
                    data.get_country(name="Japan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Jersey",
                    data.get_country(name="Jersey"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kamboçya",
                    data.get_country(name="Cambodia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kanada",
                    data.get_country(name="Canada"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Karadağ",
                    data.get_country(name="Montenegro"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Katar", data.get_country(name="Qatar"), data.get_translation_set(name="Turkish")],
                [
                    "Kazakistan",
                    data.get_country(name="Kazakhstan"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Kenya", data.get_country(name="Kenya"), data.get_translation_set(name="Turkish")],
                [
                    "Kolombiya",
                    data.get_country(name="Colombia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kongo - Brazavil",
                    data.get_country(name="Congo"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kongo - Kinşasa",
                    data.get_country(name="Congo (Dem. Republic)"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kosova",
                    data.get_country(name="Kosovo"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kosta Rika",
                    data.get_country(name="Costa Rica"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kuveyt",
                    data.get_country(name="Kuwait"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kuzey Kore",
                    data.get_country(name="Korea (North)"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Küba", data.get_country(name="Cuba"), data.get_translation_set(name="Turkish")],
                [
                    "Kıbrıs",
                    data.get_country(name="Cyprus"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Kırgızistan",
                    data.get_country(name="Kyrgyzstan"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Laos", data.get_country(name="Laos"), data.get_translation_set(name="Turkish")],
                [
                    "Letonya",
                    data.get_country(name="Latvia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Liberya",
                    data.get_country(name="Liberia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Libya", data.get_country(name="Libya"), data.get_translation_set(name="Turkish")],
                [
                    "Liechtenstein",
                    data.get_country(name="Liechtenstein"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Litvanya",
                    data.get_country(name="Lithuania"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Lübnan",
                    data.get_country(name="Lebanon"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Lüksemburg",
                    data.get_country(name="Luxembourg"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Macaristan",
                    data.get_country(name="Hungary"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Madagaskar",
                    data.get_country(name="Madagascar"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Makedonya",
                    data.get_country(name="Macedonia, Former Yugoslav Republic of"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Maldivler",
                    data.get_country(name="Maldives"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Malezya",
                    data.get_country(name="Malaysia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Mali", data.get_country(name="Mali"), data.get_translation_set(name="Turkish")],
                ["Malta", data.get_country(name="Malta"), data.get_translation_set(name="Turkish")],
                [
                    "Mauritius",
                    data.get_country(name="Mauritius"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Meksika",
                    data.get_country(name="Mexico"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Mikronezya",
                    data.get_country(name="Micronesia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Moldova",
                    data.get_country(name="Moldova"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Moritanya",
                    data.get_country(name="Mauritania"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Mozambik",
                    data.get_country(name="Mozambique"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Moğolistan",
                    data.get_country(name="Mongolia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Myanmar (Burma)",
                    data.get_country(name="Myanmar (Burma)"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Mısır", data.get_country(name="Egypt"), data.get_translation_set(name="Turkish")],
                [
                    "Namibya",
                    data.get_country(name="Namibia"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Nauru", data.get_country(name="Nauru"), data.get_translation_set(name="Turkish")],
                ["Nepal", data.get_country(name="Nepal"), data.get_translation_set(name="Turkish")],
                [
                    "Nijerya",
                    data.get_country(name="Nigeria"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Nikaragua",
                    data.get_country(name="Nicaragua"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Norveç",
                    data.get_country(name="Norway"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Pakistan",
                    data.get_country(name="Pakistan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Panama",
                    data.get_country(name="Panama"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Papua Yeni Gine",
                    data.get_country(name="Papua New Guinea"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Paraguay",
                    data.get_country(name="Paraguay"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Peru", data.get_country(name="Peru"), data.get_translation_set(name="Turkish")],
                [
                    "Polonya",
                    data.get_country(name="Poland"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Portekiz",
                    data.get_country(name="Portugal"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Porto Riko",
                    data.get_country(name="Puerto Rico"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Romanya",
                    data.get_country(name="Romania"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ruanda",
                    data.get_country(name="Rwanda"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Rusya",
                    data.get_country(name="Russian Federation"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Saint Helena",
                    data.get_country(name="Saint Helena"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Senegal",
                    data.get_country(name="Senegal"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Seyşeller",
                    data.get_country(name="Seychelles"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Singapur",
                    data.get_country(name="Singapore"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Slovakya",
                    data.get_country(name="the Slovak Republic"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Slovenya",
                    data.get_country(name="Slovenia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Solomon Adaları",
                    data.get_country(name="Soloman Islands"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Somali",
                    data.get_country(name="Somalia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Sri Lanka",
                    data.get_country(name="Sri Lanka"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Sudan", data.get_country(name="Sudan"), data.get_translation_set(name="Turkish")],
                [
                    "Surinam",
                    data.get_country(name="Suriname"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Suriye",
                    data.get_country(name="Syria"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Suudi Arabistan",
                    data.get_country(name="Saudi Arabia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Svaziland",
                    data.get_country(name="Swaziland"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Sırbistan",
                    data.get_country(name="Serbia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Tacikistan",
                    data.get_country(name="Tajikistan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Tanzanya",
                    data.get_country(name="Tanzania"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Tayland",
                    data.get_country(name="Thailand"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Tayvan",
                    data.get_country(name="Taiwan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Trinidad ve Tobago",
                    data.get_country(name="Trinidad & Tobago"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Tunus",
                    data.get_country(name="Tunisia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Türkiye",
                    data.get_country(name="Turkey"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Türkmenistan",
                    data.get_country(name="Turkmenistan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ukrayna",
                    data.get_country(name="Ukraine"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Umman", data.get_country(name="Oman"), data.get_translation_set(name="Turkish")],
                [
                    "Uruguay",
                    data.get_country(name="Uruguay"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Venezuela",
                    data.get_country(name="Venezuela"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Vietnam",
                    data.get_country(name="Vietnam"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Yemen", data.get_country(name="Yemen"), data.get_translation_set(name="Turkish")],
                [
                    "Yeni Zelanda",
                    data.get_country(name="New Zealand"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Yunanistan",
                    data.get_country(name="Greece"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Zambiya",
                    data.get_country(name="Zambia"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Zimbabve",
                    data.get_country(name="Zimbabwe"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Çekya",
                    data.get_country(name="the Czech Republic"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Çin", data.get_country(name="China"), data.get_translation_set(name="Turkish")],
                [
                    "Çin Hong Kong ÖİB",
                    data.get_country(name="Hong Kong"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Çin Makao ÖİB",
                    data.get_country(name="Macao"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Özbekistan",
                    data.get_country(name="Uzbekistan"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "Ürdün",
                    data.get_country(name="Jordan"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["İran", data.get_country(name="Iran"), data.get_translation_set(name="Turkish")],
                [
                    "İrlanda",
                    data.get_country(name="Irish Republic"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İspanya",
                    data.get_country(name="Spain"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İsrail",
                    data.get_country(name="Israel"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İsveç",
                    data.get_country(name="Sweden"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İsviçre",
                    data.get_country(name="Switzerland"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İtalya",
                    data.get_country(name="Italy"),
                    data.get_translation_set(name="Turkish"),
                ],
                [
                    "İzlanda",
                    data.get_country(name="Iceland"),
                    data.get_translation_set(name="Turkish"),
                ],
                ["Şili", data.get_country(name="Chile"), data.get_translation_set(name="Turkish")],
                [
                    "Afghanistan",
                    data.get_country(name="Afghanistan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Afrique du Sud",
                    data.get_country(name="South Africa"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Albanie",
                    data.get_country(name="Albania"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Algérie",
                    data.get_country(name="Algeria"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Allemagne",
                    data.get_country(name="Germany"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Angola",
                    data.get_country(name="Angola"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Arabie saoudite",
                    data.get_country(name="Saudi Arabia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Argentine",
                    data.get_country(name="Argentina"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Arménie",
                    data.get_country(name="Armenia"),
                    data.get_translation_set(name="French"),
                ],
                ["Aruba", data.get_country(name="Aruba"), data.get_translation_set(name="French")],
                [
                    "Australie",
                    data.get_country(name="Australia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Autriche",
                    data.get_country(name="Austria"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Azerbaïdjan",
                    data.get_country(name="Azerbaijan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bahamas",
                    data.get_country(name="Bahamas"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bahreïn",
                    data.get_country(name="Bahrain"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bangladesh",
                    data.get_country(name="Bangladesh"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Barbade",
                    data.get_country(name="Barbados"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Belgique",
                    data.get_country(name="Belgium"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Belize",
                    data.get_country(name="Belize"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bermudes",
                    data.get_country(name="Bermuda"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bhoutan",
                    data.get_country(name="Bhutan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Biélorussie",
                    data.get_country(name="Belarus"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bolivie",
                    data.get_country(name="Bolivia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bosnie-Herzégovine",
                    data.get_country(name="Bosnia and Herzegovina"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Botswana",
                    data.get_country(name="Botswana"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Brunéi Darussalam",
                    data.get_country(name="Brunei"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Brésil",
                    data.get_country(name="Brazil"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Bulgarie",
                    data.get_country(name="Bulgaria"),
                    data.get_translation_set(name="French"),
                ],
                ["Bénin", data.get_country(name="Benin"), data.get_translation_set(name="French")],
                [
                    "Cambodge",
                    data.get_country(name="Cambodia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Canada",
                    data.get_country(name="Canada"),
                    data.get_translation_set(name="French"),
                ],
                ["Chili", data.get_country(name="Chile"), data.get_translation_set(name="French")],
                ["Chine", data.get_country(name="China"), data.get_translation_set(name="French")],
                [
                    "Chypre",
                    data.get_country(name="Cyprus"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Colombie",
                    data.get_country(name="Colombia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Congo-Brazzaville",
                    data.get_country(name="Congo"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Congo-Kinshasa",
                    data.get_country(name="Congo (Dem. Republic)"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Corée du Nord",
                    data.get_country(name="Korea (North)"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Corée du Sud",
                    data.get_country(name="Korea (South)"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Costa Rica",
                    data.get_country(name="Costa Rica"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Croatie",
                    data.get_country(name="Croatia"),
                    data.get_translation_set(name="French"),
                ],
                ["Cuba", data.get_country(name="Cuba"), data.get_translation_set(name="French")],
                [
                    "Côte d’Ivoire",
                    data.get_country(name="Cote d'Ivoire"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Danemark",
                    data.get_country(name="Denmark"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Dominique",
                    data.get_country(name="Dominica"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "El Salvador",
                    data.get_country(name="El Salvador"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Espagne",
                    data.get_country(name="Spain"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Estonie",
                    data.get_country(name="Estonia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Finlande",
                    data.get_country(name="Finland"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "France",
                    data.get_country(name="France"),
                    data.get_translation_set(name="French"),
                ],
                ["Gabon", data.get_country(name="Gabon"), data.get_translation_set(name="French")],
                [
                    "Gambie",
                    data.get_country(name="Gambia"),
                    data.get_translation_set(name="French"),
                ],
                ["Ghana", data.get_country(name="Ghana"), data.get_translation_set(name="French")],
                [
                    "Gibraltar",
                    data.get_country(name="Gibraltar"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Groenland",
                    data.get_country(name="Greenland"),
                    data.get_translation_set(name="French"),
                ],
                ["Grèce", data.get_country(name="Greece"), data.get_translation_set(name="French")],
                [
                    "Guatemala",
                    data.get_country(name="Guatemala"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Guernesey",
                    data.get_country(name="Guernsey"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Guinée",
                    data.get_country(name="Guinea"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Guinée équatoriale",
                    data.get_country(name="Equatorial Guinea"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Guyana",
                    data.get_country(name="Guyana"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Géorgie",
                    data.get_country(name="Georgia"),
                    data.get_translation_set(name="French"),
                ],
                ["Haïti", data.get_country(name="Haiti"), data.get_translation_set(name="French")],
                [
                    "Honduras",
                    data.get_country(name="Honduras"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Hongrie",
                    data.get_country(name="Hungary"),
                    data.get_translation_set(name="French"),
                ],
                ["Inde", data.get_country(name="India"), data.get_translation_set(name="French")],
                [
                    "Indonésie",
                    data.get_country(name="Indonesia"),
                    data.get_translation_set(name="French"),
                ],
                ["Irak", data.get_country(name="Iraq"), data.get_translation_set(name="French")],
                ["Iran", data.get_country(name="Iran"), data.get_translation_set(name="French")],
                [
                    "Irlande",
                    data.get_country(name="Irish Republic"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Islande",
                    data.get_country(name="Iceland"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Israël",
                    data.get_country(name="Israel"),
                    data.get_translation_set(name="French"),
                ],
                ["Italie", data.get_country(name="Italy"), data.get_translation_set(name="French")],
                [
                    "Jamaïque",
                    data.get_country(name="Jamaica"),
                    data.get_translation_set(name="French"),
                ],
                ["Japon", data.get_country(name="Japan"), data.get_translation_set(name="French")],
                [
                    "Jersey",
                    data.get_country(name="Jersey"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Jordanie",
                    data.get_country(name="Jordan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Kazakhstan",
                    data.get_country(name="Kazakhstan"),
                    data.get_translation_set(name="French"),
                ],
                ["Kenya", data.get_country(name="Kenya"), data.get_translation_set(name="French")],
                [
                    "Kirghizistan",
                    data.get_country(name="Kyrgyzstan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Kosovo",
                    data.get_country(name="Kosovo"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Koweït",
                    data.get_country(name="Kuwait"),
                    data.get_translation_set(name="French"),
                ],
                ["Laos", data.get_country(name="Laos"), data.get_translation_set(name="French")],
                [
                    "Lettonie",
                    data.get_country(name="Latvia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Liban",
                    data.get_country(name="Lebanon"),
                    data.get_translation_set(name="French"),
                ],
                ["Libye", data.get_country(name="Libya"), data.get_translation_set(name="French")],
                [
                    "Libéria",
                    data.get_country(name="Liberia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Liechtenstein",
                    data.get_country(name="Liechtenstein"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Lituanie",
                    data.get_country(name="Lithuania"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Luxembourg",
                    data.get_country(name="Luxembourg"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Macédoine",
                    data.get_country(name="Macedonia, Former Yugoslav Republic of"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Madagascar",
                    data.get_country(name="Madagascar"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Malaisie",
                    data.get_country(name="Malaysia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Maldives",
                    data.get_country(name="Maldives"),
                    data.get_translation_set(name="French"),
                ],
                ["Mali", data.get_country(name="Mali"), data.get_translation_set(name="French")],
                ["Malte", data.get_country(name="Malta"), data.get_translation_set(name="French")],
                [
                    "Maroc",
                    data.get_country(name="Morocco"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Maurice",
                    data.get_country(name="Mauritius"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Mauritanie",
                    data.get_country(name="Mauritania"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Mexique",
                    data.get_country(name="Mexico"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Moldavie",
                    data.get_country(name="Moldova"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Mongolie",
                    data.get_country(name="Mongolia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Monténégro",
                    data.get_country(name="Montenegro"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Mozambique",
                    data.get_country(name="Mozambique"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Myanmar (Birmanie)",
                    data.get_country(name="Myanmar (Burma)"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Namibie",
                    data.get_country(name="Namibia"),
                    data.get_translation_set(name="French"),
                ],
                ["Nauru", data.get_country(name="Nauru"), data.get_translation_set(name="French")],
                [
                    "Nicaragua",
                    data.get_country(name="Nicaragua"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Nigéria",
                    data.get_country(name="Nigeria"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Norvège",
                    data.get_country(name="Norway"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Nouvelle-Zélande",
                    data.get_country(name="New Zealand"),
                    data.get_translation_set(name="French"),
                ],
                ["Népal", data.get_country(name="Nepal"), data.get_translation_set(name="French")],
                ["Oman", data.get_country(name="Oman"), data.get_translation_set(name="French")],
                [
                    "Ouzbékistan",
                    data.get_country(name="Uzbekistan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Pakistan",
                    data.get_country(name="Pakistan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Panama",
                    data.get_country(name="Panama"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Papouasie-Nouvelle-Guinée",
                    data.get_country(name="Papua New Guinea"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Paraguay",
                    data.get_country(name="Paraguay"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Pays-Bas",
                    data.get_country(name="Netherlands"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Philippines",
                    data.get_country(name="Philippines"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Pologne",
                    data.get_country(name="Poland"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Porto Rico",
                    data.get_country(name="Puerto Rico"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Portugal",
                    data.get_country(name="Portugal"),
                    data.get_translation_set(name="French"),
                ],
                ["Pérou", data.get_country(name="Peru"), data.get_translation_set(name="French")],
                ["Qatar", data.get_country(name="Qatar"), data.get_translation_set(name="French")],
                [
                    "R.A.S. chinoise de Hong Kong",
                    data.get_country(name="Hong Kong"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "R.A.S. chinoise de Macao",
                    data.get_country(name="Macao"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Roumanie",
                    data.get_country(name="Romania"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Royaume-Uni",
                    data.get_country(name="United Kingdom"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Russie",
                    data.get_country(name="Russian Federation"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Rwanda",
                    data.get_country(name="Rwanda"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "République dominicaine",
                    data.get_country(name="Dominican Republic"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Sainte-Hélène",
                    data.get_country(name="Saint Helena"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Serbie",
                    data.get_country(name="Serbia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Seychelles",
                    data.get_country(name="Seychelles"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Singapour",
                    data.get_country(name="Singapore"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Slovaquie",
                    data.get_country(name="the Slovak Republic"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Slovénie",
                    data.get_country(name="Slovenia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Somalie",
                    data.get_country(name="Somalia"),
                    data.get_translation_set(name="French"),
                ],
                ["Soudan", data.get_country(name="Sudan"), data.get_translation_set(name="French")],
                [
                    "Sri Lanka",
                    data.get_country(name="Sri Lanka"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Suisse",
                    data.get_country(name="Switzerland"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Suriname",
                    data.get_country(name="Suriname"),
                    data.get_translation_set(name="French"),
                ],
                ["Suède", data.get_country(name="Sweden"), data.get_translation_set(name="French")],
                [
                    "Swaziland",
                    data.get_country(name="Swaziland"),
                    data.get_translation_set(name="French"),
                ],
                ["Syrie", data.get_country(name="Syria"), data.get_translation_set(name="French")],
                [
                    "Sénégal",
                    data.get_country(name="Senegal"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Tadjikistan",
                    data.get_country(name="Tajikistan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Tanzanie",
                    data.get_country(name="Tanzania"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Taïwan",
                    data.get_country(name="Taiwan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Tchéquie",
                    data.get_country(name="the Czech Republic"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Territoires palestiniens",
                    data.get_country(name="Occupied Palestinian Territories"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Thaïlande",
                    data.get_country(name="Thailand"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Trinité-et-Tobago",
                    data.get_country(name="Trinidad & Tobago"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Tunisie",
                    data.get_country(name="Tunisia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Turkménistan",
                    data.get_country(name="Turkmenistan"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Turquie",
                    data.get_country(name="Turkey"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Ukraine",
                    data.get_country(name="Ukraine"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Uruguay",
                    data.get_country(name="Uruguay"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Venezuela",
                    data.get_country(name="Venezuela"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Vietnam",
                    data.get_country(name="Vietnam"),
                    data.get_translation_set(name="French"),
                ],
                ["Yémen", data.get_country(name="Yemen"), data.get_translation_set(name="French")],
                [
                    "Zambie",
                    data.get_country(name="Zambia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Zimbabwe",
                    data.get_country(name="Zimbabwe"),
                    data.get_translation_set(name="French"),
                ],
                ["Égypte", data.get_country(name="Egypt"), data.get_translation_set(name="French")],
                [
                    "Émirats arabes unis",
                    data.get_country(name="United Arab Emirates"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Équateur",
                    data.get_country(name="Ecuador"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "États fédérés de Micronésie",
                    data.get_country(name="Micronesia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "États-Unis",
                    data.get_country(name="USA"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Éthiopie",
                    data.get_country(name="Ethiopia"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Îles Féroé",
                    data.get_country(name="Faroe Islands"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Îles Malouines",
                    data.get_country(name="Falkland Islands"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Îles Salomon",
                    data.get_country(name="Soloman Islands"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Îles Vierges britanniques",
                    data.get_country(name="British Virgin Islands"),
                    data.get_translation_set(name="French"),
                ],
                [
                    "Afeganistão",
                    data.get_country(name="Afghanistan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Albânia",
                    data.get_country(name="Albania"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Alemanha",
                    data.get_country(name="Germany"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Angola",
                    data.get_country(name="Angola"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Argentina",
                    data.get_country(name="Argentina"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Argélia",
                    data.get_country(name="Algeria"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Armênia",
                    data.get_country(name="Armenia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Aruba",
                    data.get_country(name="Aruba"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Arábia Saudita",
                    data.get_country(name="Saudi Arabia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Austrália",
                    data.get_country(name="Australia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Azerbaijão",
                    data.get_country(name="Azerbaijan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bahamas",
                    data.get_country(name="Bahamas"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bahrein",
                    data.get_country(name="Bahrain"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bangladesh",
                    data.get_country(name="Bangladesh"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Barbados",
                    data.get_country(name="Barbados"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Belize",
                    data.get_country(name="Belize"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Benin",
                    data.get_country(name="Benin"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bermudas",
                    data.get_country(name="Bermuda"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bielorrússia",
                    data.get_country(name="Belarus"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bolívia",
                    data.get_country(name="Bolivia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Botsuana",
                    data.get_country(name="Botswana"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Brasil",
                    data.get_country(name="Brazil"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Brunei",
                    data.get_country(name="Brunei"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bulgária",
                    data.get_country(name="Bulgaria"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Butão",
                    data.get_country(name="Bhutan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bélgica",
                    data.get_country(name="Belgium"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Bósnia e Herzegovina",
                    data.get_country(name="Bosnia and Herzegovina"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Camboja",
                    data.get_country(name="Cambodia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Canadá",
                    data.get_country(name="Canada"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Catar",
                    data.get_country(name="Qatar"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Cazaquistão",
                    data.get_country(name="Kazakhstan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Chile",
                    data.get_country(name="Chile"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "China",
                    data.get_country(name="China"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Chipre",
                    data.get_country(name="Cyprus"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Cingapura",
                    data.get_country(name="Singapore"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Colômbia",
                    data.get_country(name="Colombia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Congo - Brazzaville",
                    data.get_country(name="Congo"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Congo - Kinshasa",
                    data.get_country(name="Congo (Dem. Republic)"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Coreia do Norte",
                    data.get_country(name="Korea (North)"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Coreia do Sul",
                    data.get_country(name="Korea (South)"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Costa Rica",
                    data.get_country(name="Costa Rica"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Costa do Marfim",
                    data.get_country(name="Cote d'Ivoire"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Croácia",
                    data.get_country(name="Croatia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Cuba",
                    data.get_country(name="Cuba"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Dinamarca",
                    data.get_country(name="Denmark"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Dominica",
                    data.get_country(name="Dominica"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Egito",
                    data.get_country(name="Egypt"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "El Salvador",
                    data.get_country(name="El Salvador"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Emirados Árabes Unidos",
                    data.get_country(name="United Arab Emirates"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Equador",
                    data.get_country(name="Ecuador"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Eslováquia",
                    data.get_country(name="the Slovak Republic"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Eslovênia",
                    data.get_country(name="Slovenia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Espanha",
                    data.get_country(name="Spain"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Estados Unidos",
                    data.get_country(name="USA"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Estônia",
                    data.get_country(name="Estonia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Etiópia",
                    data.get_country(name="Ethiopia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Filipinas",
                    data.get_country(name="Philippines"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Finlândia",
                    data.get_country(name="Finland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "França",
                    data.get_country(name="France"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Gabão",
                    data.get_country(name="Gabon"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Gana",
                    data.get_country(name="Ghana"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Geórgia",
                    data.get_country(name="Georgia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Gibraltar",
                    data.get_country(name="Gibraltar"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Groenlândia",
                    data.get_country(name="Greenland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Grécia",
                    data.get_country(name="Greece"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Guatemala",
                    data.get_country(name="Guatemala"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Guernsey",
                    data.get_country(name="Guernsey"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Guiana",
                    data.get_country(name="Guyana"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Guiné",
                    data.get_country(name="Guinea"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Guiné Equatorial",
                    data.get_country(name="Equatorial Guinea"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Gâmbia",
                    data.get_country(name="Gambia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Haiti",
                    data.get_country(name="Haiti"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Holanda",
                    data.get_country(name="Netherlands"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Honduras",
                    data.get_country(name="Honduras"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Hong Kong, RAE da China",
                    data.get_country(name="Hong Kong"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Hungria",
                    data.get_country(name="Hungary"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ilhas Faroe",
                    data.get_country(name="Faroe Islands"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ilhas Malvinas",
                    data.get_country(name="Falkland Islands"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ilhas Salomão",
                    data.get_country(name="Soloman Islands"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ilhas Virgens Britânicas",
                    data.get_country(name="British Virgin Islands"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Indonésia",
                    data.get_country(name="Indonesia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Iraque",
                    data.get_country(name="Iraq"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Irlanda",
                    data.get_country(name="Irish Republic"),
                    data.get_translation_set(name="Portuguese"),
                ],
                ["Irã", data.get_country(name="Iran"), data.get_translation_set(name="Portuguese")],
                [
                    "Islândia",
                    data.get_country(name="Iceland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Israel",
                    data.get_country(name="Israel"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Itália",
                    data.get_country(name="Italy"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Iêmen",
                    data.get_country(name="Yemen"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Jamaica",
                    data.get_country(name="Jamaica"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Japão",
                    data.get_country(name="Japan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Jersey",
                    data.get_country(name="Jersey"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Jordânia",
                    data.get_country(name="Jordan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Kosovo",
                    data.get_country(name="Kosovo"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Kuwait",
                    data.get_country(name="Kuwait"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Laos",
                    data.get_country(name="Laos"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Letônia",
                    data.get_country(name="Latvia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Libéria",
                    data.get_country(name="Liberia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Liechtenstein",
                    data.get_country(name="Liechtenstein"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Lituânia",
                    data.get_country(name="Lithuania"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Luxemburgo",
                    data.get_country(name="Luxembourg"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Líbano",
                    data.get_country(name="Lebanon"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Líbia",
                    data.get_country(name="Libya"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Macau, RAE da China",
                    data.get_country(name="Macao"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Macedônia",
                    data.get_country(name="Macedonia, Former Yugoslav Republic of"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Madagascar",
                    data.get_country(name="Madagascar"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Maldivas",
                    data.get_country(name="Maldives"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Mali",
                    data.get_country(name="Mali"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Malta",
                    data.get_country(name="Malta"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Malásia",
                    data.get_country(name="Malaysia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Marrocos",
                    data.get_country(name="Morocco"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Mauritânia",
                    data.get_country(name="Mauritania"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Maurício",
                    data.get_country(name="Mauritius"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Mianmar (Birmânia)",
                    data.get_country(name="Myanmar (Burma)"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Micronésia",
                    data.get_country(name="Micronesia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Moldávia",
                    data.get_country(name="Moldova"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Mongólia",
                    data.get_country(name="Mongolia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Montenegro",
                    data.get_country(name="Montenegro"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Moçambique",
                    data.get_country(name="Mozambique"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "México",
                    data.get_country(name="Mexico"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Namíbia",
                    data.get_country(name="Namibia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Nauru",
                    data.get_country(name="Nauru"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Nepal",
                    data.get_country(name="Nepal"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Nicarágua",
                    data.get_country(name="Nicaragua"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Nigéria",
                    data.get_country(name="Nigeria"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Noruega",
                    data.get_country(name="Norway"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Nova Zelândia",
                    data.get_country(name="New Zealand"),
                    data.get_translation_set(name="Portuguese"),
                ],
                ["Omã", data.get_country(name="Oman"), data.get_translation_set(name="Portuguese")],
                [
                    "Panamá",
                    data.get_country(name="Panama"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Papua-Nova Guiné",
                    data.get_country(name="Papua New Guinea"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Paquistão",
                    data.get_country(name="Pakistan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Paraguai",
                    data.get_country(name="Paraguay"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Peru",
                    data.get_country(name="Peru"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Polônia",
                    data.get_country(name="Poland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Porto Rico",
                    data.get_country(name="Puerto Rico"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Portugal",
                    data.get_country(name="Portugal"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Quirguistão",
                    data.get_country(name="Kyrgyzstan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Quênia",
                    data.get_country(name="Kenya"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Reino Unido",
                    data.get_country(name="United Kingdom"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "República Dominicana",
                    data.get_country(name="Dominican Republic"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Romênia",
                    data.get_country(name="Romania"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ruanda",
                    data.get_country(name="Rwanda"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Rússia",
                    data.get_country(name="Russian Federation"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Santa Helena",
                    data.get_country(name="Saint Helena"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Seicheles",
                    data.get_country(name="Seychelles"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Senegal",
                    data.get_country(name="Senegal"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Somália",
                    data.get_country(name="Somalia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Sri Lanka",
                    data.get_country(name="Sri Lanka"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Suazilândia",
                    data.get_country(name="Swaziland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Sudão",
                    data.get_country(name="Sudan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Suriname",
                    data.get_country(name="Suriname"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Suécia",
                    data.get_country(name="Sweden"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Suíça",
                    data.get_country(name="Switzerland"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Sérvia",
                    data.get_country(name="Serbia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Síria",
                    data.get_country(name="Syria"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Tailândia",
                    data.get_country(name="Thailand"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Taiwan",
                    data.get_country(name="Taiwan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Tajiquistão",
                    data.get_country(name="Tajikistan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Tanzânia",
                    data.get_country(name="Tanzania"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Tchéquia",
                    data.get_country(name="the Czech Republic"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Territórios palestinos",
                    data.get_country(name="Occupied Palestinian Territories"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Trinidad e Tobago",
                    data.get_country(name="Trinidad & Tobago"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Tunísia",
                    data.get_country(name="Tunisia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Turcomenistão",
                    data.get_country(name="Turkmenistan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Turquia",
                    data.get_country(name="Turkey"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Ucrânia",
                    data.get_country(name="Ukraine"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Uruguai",
                    data.get_country(name="Uruguay"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Uzbequistão",
                    data.get_country(name="Uzbekistan"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Venezuela",
                    data.get_country(name="Venezuela"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Vietnã",
                    data.get_country(name="Vietnam"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Zimbábue",
                    data.get_country(name="Zimbabwe"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Zâmbia",
                    data.get_country(name="Zambia"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "África do Sul",
                    data.get_country(name="South Africa"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Áustria",
                    data.get_country(name="Austria"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Índia",
                    data.get_country(name="India"),
                    data.get_translation_set(name="Portuguese"),
                ],
                [
                    "Австралия",
                    data.get_country(name="Australia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Австрия",
                    data.get_country(name="Austria"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Азербайджан",
                    data.get_country(name="Azerbaijan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Албания",
                    data.get_country(name="Albania"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Алжир",
                    data.get_country(name="Algeria"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Ангола",
                    data.get_country(name="Angola"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Аргентина",
                    data.get_country(name="Argentina"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Армения",
                    data.get_country(name="Armenia"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Аруба", data.get_country(name="Aruba"), data.get_translation_set(name="Russian")],
                [
                    "Афганистан",
                    data.get_country(name="Afghanistan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Багамы",
                    data.get_country(name="Bahamas"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бангладеш",
                    data.get_country(name="Bangladesh"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Барбадос",
                    data.get_country(name="Barbados"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бахрейн",
                    data.get_country(name="Bahrain"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Беларусь",
                    data.get_country(name="Belarus"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Белиз",
                    data.get_country(name="Belize"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бельгия",
                    data.get_country(name="Belgium"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Бенин", data.get_country(name="Benin"), data.get_translation_set(name="Russian")],
                [
                    "Бермуды",
                    data.get_country(name="Bermuda"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Болгария",
                    data.get_country(name="Bulgaria"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Боливия",
                    data.get_country(name="Bolivia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Босния и Герцеговина",
                    data.get_country(name="Bosnia and Herzegovina"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Ботсвана",
                    data.get_country(name="Botswana"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бразилия",
                    data.get_country(name="Brazil"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бруней-Даруссалам",
                    data.get_country(name="Brunei"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Бутан",
                    data.get_country(name="Bhutan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Великобритания",
                    data.get_country(name="United Kingdom"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Венгрия",
                    data.get_country(name="Hungary"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Венесуэла",
                    data.get_country(name="Venezuela"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Виргинские о-ва (Британские)",
                    data.get_country(name="British Virgin Islands"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Вьетнам",
                    data.get_country(name="Vietnam"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Габон", data.get_country(name="Gabon"), data.get_translation_set(name="Russian")],
                ["Гаити", data.get_country(name="Haiti"), data.get_translation_set(name="Russian")],
                [
                    "Гайана",
                    data.get_country(name="Guyana"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гамбия",
                    data.get_country(name="Gambia"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Гана", data.get_country(name="Ghana"), data.get_translation_set(name="Russian")],
                [
                    "Гватемала",
                    data.get_country(name="Guatemala"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гвинея",
                    data.get_country(name="Guinea"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Германия",
                    data.get_country(name="Germany"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гернси",
                    data.get_country(name="Guernsey"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гибралтар",
                    data.get_country(name="Gibraltar"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гондурас",
                    data.get_country(name="Honduras"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гонконг (специальный административный район)",
                    data.get_country(name="Hong Kong"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Гренландия",
                    data.get_country(name="Greenland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Греция",
                    data.get_country(name="Greece"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Грузия",
                    data.get_country(name="Georgia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Дания",
                    data.get_country(name="Denmark"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Джерси",
                    data.get_country(name="Jersey"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Доминика",
                    data.get_country(name="Dominica"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Доминиканская Республика",
                    data.get_country(name="Dominican Republic"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Египет",
                    data.get_country(name="Egypt"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Замбия",
                    data.get_country(name="Zambia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Зимбабве",
                    data.get_country(name="Zimbabwe"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Израиль",
                    data.get_country(name="Israel"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Индия", data.get_country(name="India"), data.get_translation_set(name="Russian")],
                [
                    "Индонезия",
                    data.get_country(name="Indonesia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Иордания",
                    data.get_country(name="Jordan"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Ирак", data.get_country(name="Iraq"), data.get_translation_set(name="Russian")],
                ["Иран", data.get_country(name="Iran"), data.get_translation_set(name="Russian")],
                [
                    "Ирландия",
                    data.get_country(name="Irish Republic"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Исландия",
                    data.get_country(name="Iceland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Испания",
                    data.get_country(name="Spain"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Италия",
                    data.get_country(name="Italy"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Йемен", data.get_country(name="Yemen"), data.get_translation_set(name="Russian")],
                [
                    "КНДР",
                    data.get_country(name="Korea (North)"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Казахстан",
                    data.get_country(name="Kazakhstan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Камбоджа",
                    data.get_country(name="Cambodia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Канада",
                    data.get_country(name="Canada"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Катар", data.get_country(name="Qatar"), data.get_translation_set(name="Russian")],
                ["Кения", data.get_country(name="Kenya"), data.get_translation_set(name="Russian")],
                ["Кипр", data.get_country(name="Cyprus"), data.get_translation_set(name="Russian")],
                [
                    "Киргизия",
                    data.get_country(name="Kyrgyzstan"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Китай", data.get_country(name="China"), data.get_translation_set(name="Russian")],
                [
                    "Колумбия",
                    data.get_country(name="Colombia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Конго - Браззавиль",
                    data.get_country(name="Congo"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Конго - Киншаса",
                    data.get_country(name="Congo (Dem. Republic)"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Косово",
                    data.get_country(name="Kosovo"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Коста-Рика",
                    data.get_country(name="Costa Rica"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Кот-д’Ивуар",
                    data.get_country(name="Cote d'Ivoire"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Куба", data.get_country(name="Cuba"), data.get_translation_set(name="Russian")],
                [
                    "Кувейт",
                    data.get_country(name="Kuwait"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Лаос", data.get_country(name="Laos"), data.get_translation_set(name="Russian")],
                [
                    "Латвия",
                    data.get_country(name="Latvia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Либерия",
                    data.get_country(name="Liberia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Ливан",
                    data.get_country(name="Lebanon"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Ливия", data.get_country(name="Libya"), data.get_translation_set(name="Russian")],
                [
                    "Литва",
                    data.get_country(name="Lithuania"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Лихтенштейн",
                    data.get_country(name="Liechtenstein"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Люксембург",
                    data.get_country(name="Luxembourg"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Маврикий",
                    data.get_country(name="Mauritius"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мавритания",
                    data.get_country(name="Mauritania"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мадагаскар",
                    data.get_country(name="Madagascar"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Макао (специальный административный район)",
                    data.get_country(name="Macao"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Македония",
                    data.get_country(name="Macedonia, Former Yugoslav Republic of"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Малайзия",
                    data.get_country(name="Malaysia"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Мали", data.get_country(name="Mali"), data.get_translation_set(name="Russian")],
                [
                    "Мальдивы",
                    data.get_country(name="Maldives"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мальта",
                    data.get_country(name="Malta"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Марокко",
                    data.get_country(name="Morocco"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мексика",
                    data.get_country(name="Mexico"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мозамбик",
                    data.get_country(name="Mozambique"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Молдова",
                    data.get_country(name="Moldova"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Монголия",
                    data.get_country(name="Mongolia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Мьянма (Бирма)",
                    data.get_country(name="Myanmar (Burma)"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Намибия",
                    data.get_country(name="Namibia"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Науру", data.get_country(name="Nauru"), data.get_translation_set(name="Russian")],
                ["Непал", data.get_country(name="Nepal"), data.get_translation_set(name="Russian")],
                [
                    "Нигерия",
                    data.get_country(name="Nigeria"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Нидерланды",
                    data.get_country(name="Netherlands"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Никарагуа",
                    data.get_country(name="Nicaragua"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Новая Зеландия",
                    data.get_country(name="New Zealand"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Норвегия",
                    data.get_country(name="Norway"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "ОАЭ",
                    data.get_country(name="United Arab Emirates"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Оман", data.get_country(name="Oman"), data.get_translation_set(name="Russian")],
                [
                    "Пакистан",
                    data.get_country(name="Pakistan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Палестинские территории",
                    data.get_country(name="Occupied Palestinian Territories"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Панама",
                    data.get_country(name="Panama"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Папуа – Новая Гвинея",
                    data.get_country(name="Papua New Guinea"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Парагвай",
                    data.get_country(name="Paraguay"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Перу", data.get_country(name="Peru"), data.get_translation_set(name="Russian")],
                [
                    "Польша",
                    data.get_country(name="Poland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Португалия",
                    data.get_country(name="Portugal"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Пуэрто-Рико",
                    data.get_country(name="Puerto Rico"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Республика Корея",
                    data.get_country(name="Korea (South)"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Россия",
                    data.get_country(name="Russian Federation"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Руанда",
                    data.get_country(name="Rwanda"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Румыния",
                    data.get_country(name="Romania"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сальвадор",
                    data.get_country(name="El Salvador"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Саудовская Аравия",
                    data.get_country(name="Saudi Arabia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Свазиленд",
                    data.get_country(name="Swaziland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сейшельские Острова",
                    data.get_country(name="Seychelles"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сенегал",
                    data.get_country(name="Senegal"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сербия",
                    data.get_country(name="Serbia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сингапур",
                    data.get_country(name="Singapore"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Сирия", data.get_country(name="Syria"), data.get_translation_set(name="Russian")],
                [
                    "Словакия",
                    data.get_country(name="the Slovak Republic"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Словения",
                    data.get_country(name="Slovenia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Соединенные Штаты",
                    data.get_country(name="USA"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Соломоновы Острова",
                    data.get_country(name="Soloman Islands"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Сомали",
                    data.get_country(name="Somalia"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Судан", data.get_country(name="Sudan"), data.get_translation_set(name="Russian")],
                [
                    "Суринам",
                    data.get_country(name="Suriname"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Таджикистан",
                    data.get_country(name="Tajikistan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Таиланд",
                    data.get_country(name="Thailand"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Тайвань",
                    data.get_country(name="Taiwan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Танзания",
                    data.get_country(name="Tanzania"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Тринидад и Тобаго",
                    data.get_country(name="Trinidad & Tobago"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Тунис",
                    data.get_country(name="Tunisia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Туркменистан",
                    data.get_country(name="Turkmenistan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Турция",
                    data.get_country(name="Turkey"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Узбекистан",
                    data.get_country(name="Uzbekistan"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Украина",
                    data.get_country(name="Ukraine"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Уругвай",
                    data.get_country(name="Uruguay"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Фарерские о-ва",
                    data.get_country(name="Faroe Islands"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Федеративные Штаты Микронезии",
                    data.get_country(name="Micronesia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Филиппины",
                    data.get_country(name="Philippines"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Финляндия",
                    data.get_country(name="Finland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Фолклендские о-ва",
                    data.get_country(name="Falkland Islands"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Франция",
                    data.get_country(name="France"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Хорватия",
                    data.get_country(name="Croatia"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Черногория",
                    data.get_country(name="Montenegro"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Чехия",
                    data.get_country(name="the Czech Republic"),
                    data.get_translation_set(name="Russian"),
                ],
                ["Чили", data.get_country(name="Chile"), data.get_translation_set(name="Russian")],
                [
                    "Швейцария",
                    data.get_country(name="Switzerland"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Швеция",
                    data.get_country(name="Sweden"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Шри-Ланка",
                    data.get_country(name="Sri Lanka"),
                    data.get_translation_set(name="Russian"),
                ],
                [
                    "Эквадор",
                    data.get_country(name="Ecuador"),
                    data.get_translation_set(name="Russian"),
                ],
            ]
        ]
    )
