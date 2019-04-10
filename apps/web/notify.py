from icms import email
import logging

# GDS Notify template names
__registration = 'registration'

# Get an instance of a logger
logger = logging.getLogger(__name__)


def register(user, password):
    logger.debug('Notifying %s %s', user, password)
    email.send(
        __registration, user, {
            'title': user.title,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'login': user.username,
            'password': password
        })
