from django.core.serializers.json import DjangoJSONEncoder
import json


class FormSerializeMixin(object):
    def data_dict(self):
        data = {}
        fields = self.Meta.serialize if hasattr(
            self.Meta, 'serialize') else self.Meta.fields
        for field in fields:
            value = self.cleaned_data.get(field, None)
            if value:
                data[field] = self.cleaned_data.get(field, None)
        return data

    def serialize(self):
        return json.dumps(self.data_dict(), cls=DjangoJSONEncoder)
