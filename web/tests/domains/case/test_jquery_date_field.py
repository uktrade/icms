import datetime as dt

from django.forms import forms

from web.forms.fields import (
    FutureOnlyJqueryDateField,
    JqueryDateField,
    PastOnlyJqueryDateField,
)


def test_year_select_render():
    field = JqueryDateField(year_select_range=10)
    assert "data-year-select-range" in field.widget_attrs(field.widget)
    assert field.widget_attrs(field.widget)["data-year-select-range"] == 10

    # test the rendering of the widget
    html = field.widget.render("name", None)
    assert 'data-year-select-range="10"' in html


def test_year_select_incorrect_validation():
    field = JqueryDateField(year_select_range=5)
    entered_value = dt.date(2000, 1, 1)
    try:
        field.validate(entered_value)
    except forms.ValidationError as e:
        assert "Date cannot be more than 5 years in the past/future." in str(e)


def test_year_select_correct_validation():
    field = JqueryDateField(year_select_range=10)
    entered_value = dt.date(2021, 1, 1)
    assert field.clean(entered_value) == entered_value


def test_past_only_date_field_render():
    field = PastOnlyJqueryDateField()
    assert "data-past-only" in field.widget_attrs(field.widget)
    assert field.widget_attrs(field.widget)["data-past-only"] == "yes"

    # test the rendering of the widget
    html = field.widget.render("name", None)
    assert 'data-past-only="yes"' in html


def test_past_only_date_field():
    field = PastOnlyJqueryDateField(year_select_range=10)
    try:
        field.validate(dt.datetime.now() + dt.timedelta(days=400))
    except forms.ValidationError as e:
        assert "Date cannot be in the future." in str(e)


def test_future_only_date_field_render():
    field = FutureOnlyJqueryDateField()
    assert "data-future-only" in field.widget_attrs(field.widget)
    assert field.widget_attrs(field.widget)["data-future-only"] == "yes"

    # test the rendering of the widget
    html = field.widget.render("name", None)
    assert 'data-future-only="yes"' in html


def test_future_only_date_field():
    field = FutureOnlyJqueryDateField(year_select_range=10)
    try:
        field.validate(dt.datetime.now() - dt.timedelta(days=400))
    except forms.ValidationError as e:
        assert "Date cannot be in the past." in str(e)
