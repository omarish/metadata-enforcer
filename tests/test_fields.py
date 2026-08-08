from datetime import date, datetime
from uuid import UUID

import pytest

from metadata_enforcer.models import (
    BooleanField,
    DateField,
    TagsField,
    TextField,
    URLField,
    URLPathField,
    UUIDField,
)


def test_text_field_accepts_string():
    assert TextField().clean("hello") == "hello"


def test_text_field_rejects_non_string():
    with pytest.raises(ValueError, match="must be text"):
        TextField().clean(1)


def test_optional_allows_null_and_blank():
    field = TextField(optional=True)
    assert field.clean(None) is None
    assert field.clean("") is None


def test_required_rejects_null_and_blank():
    field = TextField()
    with pytest.raises(ValueError, match="may not be null"):
        field.clean(None)
    with pytest.raises(ValueError, match="may not be blank"):
        field.clean("")


def test_choices():
    field = TextField(choices=["a", "b"])
    assert field.clean("a") == "a"
    with pytest.raises(ValueError, match="must be one of"):
        field.clean("c")


def test_boolean_field():
    assert BooleanField().clean(True) is True
    with pytest.raises(ValueError, match="must be a boolean"):
        BooleanField().clean("yes")


def test_date_field_accepts_iso_and_date():
    field = DateField()
    assert field.clean("2026-07-27") == date(2026, 7, 27)
    assert field.clean(date(2026, 7, 27)) == date(2026, 7, 27)
    with pytest.raises(ValueError, match="not a datetime"):
        field.clean(datetime(2026, 7, 27, 12, 0))
    with pytest.raises(ValueError, match="ISO 8601"):
        field.clean("07/27/2026")


def test_date_field_serialize():
    assert DateField().serialize(date(2026, 7, 27)) == "2026-07-27"


def test_tags_field():
    field = TagsField()
    assert field.clean(["a", "b"]) == ["a", "b"]
    with pytest.raises(ValueError, match="list of tags"):
        field.clean("a")
    with pytest.raises(ValueError, match="only text tags"):
        field.clean([1])


def test_uuid_field():
    field = UUIDField()
    value = field.clean("550e8400-e29b-41d4-a716-446655440000")
    assert isinstance(value, UUID)
    assert field.serialize(value) == "550e8400-e29b-41d4-a716-446655440000"
    with pytest.raises(ValueError, match="valid UUID"):
        field.clean("not-a-uuid")


def test_url_field():
    field = URLField()
    assert field.clean("https://example.com/path") == "https://example.com/path"
    with pytest.raises(ValueError, match="valid URL"):
        field.clean("ftp://example.com")
    with pytest.raises(ValueError, match="valid URL"):
        field.clean("https://exa mple.com")


def test_url_path_field():
    field = URLPathField()
    assert field.clean("/essays/hello") == "/essays/hello"
    with pytest.raises(ValueError, match="absolute"):
        field.clean("essays/hello")
    with pytest.raises(ValueError, match="only a URL path"):
        field.clean("https://example.com/x")
