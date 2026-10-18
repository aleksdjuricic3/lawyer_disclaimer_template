"""Tests for filling the disclaimer template. Synthetic fields only."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from disclaimer_template import PLACEHOLDERS, MissingFieldsError, fill, template_text

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

SAMPLE = {
    "jurisdictions": "Example Jurisdiction",
    "lexpunk_disclosure": "Example community disclosure",
    "other": "Example other community",
    "holdings": "EXAMPLE-HOLDING",
}

SECTIONS = (
    "**DISCLAIMER OF ATTORNEY – CLIENT RELATIONSHIP**",
    "**USE AT YOUR OWN RISK**",
    "**VIEWS EXPRESSED DISCLAIMER**",
)


class FillTests(unittest.TestCase):
    def test_template_text_is_preserved_in_readme(self):
        self.assertIn(template_text(), README)

    def test_each_placeholder_appears_once(self):
        text = template_text()
        for token in PLACEHOLDERS.values():
            self.assertEqual(text.count(token), 1, token)

    def test_fill_substitutes_placeholders_and_keeps_sections(self):
        filled = fill(SAMPLE)
        for token in PLACEHOLDERS.values():
            self.assertNotIn(token, filled)
        for value in SAMPLE.values():
            self.assertIn(value, filled)
        for section in SECTIONS:
            self.assertIn(section, filled)
        self.assertIn(
            "Unless we have entered into a written engagement letter providing for paid legal services",
            filled,
        )

    def test_fill_does_not_rewrite_surrounding_prose(self):
        filled = fill(SAMPLE)
        restored = filled
        for name, token in PLACEHOLDERS.items():
            restored = restored.replace(SAMPLE[name], token, 1)
        self.assertEqual(restored, template_text())

    def test_inserted_value_is_not_scanned_for_other_placeholders(self):
        fields = dict(SAMPLE)
        fields["jurisdictions"] = "see [LIST] later"
        filled = fill(fields)
        self.assertIn("see [LIST] later", filled)
        self.assertIn("EXAMPLE-HOLDING", filled)
        self.assertNotIn("[List Jxd]", filled)

    def test_missing_field_names_the_placeholder(self):
        fields = dict(SAMPLE)
        del fields["holdings"]
        with self.assertRaises(MissingFieldsError) as caught:
            fill(fields)
        self.assertEqual(caught.exception.missing, ["holdings"])
        self.assertIn("[LIST]", str(caught.exception))

    def test_none_counts_as_missing(self):
        fields = dict(SAMPLE)
        fields["jurisdictions"] = None
        with self.assertRaises(MissingFieldsError) as caught:
            fill(fields)
        self.assertEqual(caught.exception.missing, ["jurisdictions"])

    def test_non_string_value_is_rejected(self):
        fields = dict(SAMPLE)
        fields["holdings"] = ["EXAMPLE-HOLDING"]
        with self.assertRaises(TypeError):
            fill(fields)

    def test_example_yaml_fills_disclaimer_sections(self):
        data = yaml.safe_load(
            (ROOT / "template" / "fields.example.yaml").read_text(encoding="utf-8")
        )
        filled = fill(data)
        for section in SECTIONS:
            self.assertIn(section, filled)
        for token in PLACEHOLDERS.values():
            self.assertNotIn(token, filled)
        for value in data.values():
            self.assertIn(value, filled)


class CliTests(unittest.TestCase):
    def test_cli_writes_stdout_and_out_file(self):
        fields = ROOT / "template" / "fields.example.yaml"
        completed = subprocess.run(
            [sys.executable, "-m", "disclaimer_template", str(fields)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("**USE AT YOUR OWN RISK**", completed.stdout)
        self.assertNotIn("[List Jxd]", completed.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "filled.md"
            written = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "disclaimer_template",
                    str(fields),
                    "--out",
                    str(out),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertEqual(written.stdout, "")
            self.assertEqual(out.read_text(encoding="utf-8"), completed.stdout)

    def test_cli_fails_on_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            fields = Path(tmp) / "fields.yaml"
            fields.write_text(
                "jurisdictions: 'Example Jurisdiction'\n"
                "lexpunk_disclosure: 'Example community disclosure'\n"
                "other: 'Example other community'\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-m", "disclaimer_template", str(fields)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("holdings", completed.stderr)
        self.assertIn("[LIST]", completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
