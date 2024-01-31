import io
from dataclasses import dataclass, field
from typing import Any

import xlsxwriter

from web.types import TypedTextChoices


@dataclass
class XlsxHeaderData:
    data: list[str] = field(default_factory=list)
    styles: dict[str, bool | str | int] = field(default_factory=dict)


@dataclass
class XlsxSheetConfig:
    header: XlsxHeaderData = field(repr=False, default_factory=XlsxHeaderData)
    column_width: int | None = field(repr=False, default=None)
    sheet_name: str = field(default_factory=str)
    rows: list[list[str]] | None = field(repr=False, default=None)


def generate_xlsx_file(
    sheets: list[XlsxSheetConfig], options: dict[str, Any] | None = None
) -> bytes:
    """Generates an xlsx file from the provided config"""

    output = io.BytesIO()
    with xlsxwriter.Workbook(output, options) as workbook:
        for sheet in sheets:
            add_worksheet(workbook, sheet)

    xlsx_data = output.getvalue()
    return xlsx_data


def add_worksheet(workbook: xlsxwriter.Workbook, config: XlsxSheetConfig) -> None:
    worksheet = workbook.add_worksheet(config.sheet_name)
    header_style = workbook.add_format(config.header.styles)
    cell_format = workbook.add_format()
    cell_format.set_align("top")
    cell_format.set_align("left")
    for column, value in enumerate(config.header.data):
        worksheet.write(0, column, value, header_style)

    columns = len(config.header.data)
    if config.column_width and columns:
        worksheet.set_column(0, columns - 1, config.column_width)

    rows = config.rows or []

    for row, row_data in enumerate(rows, start=1):
        for column, data in enumerate(row_data):
            worksheet.write(row, column, data, cell_format)


class MIMETYPE(TypedTextChoices):
    CSV = ("application/csv", "CSV")
    XLSX = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "XLSX")
