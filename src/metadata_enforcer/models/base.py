from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .exceptions import ValidationError
from .fields import AbstractBaseField
from .options import ExtraFields


class ModelMeta(type):
    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> ModelMeta:
        fields: dict[str, AbstractBaseField] = {}
        for base in bases:
            fields.update(getattr(base, "_fields", {}))
        fields.update(
            {
                field_name: value
                for field_name, value in namespace.items()
                if isinstance(value, AbstractBaseField)
            }
        )

        cls = super().__new__(mcls, name, bases, namespace)
        cls._fields = fields

        meta = namespace.get("Meta")
        inherited_extra = next(
            (
                base._extra
                for base in bases
                if isinstance(base, ModelMeta) and hasattr(base, "_extra")
            ),
            ExtraFields.ALLOW,
        )
        extra = getattr(meta, "extra", inherited_extra)
        try:
            cls._extra = ExtraFields(extra)
        except ValueError as error:
            choices = ", ".join(option.value for option in ExtraFields)
            raise TypeError(f"Meta.extra must be one of: {choices}") from error

        inherited_field_order = next(
            (
                base._field_order
                for base in bases
                if isinstance(base, ModelMeta) and hasattr(base, "_field_order")
            ),
            (),
        )
        field_order = getattr(meta, "field_order", inherited_field_order)
        if isinstance(field_order, str):
            raise TypeError("Meta.field_order must be a sequence of field names")
        cls._field_order = tuple(field_order)
        if any(not isinstance(name, str) for name in cls._field_order):
            raise TypeError("Meta.field_order must contain only field names")
        if len(cls._field_order) != len(set(cls._field_order)):
            raise TypeError("Meta.field_order may not contain duplicate field names")

        cls._abstract = bool(getattr(meta, "abstract", False))
        cls._constraints = tuple(getattr(meta, "constraints", ()))
        return cls


class Model(metaclass=ModelMeta):
    _fields: dict[str, AbstractBaseField]
    _abstract: bool
    _extra: ExtraFields
    _field_order: tuple[str, ...]
    _constraints: tuple[Any, ...]

    class Meta:
        abstract = True
        extra = ExtraFields.ALLOW
        field_order: tuple[str, ...] = ()

    def __init__(self, **values: Any) -> None:
        if self._abstract:
            raise TypeError(f"{type(self).__name__} is abstract")
        self._values = self.validate(values)

    @classmethod
    def validate(cls, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Validate metadata and return a cleaned copy."""
        cleaned: dict[str, Any] = {}
        errors: dict[str, str] = {}

        for name, field in cls._fields.items():
            if name not in metadata:
                if field.has_default:
                    try:
                        cleaned[name] = field.clean(field.get_default())
                    except ValueError as error:
                        errors[name] = f"invalid default: {error}"
                elif not field.optional:
                    errors[name] = "is required"
                continue

            try:
                cleaned[name] = field.clean(metadata[name])
            except ValueError as error:
                errors[name] = str(error)

        extras = set(metadata) - set(cls._fields)
        if cls._extra is ExtraFields.ALLOW:
            cleaned.update({name: metadata[name] for name in extras})
        elif cls._extra is ExtraFields.FORBID:
            errors.update({name: "is not a recognized field" for name in extras})
        # ExtraFields.IGNORE: drop extras from the cleaned result intentionally.

        if errors:
            raise ValidationError(errors)
        return cleaned

    @classmethod
    def apply_defaults(cls, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Return metadata with missing field defaults added, without validation."""
        result = dict(metadata)
        for name, field in cls._fields.items():
            if name not in result and field.has_default:
                try:
                    default = field.clean(field.get_default())
                    result[name] = field.serialize(default)
                except ValueError as error:
                    raise ValidationError(
                        {name: f"invalid default: {error}"}
                    ) from error
        return result

    @classmethod
    def order_metadata(cls, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Order configured fields first, preserving all remaining field order."""
        ordered = {
            name: metadata[name]
            for name in cls._field_order
            if name in metadata
        }
        ordered.update(
            (name, value) for name, value in metadata.items() if name not in ordered
        )
        return ordered

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._values)
