import requests


class InfectedFileException(Exception):
    pass


class ClamAV():
    """
    Helper class to use ClamAV rest api to scan files
    """
    def __init__(self, username, password, endpoint):
        self.username = username
        self.password = password
        self.endpoint = endpoint

    def is_safe(self, bytes_string):
        scan_status = requests.post(
            self.endpoint,
            auth=(self.username, self.password,),
            files={"file": bytes_string},
        ).json()

        return not scan_status['malware'] if 'malware' in scan_status else False
