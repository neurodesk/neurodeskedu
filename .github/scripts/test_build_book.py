import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

import yaml

import build_book
from build_book import adapt_markdown, controls, discover, embed_widgets, finish, prepare
from verify_book import PageLinks


class BookBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.book = self.root / "books"
        self.book.mkdir()
        self.settings = yaml.safe_load(Path("books/publishing.yml").read_text())
        self.settings["redirects"] = {"old/page": "examples/topic/Test_one.ipynb"}
        (self.book / "myst.yml").write_text(Path("books/myst.yml").read_text())
        for name in ["intro.md", "examples/intro.md", "examples/topic/intro.md"]:
            path = self.book / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Introduction\n")
        self.source = Path("examples/topic/Test_one.ipynb")
        self.notebook = {
            "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"nd_review_id": "test-review", "widgets": {"saved": "state"}},
            "cells": [
                {"cell_type": "markdown", "id": "header", "metadata": {},
                 "source": "# Example\n\n**Author:** Example Author\n"},
                {"cell_type": "code", "id": "compute", "metadata": {"tags": ["hide-input"]},
                 "execution_count": 4, "source": "raise RuntimeError('must not execute')",
                 "outputs": [{"output_type": "stream", "name": "stdout", "text": ["saved output\n"]}]},
            ],
        }
        (self.book / self.source).write_text(json.dumps(self.notebook))

    def test_discovers_new_pages_at_every_depth_and_orders_sections(self):
        for name in ["tutorials", "contribute"]:
            (self.book / name).mkdir()
            (self.book / name / "intro.md").write_text(f"# {name}\n")
        for name in ["review", "tutorials", "examples"]:
            (self.book / "contribute" / f"{name}.md").write_text(f"# {name}\n")
        pages, toc = discover(self.book)
        self.assertEqual([item["file"] for item in toc],
                         ["intro.md", "examples/intro.md", "tutorials/intro.md", "contribute/intro.md"])
        self.assertEqual([item["file"] for item in toc[-1]["children"]],
                         ["contribute/examples.md", "contribute/tutorials.md", "contribute/review.md"])
        self.assertEqual(toc[1]["children"][0]["children"], [{"file": self.source.as_posix()}])
        self.assertIn(self.source, pages)

    def test_duplicate_stems_fail_before_build(self):
        (self.book / self.source.with_suffix(".md")).write_text("# Duplicate\n")
        with self.assertRaisesRegex(ValueError, "share a source stem"):
            discover(self.book)

    def test_legacy_heading_links_and_social_handles_remain_readable(self):
        text = "[Step](#1.-Project-setup) [Other](#custom-ID)\n> Github: @example\n"
        self.assertEqual(adapt_markdown(text, {"id-1-project-setup"}),
                         "[Step](#id-1-project-setup) [Other](#custom-ID)\n> Github: \\@example\n")

    def test_preparation_preserves_code_outputs_widgets_and_original_sources(self):
        before = (self.book / self.source).read_bytes()
        stage = self.root / "stage"
        pages, toc = discover(self.book)
        prepare(self.book, stage, pages, toc, self.settings,
                {"books/" + self.source.as_posix(): {"doi_url": "https://doi.org/10.5281/zenodo.12345"}})
        after = json.loads((stage / self.source).read_text())
        self.assertEqual(after["cells"][1:], self.notebook["cells"][1:])
        self.assertEqual(after["metadata"], self.notebook["metadata"])
        self.assertEqual((self.book / self.source).read_bytes(), before)
        text = "".join(after["cells"][0]["source"])
        self.assertIn("doi: 10.5281/zenodo.12345", text)
        self.assertIn("execute:\n  skip: true", text)
        self.assertIn("/edu/_sources/examples/topic/Test_one.ipynb", text)
        self.assertIn("{admonition} Unreviewed", text)
        self.assertEqual(text.count("/hub/user-redirect/git-pull?"), 5)

    def test_frontmatter_cell_without_trailing_newline_keeps_its_metadata(self):
        self.notebook["cells"][0]["source"] = "---\ntitle: Front Title\nsubtitle: Sub\n---"
        (self.book / self.source).write_text(json.dumps(self.notebook))
        pages, toc = discover(self.book)
        prepare(self.book, self.root / "stage", pages, toc, self.settings, {})
        text = "".join(json.loads((self.root / "stage" / self.source).read_text())["cells"][0]["source"])
        meta = yaml.safe_load(text.split("---\n")[1])
        self.assertEqual((meta["title"], meta["subtitle"]), ("Front Title", "Sub"))
        self.assertEqual(text.count("---\n"), 2)

    def test_controls_follow_a_title_only_first_cell(self):
        self.notebook["cells"][0]["source"] = "# Example"
        (self.book / self.source).write_text(json.dumps(self.notebook))
        pages, toc = discover(self.book)
        prepare(self.book, self.root / "stage", pages, toc, self.settings, {})
        text = "".join(json.loads((self.root / "stage" / self.source).read_text())["cells"][0]["source"])
        self.assertLess(text.index("# Example"), text.index("{dropdown} Run this notebook"))

    def test_launch_urls_identify_original_notebook_and_branch(self):
        text = controls(self.source, None, {}, self.settings)
        for line in text.splitlines():
            if not line.startswith("- "):
                continue
            url = line.split("(<", 1)[1].split(">)", 1)[0]
            query = parse_qs(urlparse(url).query)
            self.assertEqual(query["repo"], [self.settings["repository"]])
            self.assertEqual(query["branch"], ["main"])
            self.assertEqual(query["urlpath"], ["lab/tree/neurodeskedu/books/" + self.source.as_posix()])
        self.assertNotIn("nd-launch", controls(Path("tutorial.md"), None, {}, self.settings))

    def test_review_states_and_reviewer_visibility(self):
        labels = {"queued": "Unreviewed", "reviewed": "Reviewed", "stale": "Review out-of-date",
                  "in-progress": "Under review"}
        for state, label in labels.items():
            with self.subTest(state=state):
                text = controls(Path("page.md"), "id", {"id": {"state": state, "reviewers": ["reviewer"]}}, self.settings)
                self.assertIn("{admonition} " + label, text)
                self.assertEqual("@reviewer" in text, state in {"reviewed", "stale"})
        self.assertEqual(controls(Path("page.md"), None, {}, self.settings), "")

    def test_saved_widgets_embed_their_model_dependencies_without_unrelated_models(self):
        mime = "application/vnd.jupyter.widget-view+json"
        self.notebook["cells"][1]["outputs"] = [{"output_type": "display_data", "metadata": {},
                                               "data": {mime: {"model_id": "viewer", "version_major": 2}}}]
        models = {"viewer": {"state": {"volume": "IPY_MODEL_volume", "_esm": "</script>"}},
                  "volume": {"state": {"data": [1, 2, 3]}}, "unrelated": {"state": {}}}
        self.notebook["metadata"]["widgets"] = {"application/vnd.jupyter.widget-state+json": {
            "version_major": 2, "version_minor": 0, "state": models,
        }}
        stage = self.root / "stage"
        embed_widgets(self.notebook, stage, self.source, "/edu")
        assets = list((stage / "_static/widgets").glob("*.html"))
        self.assertEqual(len(assets), 1)
        self.assertEqual(json.loads(self.widget_state(assets[0]))["state"],
                         {k: models[k] for k in ["viewer", "volume"]})
        output = self.notebook["cells"][1]["outputs"][0]["data"]["text/html"]
        self.assertIn("/edu/_static/widgets/" + assets[0].name, output)
        self.assertNotIn("widgets", self.notebook["metadata"])

    def test_widget_views_without_saved_state_keep_the_text_fallback(self):
        self.notebook["metadata"].pop("widgets")
        data = {"application/vnd.jupyter.widget-view+json": {"model_id": "missing"},
                "text/plain": "Widget output"}
        self.notebook["cells"][1]["outputs"] = [{"output_type": "display_data", "data": data}]
        embed_widgets(self.notebook, self.root / "stage", self.source, "/edu")
        self.assertEqual(self.notebook["cells"][1]["outputs"][0]["data"], data)

    def test_widget_views_with_unsaved_models_keep_the_text_fallback(self):
        mime = "application/vnd.jupyter.widget-view+json"
        data = {mime: {"model_id": "closed"}, "text/plain": "Progress"}
        self.notebook["cells"][1]["outputs"] = [{"output_type": "display_data", "data": dict(data)}]
        self.notebook["metadata"]["widgets"] = {"application/vnd.jupyter.widget-state+json": {
            "version_major": 2, "version_minor": 0, "state": {},
        }}
        embed_widgets(self.notebook, self.root / "stage", self.source, "/edu")
        self.assertEqual(self.notebook["cells"][1]["outputs"][0]["data"], {"text/plain": "Progress"})

    def widget_state(self, page: Path) -> str:
        parts = json.loads(page.read_text().split("Promise.all(")[1].split(".map(")[0])
        return "".join((page.parent / part).read_text() for part in parts)

    def test_large_widget_state_is_split_into_publishable_parts(self):
        mime = "application/vnd.jupyter.widget-view+json"
        self.notebook["cells"][1]["outputs"] = [{"output_type": "display_data", "metadata": {},
                                               "data": {mime: {"model_id": "viewer"}}}]
        models = {"viewer": {"state": {"volume": "é" * 200}}}
        self.notebook["metadata"]["widgets"] = {"application/vnd.jupyter.widget-state+json": {
            "version_major": 2, "version_minor": 0, "state": models,
        }}
        stage = self.root / "stage"
        with mock.patch.object(build_book, "WIDGET_PART_SIZE", 64):
            embed_widgets(self.notebook, stage, self.source, "/edu")
        folder = stage / "_static/widgets"
        parts = sorted(folder.glob("*.txt"))
        self.assertGreater(len(parts), 10)
        self.assertTrue(all(part.stat().st_size <= 64 for part in parts))
        page = next(folder.glob("*.html"))
        self.assertEqual(json.loads(self.widget_state(page))["state"], models)

    def test_export_requires_every_page_and_preserves_raw_downloads_and_aliases(self):
        stage = self.root / "stage"
        built = stage / "_build/html"
        content = stage / "_build/site/content"
        content.mkdir(parents=True)
        built.mkdir()
        pages = [self.source]
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "Missing exported pages"):
            finish(stage, self.book, output, pages, self.settings)
        route = "examples/topic/test-one"
        (content / "page.json").write_text(json.dumps({"location": "/" + str(self.source),
                                                       "slug": route.replace("/", ".")}))
        (built / route).mkdir(parents=True)
        (built / route / "index.html").write_text("<html><head></head><body>saved output</body></html>")
        finish(stage, self.book, output, pages, self.settings)
        self.assertEqual((output / "_sources" / self.source).read_bytes(), (self.book / self.source).read_bytes())
        self.assertIn('name="citation_author" content="Example Author"', (output / route / "index.html").read_text())
        alias = (output / "old/page.html").read_text()
        self.assertIn("../examples/topic/test-one/", alias)
        self.assertIn("location.search + location.hash", alias)
        self.assertTrue((output / ".nojekyll").exists())

    @unittest.skipUnless(os.environ.get("BOOK_INTEGRATION_TEST"), "set BOOK_INTEGRATION_TEST=1 to run Jupyter Book")
    def test_real_engine_uses_saved_outputs_without_executing(self):
        (self.book / "publishing.yml").write_text(yaml.safe_dump(self.settings))
        (self.book / "myst.yml").write_text(yaml.safe_dump({
            "version": 1, "project": {},
            "site": {"template": "book-theme", "options": {"folders": True}},
        }))
        self.notebook["metadata"].pop("widgets")
        (self.book / self.source).write_text(json.dumps(self.notebook))
        subprocess.run([sys.executable, ".github/scripts/build_book.py", "--book", str(self.book)], check=True)
        output = self.book / "_build/html"
        page = output / "examples/topic/test-one/index.html"
        self.assertIn("saved output", page.read_text())
        self.assertIn(
            f"{self.settings['repository']}/edit/{self.settings['branch']}/books/{self.source}",
            PageLinks(page.read_text()).links,
        )
        self.assertEqual((output / "_sources" / self.source).read_bytes(), (self.book / self.source).read_bytes())
        launches = [url for url in PageLinks(page.read_text()).links if "/hub/user-redirect/git-pull?" in url]
        self.assertEqual(len(launches), 5)
        article = json.loads((self.book / "_build/myst-source/_build/site/content/examples.topic.test-one.json").read_text())
        self.assertEqual(article["frontmatter"]["execute"], {"skip": True})


if __name__ == "__main__":
    unittest.main()
