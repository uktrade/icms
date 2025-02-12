from django.contrib.messages import Message
from django.contrib.messages import get_messages as django_get_messages
from django.http import HttpRequest


def get_messages(request: HttpRequest) -> list[Message]:
    """
    Return the message storage on the request if it exists, add some display classes, otherwise return
    an empty list.
    """
    messages = django_get_messages(request)
    for message in messages:
        message.class_list = ["info-box"] + [f"info-box-{tag}" for tag in message.tags.split()]
        if message.extra_tags and "safe" in message.extra_tags:
            message.safe = True
        else:
            message.safe = False
    return messages
