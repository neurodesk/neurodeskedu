"""Build a tiny book with the production config, extensions, and install script."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BookBuildTest(unittest.TestCase):
    def test_isolated_build_renders_saved_outputs_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory) / "books"
            book.mkdir()
            shutil.copy2(ROOT / "books/_config.yml", book)
            for name in ("_ext", "_static"):
                shutil.copytree(ROOT / "books" / name, book / name)
            (book / "images").mkdir()
            shutil.copy2(ROOT / "books/images/neurodesk_logo.svg", book / "images")
            (book / "intro.md").write_text("# Publishing smoke test\n")
            notebook_dir = book / "examples/structural_imaging"
            notebook_dir.mkdir(parents=True)
            (book / "examples/intro.md").write_text("# Examples\n")
            (notebook_dir / "intro.md").write_text("# Structural imaging\n")
            notebook = {
                "nbformat": 4, "nbformat_minor": 5,
                "metadata": {
                    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                    "language_info": {"name": "python"},
                    "nd_review_id": "publishing-smoke-test",
                },
                "cells": [
                    {"id": "title", "cell_type": "markdown", "metadata": {}, "source": "# Saved notebook"},
                    {"id": "result", "cell_type": "code", "metadata": {}, "execution_count": 1,
                     "source": "raise RuntimeError('Publication must not execute notebooks')",
                     "outputs": [{"output_type": "stream", "name": "stdout", "text": "SAVED_RESULT_MARKER"}]},
                ],
            }
            (notebook_dir / "saved.ipynb").write_text(json.dumps(notebook))
            environment = os.environ.copy()
            # The builder must not depend on the user's package index or user site.
            environment.update(PIP_NO_INDEX="1", PIP_INDEX_URL="https://invalid.example/simple", PYTHONNOUSERSITE="1")
            result = subprocess.run(
                ["bash", str(ROOT / ".github/scripts/build_book.sh"), str(book)],
                env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=600,
            )
            self.assertEqual(result.returncode, 0, result.stdout[-20000:])
            html = (book / "_build/html/examples/structural_imaging/saved.html").read_text()
            self.assertIn("SAVED_RESULT_MARKER", html)
            self.assertIn('name="nd-review-id" content="publishing-smoke-test"', html)
            self.assertTrue((book / "_build/html/intro.html").is_file())


if __name__ == "__main__":
    unittest.main()
