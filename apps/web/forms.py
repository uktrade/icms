from django.contrib.auth.forms import AuthenticationForm
import logging

logger = logging.getLogger(__name__)


class LoginForm(AuthenticationForm):
    print('Initialising login form')
    pass
