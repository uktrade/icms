import jinja2
from django.template.backends.jinja2 import Jinja2


class EcilJinja2Backend(Jinja2):
    app_dirname = "jinja2"

    def __init__(self, params):
        params = params.copy()
        self.dirs = list(params.get("DIRS"))
        self.app_dirs = params.get("APP_DIRS")

        params["OPTIONS"]["loader"] = jinja2.ChoiceLoader(
            [
                jinja2.FileSystemLoader(self.template_dirs),
                jinja2.PrefixLoader(
                    {"govuk_frontend_jinja": jinja2.PackageLoader("govuk_frontend_jinja")}
                ),
            ]
        )

        super().__init__(params)
