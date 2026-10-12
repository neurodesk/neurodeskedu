import json
import io
import hashlib
import shutil
import struct
import tarfile
import zlib
from contextlib import redirect_stdout
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
import install_oxipng
from build_book import adapt_markdown, controls, discover, embed_widgets, finish, merge_streams, prepare
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
        meta = yaml.safe_load(text.split("---\n")[1])
        self.assertEqual(meta["edit_url"],
                         "https://github.dev/neurodesk/neurodeskedu/blob/main/books/examples/topic/Test_one.ipynb")
        self.assertEqual(yaml.safe_load((stage / "intro.md").read_text().split("---\n")[1])["edit_url"],
                         "https://github.com/neurodesk/neurodeskedu/edit/main/books/intro.md")
        self.assertIn("{admonition} Unreviewed", text)
        self.assertEqual(text.count("/hub/user-redirect/git-pull?"), 5)

    def test_stream_outputs_are_merged_per_stream_like_jupyter_book_1(self):
        stream = lambda name, text: {"output_type": "stream", "name": name, "text": text}
        result = {"output_type": "execute_result", "execution_count": 4, "metadata": {}, "data": {"text/plain": "1"}}
        self.notebook["cells"][1]["outputs"] = [
            stream("stderr", ["[dipy] INFO: Downloading\n"]), stream("stderr", "[dipy] INFO: From: url\n"),
            stream("stdout", ["Data shape: (81, 106)\n"]), stream("stderr", "10%\r100%\n"), result,
        ]
        (self.book / self.source).write_text(json.dumps(self.notebook))
        pages, toc = discover(self.book)
        prepare(self.book, self.root / "stage", pages, toc, self.settings, {})
        outputs = json.loads((self.root / "stage" / self.source).read_text())["cells"][1]["outputs"]
        self.assertEqual(outputs, [
            stream("stderr", "[dipy] INFO: Downloading\n[dipy] INFO: From: url\n100%\n"),
            stream("stdout", ["Data shape: (81, 106)\n"]), result,
        ])
        self.assertEqual(merge_streams([]), [])

    def test_scroll_output_tag_marks_the_cell_for_the_scroll_style(self):
        self.notebook["cells"][1]["metadata"]["tags"].append("scroll-output")
        (self.book / self.source).write_text(json.dumps(self.notebook))
        pages, toc = discover(self.book)
        prepare(self.book, self.root / "stage", pages, toc, self.settings, {})
        cell = json.loads((self.root / "stage" / self.source).read_text())["cells"][1]
        self.assertEqual(cell["metadata"]["class"], "nd-scroll-output")
        self.assertIn(".nd-scroll-output", Path("books/_static/review-badge.css").read_text())

    def test_progress_bar_cleanup_matches_carriage_return_semantics_in_linear_time(self):
        import random, re, time
        def clean(text):
            return merge_streams([{"output_type": "stream", "name": "stdout", "text": text}])[0]["text"]
        rng = random.Random(0)
        for _ in range(2000):
            text = "".join(rng.choice("ab\r\n") for _ in range(rng.randint(1, 12)))
            expected = re.sub(r".*\r(?=[^\n])", "", text.replace("\r\n", "\n")) if "\r" in text else text
            self.assertEqual(clean(text), expected, repr(text))
        start = time.monotonic()
        self.assertEqual(clean("0%\r50%\r100%" + "x" * 1_000_000), "100%" + "x" * 1_000_000)
        self.assertLess(time.monotonic() - start, 2)
        chunks = [{"output_type": "stream", "name": "stdout", "text": "y" * 100 + "\n"} for _ in range(20_000)]
        start = time.monotonic()
        self.assertEqual(merge_streams(chunks)[0]["text"], ("y" * 100 + "\n") * 20_000)
        self.assertLess(time.monotonic() - start, 2)

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

    def test_widget_javascript_is_stored_once_and_referenced(self):
        mime = "application/vnd.jupyter.widget-view+json"
        esm = "export default {}; // " + "x" * 2000
        self.notebook["cells"][1]["outputs"] = [{"output_type": "display_data", "data": {mime: {"model_id": m}}}
                                                for m in ["first", "second"]]
        models = {m: {"state": {"_esm": esm, "volume": m}} for m in ["first", "second"]}
        self.notebook["metadata"]["widgets"] = {"application/vnd.jupyter.widget-state+json": {
            "version_major": 2, "version_minor": 0, "state": models,
        }}
        stage = self.root / "stage"
        embed_widgets(self.notebook, stage, self.source, "/edu")
        folder = stage / "_static/widgets"
        [shared] = folder.glob("esm-*.js")
        self.assertEqual(shared.read_text(), esm)
        for page in folder.glob("*.html"):
            state = json.loads(self.widget_state(page))["state"]
            [model] = state.values()
            self.assertEqual(model["state"]["_esm"], "nd-esm:" + shared.name)
            self.assertNotIn(esm, self.widget_state(page))

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

    def test_published_pngs_shrink_without_changing_pixels(self):
        import io
        from PIL import Image

        figure = Image.new("RGBA", (64, 64))
        figure.putdata([((x * y) % 7 * 30, x * 4, y * 4, 255) for y in range(64) for x in range(64)])
        stored = io.BytesIO()
        figure.save(stored, "PNG", compress_level=0)
        stage = self.root / "stage"
        built = stage / "_build/html"
        content = stage / "_build/site/content"
        content.mkdir(parents=True)
        route = "examples/topic/test-one"
        (content / "page.json").write_text(json.dumps({"location": "/" + str(self.source),
                                                       "slug": route.replace("/", ".")}))
        (built / route).mkdir(parents=True)
        (built / route / "index.html").write_text("<html><head></head><body></body></html>")
        (built / "build").mkdir()
        (built / "build/figure.png").write_bytes(stored.getvalue())
        (built / "build/photo.png").write_bytes(b"\xff\xd8\xff\xe0 a JPEG with a .png name")
        output = self.root / "output"
        finish(stage, self.book, output, [self.source], self.settings)
        optimized = output / "build/figure.png"
        self.assertLess(optimized.stat().st_size, len(stored.getvalue()))
        self.assertEqual(Image.open(optimized).convert("RGBA").tobytes(), figure.tobytes())
        self.assertEqual((output / "build/photo.png").read_bytes(), b"\xff\xd8\xff\xe0 a JPEG with a .png name")

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
        for copy in [built / "_static/widgets/w.html", built / "build/_static/widgets/w.html"]:
            copy.parent.mkdir(parents=True)
            copy.write_text("widget")
        (built / "build/Test_one-0123.ipynb").write_text("{}")
        finish(stage, self.book, output, pages, self.settings)
        self.assertTrue((output / "_static/widgets/w.html").exists())
        self.assertFalse((output / "build/_static").exists())
        self.assertEqual(list((output / "build").glob("*.ipynb")), [])
        self.assertEqual((output / "_sources" / self.source).read_bytes(), (self.book / self.source).read_bytes())
        self.assertIn('name="citation_author" content="Example Author"', (output / route / "index.html").read_text())
        self.assertIn('location.replace("https://neurodesk.org/edu/"', (output / route / "index.html").read_text())
        self.assertIn('<script src="/edu/_static/launch-menu.js" defer>', (output / route / "index.html").read_text())
        self.assertIn('<script src="/edu/_static/home-button.js" defer>', (output / route / "index.html").read_text())
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
            f"https://github.dev/neurodesk/neurodeskedu/blob/{self.settings['branch']}/books/{self.source}",
            PageLinks(page.read_text()).links,
        )
        self.assertEqual((output / "_sources" / self.source).read_bytes(), (self.book / self.source).read_bytes())
        launches = [url for url in PageLinks(page.read_text()).links if "/hub/user-redirect/git-pull?" in url]
        self.assertEqual(len(launches), 5)
        article = json.loads((self.book / "_build/myst-source/_build/site/content/examples.topic.test-one.json").read_text())
        self.assertEqual(article["frontmatter"]["execute"], {"skip": True})


class PngOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "figure.png"

    def write_png(self):
        from PIL import Image
        Image.new("RGBA", (64, 64), (15, 30, 45, 255)).save(self.path, compress_level=0)
        return self.path.read_bytes()

    def test_decoder_failures_warn_and_preserve_input(self):
        for data in (b"\xff\xd8\xff\xe0 a JPEG", self.write_png()[:40]):
            with self.subTest(data=data):
                self.path.write_bytes(data)
                with redirect_stdout(io.StringIO()) as output:
                    build_book.optimize_png(self.path)
                self.assertIn("::warning::Left figure.png unoptimized:", output.getvalue())
                self.assertEqual(self.path.read_bytes(), data)

    def test_native_16_bit_rgb_samples_survive_optimization(self):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

        width, height = 64, 64
        samples = bytes().join(struct.pack(">HHH", x * 997, y * 991, (x * y * 31) % 65536)
                              for y in range(height) for x in range(width))
        rows = b"".join(b"\0" + samples[y * width * 6:(y + 1) * width * 6] for y in range(height))
        original = (b"\x89PNG\r\n\x1a\n"
                    + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(rows, level=0)) + chunk(b"IEND", b""))
        self.path.write_bytes(original)
        build_book.optimize_png(self.path)
        optimized = self.path.read_bytes()
        self.assertLess(len(optimized), len(original))
        self.assertEqual(struct.unpack(">IIBBBBB", optimized[16:29]), (64, 64, 16, 2, 0, 0, 0))
        compressed = b""
        offset = 8
        while offset < len(optimized):
            length = struct.unpack(">I", optimized[offset:offset + 4])[0]
            if optimized[offset + 4:offset + 8] == b"IDAT":
                compressed += optimized[offset + 8:offset + 8 + length]
            offset += length + 12
        filtered = zlib.decompress(compressed)
        decoded = bytearray()
        previous = bytearray(width * 6)
        for y in range(height):
            offset = y * (width * 6 + 1)
            filter_type = filtered[offset]
            row = bytearray(filtered[offset + 1:offset + 1 + width * 6])
            for x in range(len(row)):
                left = row[x - 6] if x >= 6 else 0
                above = previous[x]
                upper_left = previous[x - 6] if x >= 6 else 0
                prediction = left + above - upper_left
                paeth = min((left, above, upper_left), key=lambda value: abs(prediction - value))
                predictors = (0, left, above, (left + above) // 2, paeth)
                row[x] = (row[x] + predictors[filter_type]) % 256
            decoded.extend(row)
            previous = row
        self.assertEqual(decoded, samples)

    def test_missing_input_fails(self):
        with self.assertRaisesRegex(RuntimeError, "oxipng failed"):
            build_book.optimize_png(self.path)

    def test_missing_tool_fails_before_build_and_during_optimization(self):
        self.write_png()
        with mock.patch.dict(os.environ, {"PATH": str(self.root)}):
            with self.assertRaises(FileNotFoundError):
                build_book.optimize_png(self.path)
            result = subprocess.run([sys.executable, ".github/scripts/build_book.py", "--book", str(self.root)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("run python .github/scripts/install_oxipng.py", result.stderr)
            with self.assertRaisesRegex(FileNotFoundError, "oxipng is required"):
                finish(self.root, self.root, self.root, [], {})

    def test_nonexecutable_tool_fails(self):
        binary = self.root / "oxipng"
        shutil.copyfile(shutil.which("oxipng"), binary)
        binary.chmod(0o644)
        with mock.patch.dict(os.environ, {"PATH": str(self.root)}):
            with self.assertRaises(PermissionError):
                build_book.optimize_png(self.path)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root bypasses file permissions")
    def test_file_access_failures_propagate_without_warning(self):
        original = self.write_png()
        for mode in (0o000, 0o444):
            with self.subTest(mode=mode):
                self.path.chmod(mode)
                try:
                    with redirect_stdout(io.StringIO()) as output:
                        with self.assertRaisesRegex(RuntimeError, "Failed to open file for reading|Permission denied"):
                            build_book.optimize_png(self.path)
                    self.assertEqual(output.getvalue(), "")
                finally:
                    self.path.chmod(0o600)
                self.assertEqual(self.path.read_bytes(), original)


class OxipngInstallerTests(unittest.TestCase):
    def test_archive_integrity_and_atomic_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            installed = destination / "oxipng"
            installed.write_bytes(b"previous installation")
            for scenario in ("checksum", "symlink", "version", "success", "success"):
                with self.subTest(scenario=scenario):
                    archive_bytes = io.BytesIO()
                    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
                        member = tarfile.TarInfo(f"oxipng-{install_oxipng.VERSION}-test/oxipng")
                        version = "wrong" if scenario == "version" else install_oxipng.VERSION
                        executable = f"#!/bin/sh\necho oxipng {version}\n".encode()
                        if scenario == "symlink":
                            member.type = tarfile.SYMTYPE
                            member.linkname = "../../outside"
                        else:
                            member.size = len(executable)
                        archive.addfile(member, io.BytesIO(executable))
                    data = archive_bytes.getvalue()
                    digest = "wrong" if scenario == "checksum" else hashlib.sha256(data).hexdigest()
                    host = (install_oxipng.platform.system(), install_oxipng.platform.machine())
                    before = installed.read_bytes()
                    with mock.patch.object(install_oxipng, "ASSETS", {host: ("test", digest)}), \
                         mock.patch.object(install_oxipng, "urlopen", return_value=io.BytesIO(data)):
                        if scenario == "success":
                            self.assertEqual(install_oxipng.install(destination), installed)
                            self.assertEqual(installed.read_bytes(), executable)
                            self.assertTrue(os.access(installed, os.X_OK))
                        else:
                            with self.assertRaises(RuntimeError):
                                install_oxipng.install(destination)
                            self.assertEqual(installed.read_bytes(), before)
                    self.assertEqual(list(destination.iterdir()), [installed])


if __name__ == "__main__":
    unittest.main()
