#!/usr/bin/env python3
"""Check the exported site's page coverage, launch links, and raw downloads."""

import argparse
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import yaml

from build_book import discover, merge_streams


class PageLinks(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.refresh = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "meta" and attrs.get("http-equiv") == "refresh":
            self.refresh = attrs["content"].split("url=", 1)[1]


def verify(book: Path, raw: Path, preview: bool = False) -> None:
    pages, _ = discover(book)
    output = book / "_build/html"
    if preview:
        output /= "preview"
    routes = json.loads((output / "neurodesk-pages.json").read_text())
    settings = yaml.safe_load((book / "publishing.yml").read_text())
    assert set(routes) == {p.as_posix() for p in pages}, "Exported page inventory differs from the sources"
    assert len(set(routes.values())) == len(pages), "Page routes collide"
    for source in pages:
        page = PageLinks((output / routes[source.as_posix()] / "index.html").read_text())
        editor = (settings["repository"].replace("://github.com/", "://github.dev/") + "/blob"
                  if source.suffix == ".ipynb" else settings["repository"] + "/edit")
        edit_url = f"{editor}/{settings['branch']}/books/{quote(source.as_posix())}"
        assert edit_url in page.links, f"Incorrect source edit link: {source}"
        hubs = [url for url in page.links if "/hub/user-redirect/git-pull?" in url]
        assert len(hubs) == (len(settings["hubs"]) if source.suffix == ".ipynb" else 0), source
        for url in hubs:
            query = parse_qs(urlparse(url).query)
            assert query["repo"] == [settings["repository"]], source
            assert query["branch"] == [settings["branch"]], source
            assert query["urlpath"] == [f"lab/tree/{settings['repository'].rsplit('/', 1)[1]}/books/{source.as_posix()}"], source
        assert (output / "_sources" / source).read_bytes() == (raw / source).read_bytes(), source
        if source.suffix == ".ipynb":
            original = json.loads((book / source).read_text())
            staged = json.loads((book / "_build/myst-source" / source).read_text())
            assert {k: v for k, v in original["metadata"].items() if k != "widgets"} == {
                k: v for k, v in staged["metadata"].items() if k != "widgets"
            }, source
            original_cells = [c for c in original["cells"] if c["cell_type"] != "markdown"]
            staged_cells = [c for c in staged["cells"] if c["cell_type"] != "markdown"]
            assert len(original_cells) == len(staged_cells), source
            for before, after in zip(original_cells, staged_cells):
                if "scroll-output" in before.get("metadata", {}).get("tags", []):
                    before = {**before, "metadata": {**before["metadata"], "class": "nd-scroll-output"}}
                assert {k: v for k, v in before.items() if k != "outputs"} == {
                    k: v for k, v in after.items() if k != "outputs"
                }, source
                expected = merge_streams(copy.deepcopy(before.get("outputs", [])))
                assert len(expected) == len(after.get("outputs", [])), source
                for old_output, new_output in zip(expected, after.get("outputs", [])):
                    if "widgets" in original["metadata"] and "application/vnd.jupyter.widget-view+json" in old_output.get("data", {}):
                        assert "_static/widgets/" in new_output["data"]["text/html"], source
                    else:
                        assert old_output == new_output, source
    aliases = {p.with_suffix("").as_posix(): p.as_posix() for p in pages}
    aliases.update(settings.get("redirects", {}))
    for old, source in aliases.items():
        alias = output / (old + ".html")
        redirect = PageLinks(alias.read_text()).refresh
        assert redirect, alias
        assert (alias.parent / redirect / "index.html").resolve() == (
            output / routes[source] / "index.html"
        ).resolve(), alias
    print(f"Verified {len(pages)} pages, raw downloads, saved notebook cells, and {len(aliases)} redirects")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path("books"))
    parser.add_argument("--raw-books", type=Path)
    parser.add_argument("--with-preview", action="store_true")
    args = parser.parse_args()
    verify(args.book, args.raw_books or args.book)
    if args.with_preview:
        verify(args.book, args.raw_books or args.book, preview=True)
