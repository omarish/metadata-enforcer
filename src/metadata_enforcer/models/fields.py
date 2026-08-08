from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit
from uuid import UUID

if TYPE_CHECKING:
    from .base import Model


class _Missing:
    pass


MISSING = _Missing()


class AbstractBaseField:
    """A declarative metadata field."""

    def __init__(
        self,
        *,
        default: Any = MISSING,
        optional: bool = False,
        choices: tuple[Any, ...] | list[Any] | None = None,
        unique: bool = False,
        description: str | None = None,
    ) -> None:
        self.default = default
        self.optional = optional
        self.choices = tuple(choices) if choices is not None else None
        self.unique = unique  # reserved; not enforced in 2.0
        self.description = description
        self.name: str | None = None

    def __set_name__(self, owner: type[Model], name: str) -> None:
        self.name = name

    def __get__(self, instance: Model | None, owner: type[Model]) -> Any:
        if instance is None:
            return self
        return instance._values.get(self.name)

    def __set__(self, instance: Model, value: Any) -> None:
        instance._values[self._field_name] = self.clean(value)

    @property
    def _field_name(self) -> str:
        if self.name is None:
            raise RuntimeError("Field has not been attached to a model")
        return self.name

    @property
    def has_default(self) -> bool:
        return self.default is not MISSING

    def get_default(self) -> Any:
        if not self.has_default:
            raise RuntimeError(f"{self._field_name} has no default")
        if isinstance(self.default, Callable):
            return self.default()
        return deepcopy(self.default)

    def clean(self, value: Any) -> Any:
        if value is None or value == "":
            if self.optional:
                return None
            if value == "":
                raise ValueError("may not be blank")
            raise ValueError("may not be null")

        value = self.to_python(value)
        if self.choices is not None and value not in self.choices:
            choices = ", ".join(repr(choice) for choice in self.choices)
            raise ValueError(f"must be one of: {choices}")
        return value

    def to_python(self, value: Any) -> Any:
        return value

    def serialize(self, value: Any) -> Any:
        return value


class BooleanField(AbstractBaseField):
    def to_python(self, value: Any) -> bool:
        if not isinstance(value, bool):
            raise ValueError("must be a boolean")
        return value


class DateField(AbstractBaseField):
    def to_python(self, value: Any) -> date:
        if isinstance(value, datetime):
            raise ValueError("must be a date, not a datetime")
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        raise ValueError("must be an ISO 8601 date")

    def serialize(self, value: Any) -> str:
        return self.to_python(value).isoformat()


class TextField(AbstractBaseField):
    def to_python(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be text")
        return value


class TagsField(AbstractBaseField):
    def to_python(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("must be a list of tags")
        if any(not isinstance(tag, str) for tag in value):
            raise ValueError("must contain only text tags")
        return value.copy()


class UUIDField(AbstractBaseField):
    def to_python(self, value: Any) -> UUID:
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                pass
        raise ValueError("must be a valid UUID")

    def serialize(self, value: Any) -> str:
        return str(self.to_python(value))


class URLField(AbstractBaseField):
    def __init__(
        self,
        *,
        schemes: tuple[str, ...] = ("http", "https"),
        **options: Any,
    ) -> None:
        super().__init__(**options)
        self.schemes = tuple(scheme.lower() for scheme in schemes)

    def to_python(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("must be a URL")
        if any(character.isspace() for character in value):
            raise ValueError("must be a valid URL")

        parsed = urlsplit(value)
        if parsed.scheme.lower() not in self.schemes or parsed.hostname is None:
            schemes = ", ".join(self.schemes)
            raise ValueError(f"must be a valid URL using one of: {schemes}")

        try:
            parsed.port
        except ValueError as error:
            raise ValueError("must be a valid URL") from error
        return value


class URLPathField(AbstractBaseField):
    def __init__(self, *, absolute: bool = True, **options: Any) -> None:
        super().__init__(**options)
        self.absolute = absolute

    def to_python(self, value: Any) -> str:
        if not isinstance(value, str) or any(
            character.isspace() for character in value
        ):
            raise ValueError("must be a URL path")

        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("must contain only a URL path")
        if self.absolute and (not value.startswith("/") or value.startswith("//")):
            raise ValueError("must be an absolute URL path")
        if "\\" in value:
            raise ValueError("must use forward slashes")
        return value
