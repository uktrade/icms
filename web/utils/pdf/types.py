from enum import Enum, auto


# This will be fleshed out more when required.
class DocumentTypes(Enum):
    LICENCE_PREVIEW = auto()
    LICENCE_PRE_SIGN = auto()
    LICENCE_SIGNED = auto()
    CERTIFICATE = auto()
    COVER_LETTER = auto()
