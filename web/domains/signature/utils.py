import base64

from web.utils.s3 import get_file_from_s3

from .models import Signature


def get_signature_file_bytes(signature: Signature) -> bytes:
    """Fetch the signature file object from s3 and return as bytes

    :param signature: Signature object:
    :return: file bytes
    """
    return get_file_from_s3(signature.path)


def get_signature_file_base64(signature: Signature) -> str:  # /PS-IGNORE
    """Fetch the signature file object from s3 and return as a base64 string

    :param signature: Signature object:
    :return: base64 file string
    """

    signature_file_bytes = get_signature_file_bytes(signature)
    encoded_bytes = base64.b64encode(signature_file_bytes)  # /PS-IGNORE
    return encoded_bytes.decode()


def get_active_signature() -> Signature:
    """Fetch the active signature

    :return: Signature object
    """
    return Signature.objects.get(is_active=True)


def get_active_signature_file() -> tuple[Signature, str]:
    """Fetch the active signature and base64 file string

    :return: Signature object, base64 file string
    """
    signature = get_active_signature()
    return signature, get_signature_file_base64(signature)  # /PS-IGNORE
