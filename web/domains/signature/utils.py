import base64

from web.utils.s3 import get_file_from_s3

from .models import Signature


def get_signature_file_base64(signature: Signature) -> str:  # /PS-IGNORE
    """Fetch the signature file object from s3 and return as a base64 string

    :param signature: Signature object:
    :return: base64 file string
    """
    signature_file = get_file_from_s3(signature.path)
    encoded_bytes = base64.b64encode(signature_file)  # /PS-IGNORE
    return encoded_bytes.decode()


def get_active_signature_file() -> tuple[Signature, str]:
    """Fetch the active signature and base64 file string

    :return: Signature object, base64 file string
    """
    signature = Signature.objects.get(is_active=True)
    return signature, get_signature_file_base64(signature)  # /PS-IGNORE
