from web.domains.exporter.forms import ExporterFilter


def test_name_filter(db):
    results = ExporterFilter(data={"exporter_name": "exporter 1"}).qs
    assert results.count() == 1


def test_filter_order(db):
    results = ExporterFilter(data={"exporter_name": "exporter"}).qs
    assert results.count() == 3
    assert results.first().name == "Test Exporter 1"
    assert results.last().name == "Test Exporter 3 Inactive"
