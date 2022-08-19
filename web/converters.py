class NegativeIntConverter:
    regex = r"-?\d+"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%d" % value


class CaseTypeConverter:
    regex = "import|export|access"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in ["import", "export", "access"]:
            raise ValueError

        return value


class ExportApplicationTypeConverter:
    regex = "cfs|com|gmp"

    def to_python(self, value):
        return value.upper()

    def to_url(self, value):
        if value not in ["cfs", "com", "gmp"]:
            raise ValueError

        return value


class SILSectionTypeConverter:
    regex = "section1|section2|section5|section582-obsolete|section582-other|section_legacy"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in [
            "section1",
            "section2",
            "section5",
            "section582-obsolete",
            "section582-other",
            "section_legacy",
        ]:
            raise ValueError

        return value


class EntityTypeConverter:
    regex = "individual|organisation"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in ["individual", "organisation"]:
            raise ValueError

        return value


class OrgTypeConverter:
    regex = "importer|exporter"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in ["importer", "exporter"]:
            raise ValueError

        return value


class ChiefStatusConverter:
    regex = "success|failure"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in ["success", "failure"]:
            raise ValueError

        return value
