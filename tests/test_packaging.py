"""Packaging contract for the installable disclaimer template.

Synthetic fields only. The canonical disclaimer bytes are not rewritten here.
"""

import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from disclaimer_template import PLACEHOLDERS
from disclaimer_template.__main__ import main

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


class PackagingContractTests(unittest.TestCase):
    def test_console_script_and_package_data_are_declared(self):
        scripts = PYPROJECT["project"]["scripts"]
        self.assertEqual(
            scripts["disclaimer-template"],
            "disclaimer_template.__main__:main",
        )
        package_data = PYPROJECT["tool"]["setuptools"]["package-data"]
        self.assertIn("template.md", package_data["disclaimer_template"])
        self.assertEqual(
            PYPROJECT["tool"]["setuptools"]["packages"],
            ["disclaimer_template"],
        )
        template = ROOT / "disclaimer_template" / "template.md"
        self.assertTrue(template.is_file())

    def test_pyyaml_pin_matches_hashed_requirements(self):
        self.assertEqual(PYPROJECT["project"]["dependencies"], ["PyYAML==6.0.3"])
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("PyYAML==6.0.3", requirements)
        self.assertIn("--hash=sha256:", requirements)

    def test_main_entry_point_fills_example_yaml(self):
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([str(ROOT / "template" / "fields.example.yaml")])
        self.assertEqual(code, 0, stderr.getvalue())
        text = stdout.getvalue()
        for token in PLACEHOLDERS.values():
            self.assertNotIn(token, text)
        self.assertIn("Example Jurisdiction", text)
        self.assertIn("EXAMPLE-HOLDING", text)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
