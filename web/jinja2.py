from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib import messages
from django.urls import reverse
from jinja2 import Environment
from web.base.utils import dict_merge


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_messages': messages.get_messages,
        'dict_merge': dict_merge
    })
    return env
