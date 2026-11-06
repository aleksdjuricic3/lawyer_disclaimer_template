"""Read a YAML fields file and write the filled disclaimer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from disclaimer_template import MissingFieldsError, fill


class FieldsFileError(Exception):
    """The fields file could not be read as a YAML mapping."""


def load_fields(path: Path) -> dict[str, object]:
    try:
        import yaml
    except ImportError as exc:
        raise FieldsFileError(
            "PyYAML is required (python -m pip install -r requirements.txt)"
        ) from exc
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FieldsFileError(str(exc)) from exc
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FieldsFileError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FieldsFileError(f"{path} must contain a YAML mapping of fields")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fill the disclaimer template from a YAML fields file."
    )
    parser.add_argument(
        "fields",
        type=Path,
        help="YAML file of placeholder fields (see template/fields.example.yaml)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write filled markdown to this path instead of stdout",
    )
    args = parser.parse_args(argv)
    try:
        text = fill(load_fields(args.fields))
    except (MissingFieldsError, TypeError, FieldsFileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.out is not None:
        try:
            args.out.write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
