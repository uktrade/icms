from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


# All options available here:
# https://design-system.service.gov.uk/components/notification-banner/
class NotificationBannerKwargs(TextOrHTMLMixin, BaseModel):
    # Required. The text that displays in the notification banner.
    # You can use any string with this option.
    # If you set html, this option is not required and is ignored.
    text: str | None = None
    # Required. The HTML to use within the notification banner.
    # You can use any string with this option.
    # If you set html, text is not required and is ignored.
    html: str | None = None
    # nunjucks-block - Not strictly a parameter but Nunjucks code convention.
    # Using a call block enables you to call a macro with all the text inside the tag.
    # This is helpful if you want to pass a lot of content into a macro.
    # To use it, you will need to wrap the entire notification banner component in a call block.
    caller: Any | None = None
    # The title text that displays in the notification banner.
    # You can use any string with this option.
    # Use this option to set text that does not contain HTML.
    # The available default values are ‘Important’, ‘Success’, and None:
    #   - if you do not set type, titleText defaults to "Important"
    #   - if you set type to success, titleText defaults to "Success"
    #   - if you set titleHtml, this option is ignored
    titleText: str | None = None
    # The title HTML to use within the notification banner.
    # You can use any string with this option.
    # Use this option to set text that contains HTML.
    # If you set titleHtml, the titleText option is ignored.
    titleHtml: str | None = None
    # Sets heading level for the title only.
    # You can only use values between 1 and 6 with this option.
    # The default is 2.
    titleHeadingLevel: str | None = None
    # The type of notification to render.
    # You can use only "success" or null values with this option.
    # If you set type to "success", the notification banner sets role to "alert".
    # JavaScript then moves the keyboard focus to the notification banner when the page loads.
    # If you do not set type, the notification banner sets role to "region".
    type: str | None = None
    # Overrides the value of the role attribute for the notification banner.
    # Defaults to "region".
    # If you set type to "success", role defaults to "alert".
    role: str | None = None
    # The id for the banner title, and the aria-labelledby attribute in the banner.
    # Defaults to "govuk-notification-banner-title".
    titleId: str | None = None
    # If you set type to "success", or role to "alert", JavaScript moves the keyboard focus to the notification banner when the page loads.
    # To disable this behaviour, set disableAutoFocus to true.
    disableAutoFocus: bool | None = None
    # The classes that you want to add to the notification banner.
    classes: str | None = None
    # The HTML attributes that you want to add to the notification banner, for example, data attributes.
    attributes: dict[str, Any] | None = None
