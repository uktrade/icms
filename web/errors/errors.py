from typing import Any


class APIError(Exception):
    def __init__(self, error_msg: str, dev_error_msg: str, status_code: Any = None) -> None:
        """Exception returned for known errors when interacting with 3rd party APIs.

        :param error_msg: Error message suitable to show user.
        :param dev_error_msg: Detailed error message.
        :param status_code: Status code from external API
        """

        self.error_msg = error_msg
        self.dev_error_msg = dev_error_msg
        self.status_code = status_code

        super().__init__(error_msg)

    def __str__(self):
        return f"APIError(error_msg={self.error_msg!r}, dev_error_msg={self.dev_error_msg!r}, status_code={self.status_code!r})"
