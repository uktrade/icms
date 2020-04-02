import structlog as logging
from django.template.loader import render_to_string

from . import email

# Get an instance of a logger
logger = logging.getLogger(__name__)


def register(request, user, password):
    logger.debug('Notifying user for registration', user=user)
    subject = 'Import Case Management System Account '
    message = render_to_string('email/registration/registration.html',
                               {'password': password}, request)
    email.email_user(subject, user, message)


def access_request_admin(user, access_request):
    logger.debug('Notifying admins for new access request',
                 user=user,
                 access_request=access_request)
    subject = 'Import Case Management System Account'
    message = render_to_string('email/access/admin.html', {
        'subject': subject,
        'user': user,
        'access_request': access_request
    })
    email.email_user(subject, user, message)


def access_request_requester(access_request):
    logger.debug('Notifying user for new access request',
                 access_request=access_request)
    requester = access_request.submitted_by
    subject = 'Import Case Management System Account'
    message = render_to_string('email/access/requester.html', {
        'subject': subject,
        'user': requester,
        'access_request': access_request
    })
    email.email_user(subject, requester, message)
