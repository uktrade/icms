import unicodedata


def normalize_address(input: str) -> str:
    # Normalize string to remove unwanted characters
    input = unicodedata.normalize("NFKD", input).encode("ascii", "ignore").decode("utf8")

    # manually replace grave accent (U+0060) with apostrophe (U+0027) as CHIEF does not support it
    input = input.replace("\u0060", "\u0027")

    return input
