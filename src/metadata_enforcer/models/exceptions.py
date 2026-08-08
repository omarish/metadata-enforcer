from collections.abc import Mapping


class ValidationError(ValueError):
    """Raised when metadata does not conform to a model."""

    def __init__(self, errors: Mapping[str, str]) -> None:
        self.errors = dict(errors)
        message = "; ".join(f"{name}: {error}" for name, error in self.errors.items())
        super().__init__(message)
