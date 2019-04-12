from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def fetch_email_templates(client):
    templates = {}
    response = client.get_all_templates(template_type="email")
    for template in response['templates']:
        logger.debug('Template: %r', template)
        templates[template['name']] = {
            'name': template['name'],
            'id': template['id']
        }

    logger.debug('Fetched templates %r', templates)
    return templates


def client():
    if settings.EMAIL_API_KEY:
        return NotificationsAPIClient(settings.EMAIL_API_KEY)
    else:
        logger.warning('GDS Notify not configured. Dumping emails to console')
        return EmailDumper()


def get_template(template_name):
    templates = fetch_email_templates(client())
    return templates[template_name]


def send(template_name, user, context={}):
    template = get_template(template_name)
    logger.debug('Sending template: %s to user: %s', template['name'],
                 user.username)
    logger.debug('email:%s', user.email)
    client().send_email_notification(
        user.email,
        template['id'],
        context,
        email_reply_to_id=settings.EMAIL_REPLY_TO_ID)


class EmailDumper():
    def send_email_notification(self,
                                email_address,
                                template,
                                personalisation=None,
                                reference=None,
                                email_reply_to_id=None):
        logger.debug('Dumping email notification:')
        logger.debug('To: %s', email_address)
        logger.debug('Template Id: %s', template)
        logger.debug('Personalisation %r', personalisation)
        logger.debug('Reference: %s', reference)
        logger.debug('Reply To Id: %s', email_reply_to_id)
