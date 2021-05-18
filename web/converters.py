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
    regex = "CFS|COM"

    def to_python(self, value):
        return value

    def to_url(self, value):

        if value not in ["CFS", "COM"]:
            raise ValueError

        return value


class SILSectionTypeConverter:
    regex = "section1|section2|section5|section582-obsolete|section582-other"

    def to_python(self, value):
        return value

    def to_url(self, value):
        if value not in [
            "section1",
            "section2",
            "section5",
            "section582-obsolete",
            "section582-other",
        ]:
            raise ValueError

        return value
