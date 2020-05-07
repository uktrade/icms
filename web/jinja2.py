import re
from datetime import datetime

import pytz
from compressor.contrib.jinja2ext import CompressorExtension
from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils.formats import get_format
from jinja2 import Environment, evalcontextfilter
from markupsafe import Markup, escape


@evalcontextfilter
def nl2br(eval_ctx, value):
    paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    paragraphs = paragraph_re.split(escape(value))
    html = ('<p>{}</p>'.format(p.replace('\n', Markup('<br>\n')))
            for p in paragraphs)
    result = '\n\n'.join(html)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def show_all_attrs(value):
    res = []
    for k in dir(value):
        res.append('%r %r\n' % (k, getattr(value, k)))
    return '\n'.join(res)


def input_datetime(value):
    """
        Convert a utc datetime from string to input date format
    """
    if not value:
        return ''

    input_formats = get_format('DATETIME_INPUT_FORMATS')
    for format in input_formats:
        try:
            datetime.strptime(value, format)
            return value
        except ValueError:
            continue

    local_timezone = pytz.timezone(settings.TIME_ZONE)
    naive_datetime = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
    local_datetime = local_timezone.localize(naive_datetime, is_dst=None)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    for format in get_format('DATETIME_INPUT_FORMATS'):
        try:
            return utc_datetime.strftime(format)
        except (ValueError, TypeError):
            continue

    return value


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
    env.filters['input_datetime'] = input_datetime
    env.filters['nl2br'] = nl2br
    return env
