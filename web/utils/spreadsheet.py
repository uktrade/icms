import io
from dataclasses import dataclass, field

import xlsxwriter


@dataclass
class XlsxHeaderData:
    data: list[str] = field(default_factory=list)
    styles: dict[str, bool | str | int] = field(default_factory=dict)


@dataclass
class XlsxConfig:
    header: XlsxHeaderData = field(repr=False, default_factory=XlsxHeaderData)
    column_width: int | None = field(repr=False, default=None)
    sheet_name: str = field(default_factory=str)
    rows: list[list[str]] | None = field(repr=False, default=None)


def generate_xlsx_file(config: XlsxConfig) -> bytes:
    """Generates an xlsx file from the provided config"""

    output = io.BytesIO()
    with xlsxwriter.Workbook(output) as workbook:
        worksheet = workbook.add_worksheet(config.sheet_name)
        header_style = workbook.add_format(config.header.styles)
        for column, value in enumerate(config.header.data):
            worksheet.write(0, column, value, header_style)

        columns = len(config.header.data)
        if config.column_width and columns:
            worksheet.set_column(0, columns - 1, config.column_width)

        rows = config.rows or []

        for row, row_data in enumerate(rows, start=1):
            for column, data in enumerate(row_data):
                worksheet.write(row, column, data)

    xlsx_data = output.getvalue()
    return xlsx_data
