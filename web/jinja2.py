from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def show_all_attrs(value):
    res = []
    for k in dir(value):
        res.append('%r %r\n' % (k, getattr(value, k)))
    return '\n'.join(res)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_messages': messages.get_messages
    })
    env.filters['show_all_attrs'] = show_all_attrs
    return env
