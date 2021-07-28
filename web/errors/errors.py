class APIError(Exception):
    def __init__(self, error_msg: str, dev_error_msg: str) -> None:
        """Exception returned for known errors when interacting with 3rd party apis.

        :param error_msg: Error message suitable to show user.
        :param dev_error_msg: Detailed error message.
        """

        self.error_msg = error_msg
        self.dev_error_msg = dev_error_msg

        super().__init__(error_msg)

    def __str__(self):
        return f"APIError(error_msg={self.error_msg!r}, dev_error_msg={self.dev_error_msg!r})"
