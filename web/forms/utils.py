import re


def clean_postcode(postcode: str) -> str:
    return re.sub(r"\s+", "", postcode).upper()
