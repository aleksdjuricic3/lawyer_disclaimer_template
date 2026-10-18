"""Fill the canonical disclaimer template.

``template.md`` is the upstream README prose. ``fill`` substitutes bracket
placeholders and leaves every other character alone.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from importlib.resources import files

# Field name -> bracket placeholder in the canonical disclaimer.
PLACEHOLDERS: dict[str, str] = {
    "jurisdictions": "[List Jxd]",
    "lexpunk_disclosure": "[LeXpunk/L3X disclosure]",
    "other": "[Other]",
    "holdings": "[LIST]",
}

_TOKEN_RE = re.compile("|".join(re.escape(token) for token in PLACEHOLDERS.values()))


class MissingFieldsError(Exception):
    """A required placeholder field is absent or null."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = list(missing)
        details = ", ".join(f"{name} ({PLACEHOLDERS[name]})" for name in self.missing)
        super().__init__(f"Missing required placeholders: {details}")


def template_text() -> str:
    """Return the canonical disclaimer markdown."""
    return (files(__package__) / "template.md").read_text(encoding="utf-8")


def fill(fields: Mapping[str, object]) -> str:
    """Substitute bracket placeholders in the canonical disclaimer.

    ``fields`` must include every key in ``PLACEHOLDERS``. Values are strings
    (an empty string is allowed). A missing key or ``None`` raises
    ``MissingFieldsError``. Other values raise ``TypeError``.

    Replacement is a single pass, so a value that itself contains a bracket
    placeholder is left as written.
    """
    if not isinstance(fields, Mapping):
        raise TypeError("fields must be a mapping of placeholder names to strings")

    missing = [
        name for name in PLACEHOLDERS if name not in fields or fields[name] is None
    ]
    if missing:
        raise MissingFieldsError(missing)

    values: dict[str, str] = {}
    for name, token in PLACEHOLDERS.items():
        value = fields[name]
        if not isinstance(value, str):
            raise TypeError(
                f"{name} ({token}) must be a string, got {type(value).__name__}"
            )
        values[token] = value

    return _TOKEN_RE.sub(lambda match: values[match.group(0)], template_text())
