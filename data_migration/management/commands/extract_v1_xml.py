from itertools import islice

from ._base import MigrationBaseCommand
from .config.run_order import DATA_TYPE, DATA_TYPE_XML
from .utils.format import format_name


class Command(MigrationBaseCommand):
    help = """Parses the XML for data stored in the data migration models xml columns"""

    DATA_TYPE_START = {
        "user": ["u", "user"],
        "import_application": ["ia", "import_application"],
        "export_application": ["ea", "export_application"],
    }

    def handle(self, *args, **options):
        super().handle(*args, **options)

        self._extract_xml_data("user", options["skip_user"])
        self._extract_xml_data("import_application", options["skip_ia"])
        self._extract_xml_data("export_application", options["skip_export"])
        self._log_script_end()

    def _extract_xml_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        """Iterates over the models listed for the specified data_type and parses the xml from their parent"""

        if not self._get_start_type(data_type):
            return

        parser_list = DATA_TYPE_XML[data_type]
        start, parser_list = self._get_data_list(parser_list)
        name = format_name(data_type)

        if skip:
            self.log(f"Skipping {name} XML Parsing")
            return

        self.log(f"Extracting xml data for {name}")

        for idx, parser in enumerate(parser_list, start=start):
            self.log("\t" + parser.log_message(idx))
            objs = parser.get_queryset()
            count = 0

            while True:
                batch = list(islice(objs, self.batch_size))

                if not batch:
                    break

                for model, data in parser.parse_xml(batch).items():
                    created = model.objects.bulk_create(data)
                    count += len(created)

            self._log_time(count=count)

        self.log("XML extraction complete")
