import re

from compressor.contrib.jinja2ext import CompressorExtension
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment, evalcontextfilter
from markupsafe import Markup, escape


@evalcontextfilter
def nl2br(eval_ctx, value):
    paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    paragraphs = paragraph_re.split(escape(value))
    html = ('<p>%s</p>' % p.replace('\n', Markup('<br>\n')) for p in paragraphs)
    result = '\n\n'.join(html)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def show_all_attrs(value):
    res = []
    for k in dir(value):
        res.append('%r %r\n' % (k, getattr(value, k)))
    return '\n'.join(res)


def modify_query(request, **new_params):
    params = request.GET.copy()
    for k, v in new_params.items():
        params[k] = v
    return request.build_absolute_uri('?' + params.urlencode())


def environment(**options):
    env = Environment(extensions=[CompressorExtension], **options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'get_messages': messages.get_messages,
        'modify_query': modify_query
    })
    env.filters['show_all_attrs'] = show_all_attrs
    env.filters['nl2br'] = nl2br
    return env
