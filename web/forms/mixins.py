import structlog as logging
from django.forms import Form

logger = logging.getLogger(__name__)


class ReadonlyFormMixin(Form):
    """ Makes forms read only, prevents changing any data"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].disabled = True

    def save(self, *args, **kwargs):
        pass
