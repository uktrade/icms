from markupsafe import Markup


def get_html_or_text(value: str | Markup) -> dict[str, str | Markup]:
    if isinstance(value, Markup):
        return {"html": value}

    return {"text": value}
