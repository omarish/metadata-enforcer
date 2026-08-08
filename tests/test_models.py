import pytest

from metadata_enforcer.models import (
    ExtraFields,
    Model,
    TextField,
    ValidationError,
)


class AbstractPage(Model):
    title = TextField()

    class Meta:
        abstract = True


class Page(AbstractPage):
    subtitle = TextField(default="untitled")

    class Meta:
        extra = ExtraFields.FORBID
        field_order = ("title", "subtitle")


class LoosePage(AbstractPage):
    class Meta:
        extra = ExtraFields.ALLOW


class IgnoringPage(AbstractPage):
    class Meta:
        extra = ExtraFields.IGNORE


def test_abstract_cannot_instantiate():
    with pytest.raises(TypeError, match="abstract"):
        AbstractPage(title="x")


def test_validate_required_and_defaults():
    cleaned = Page.validate({"title": "Hello"})
    assert cleaned["title"] == "Hello"
    assert cleaned["subtitle"] == "untitled"


def test_validate_missing_required():
    with pytest.raises(ValidationError) as exc:
        Page.validate({})
    assert "title" in exc.value.errors
    assert exc.value.errors["title"] == "is required"


def test_forbid_extra_fields():
    with pytest.raises(ValidationError) as exc:
        Page.validate({"title": "Hello", "unknown": 1})
    assert exc.value.errors["unknown"] == "is not a recognized field"


def test_allow_extra_fields():
    cleaned = LoosePage.validate({"title": "Hello", "unknown": 1})
    assert cleaned["unknown"] == 1


def test_ignore_extra_fields():
    cleaned = IgnoringPage.validate({"title": "Hello", "unknown": 1})
    assert cleaned == {"title": "Hello"}
    assert "unknown" not in cleaned


def test_apply_defaults_and_order():
    result = Page.apply_defaults({"title": "Hello", "extra": True})
    assert result["subtitle"] == "untitled"
    ordered = Page.order_metadata({"extra": True, "subtitle": "s", "title": "Hello"})
    assert list(ordered) == ["title", "subtitle", "extra"]


def test_instance_to_dict():
    page = Page(title="Hello")
    assert page.to_dict()["title"] == "Hello"
    assert page.title == "Hello"


def test_field_inheritance_override():
    class Child(Page):
        title = TextField(optional=True)

    cleaned = Child.validate({})
    assert "title" not in cleaned or cleaned.get("title") is None
