from django.shortcuts import render
import django_filters as filter
from web.base.forms.forms import FilterSet
# from web.base.utils import dict_merge
from web.models import User
from .filters import _filter_config


