from typing import Any

from pydantic import BaseModel

from .common import TextOrHTMLMixin


class RowItem(TextOrHTMLMixin, BaseModel):
    # Required. If html is set, this is not required.
    # Text for cells in table rows.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # Required. If text is set, this is not required.
    # HTML for cells in table rows.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # Specify format of a cell. Currently we only use “numeric”.
    format: str | None = None
    # Classes to add to the table row cell.
    classes: str | None = None
    # Specify how many columns a cell extends.
    colspan: int | None = None
    # Specify how many rows a cell extends.
    rowspan: int | None = None
    # attributes 	object 	HTML attributes (for example data attributes) to add to the table cell.
    attributes: dict[str, Any] | None = None


class HeadItem(TextOrHTMLMixin, BaseModel):
    # If html is set, this is not required.
    # Text for table head cells.
    # If html is provided, the text option will be ignored.
    text: str | None = None
    # html 	string 	If text is set, this is not required.
    # HTML for table head cells.
    # If html is provided, the text option will be ignored.
    html: str | None = None
    # format 	string 	Specify format of a cell. Currently we only use “numeric”.
    format: str | None = None
    # classes 	string 	Classes to add to the table head cell.
    classes: str | None = None
    # colspan 	integer 	Specify how many columns a cell extends.
    colspan: int | None = None
    # rowspan 	integer 	Specify how many rows a cell extends.
    rowspan: int | None = None
    # attributes 	object 	HTML attributes (for example data attributes) to add to the table cell.
    attributes: dict[str, Any] | None = None


# All options available here:
# https://design-system.service.gov.uk/components/table/
class TableKwargs(BaseModel):
    # Required. The rows within the table component.
    rows: list[list[RowItem]]
    # Can be used to add a row of table header cells (<th>) at the top of the table component.
    head: list[list[HeadItem]]
    # Caption text.
    caption: str | None = None
    # Classes for caption text size. Classes should correspond to the available typography heading classes.
    captionClasses: str | None = None
    # If set to true, the first cell in each row will be a table header (<th>).
    firstCellIsHeader: bool | None = None
    # Classes to add to the table container.
    classes: str | None = None
    # HTML attributes (for example data attributes) to add to the table container.
    attributes: dict[str, Any] | None = None
