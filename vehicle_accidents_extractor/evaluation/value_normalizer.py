"""Normalize values for extraction scoring and vehicle matching."""

from typing import Any


def normalize_value(value: Any) -> Any:
    """Trim and casefold strings; compare other JSON values exactly."""
    return value.strip().casefold() if isinstance(value, str) else value
