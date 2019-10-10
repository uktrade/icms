from . import email
from django.template.loader import render_to_string
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def register(request, user, password):
    logger.debug('Notifying %s for registration', user)
    subject = 'Import Case Management System Account '
    message = render_to_string('email/registration/registration.html', {
        'subject': subject,
        'user': user,
        'password': password
    }, request)
    # Logged only on debug
    logger.debug('Temporary password for %s: %s', user.first_name, password)
    email.send(subject, user, message)
