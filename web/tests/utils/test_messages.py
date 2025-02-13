from unittest.mock import patch

from django.contrib.messages import Message, constants

from web.utils.messages import get_messages


@patch(
    "web.utils.messages.django_get_messages",
    return_value=[
        Message(constants.INFO, "Test message", "tag"),
        Message(constants.WARNING, "Test message", "safe"),
        Message(constants.WARNING, "Test message"),
    ],
)
def test_messages(rf):
    messages = get_messages(rf)
    assert len(messages) == 3
    assert messages[0].class_list == ["info-box", "info-box-tag", "info-box-info"]
    assert messages[0].safe is False

    assert messages[1].class_list == ["info-box", "info-box-safe", "info-box-warning"]
    assert messages[1].safe is True

    assert messages[2].class_list == ["info-box", "info-box-warning"]
    assert messages[2].safe is False
