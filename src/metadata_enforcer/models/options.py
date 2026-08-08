from enum import Enum


class ExtraFields(str, Enum):
    """How a model handles metadata fields it does not declare."""

    ALLOW = "allow"
    IGNORE = "ignore"
    FORBID = "forbid"
