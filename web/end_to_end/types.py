from typing import TypedDict


# Taken from the playwright api_structures file
class FilePayload(TypedDict):
    name: str
    mimeType: str
    buffer: bytes
