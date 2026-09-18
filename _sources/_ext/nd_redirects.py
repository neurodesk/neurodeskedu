"""Sphinx extension: emit redirect stubs for pages that have moved.

When a page is moved to a new location in the book its old URL stops
working, and links published elsewhere (papers, slides, the Neurodesk
website) break.  This extension keeps the old URL alive by writing a
small HTML file at the old path that redirects to the new one.

Setup (in _config.yml):
  sphinx:
    config:
      nd_redirects:
        # old docname (no extension): new docname or absolute URL
        examples/workflows/RISE_slideshow: tutorials/about_neurodesk/RISE_slideshow
    local_extensions:
      nd_redirects: _ext

Targets that start with a scheme (https://...) or a slash are used as
given; anything else is treated as a docname in this book and turned
into a link relative to the old page, so the stubs work regardless of
the domain or subpath the book is served from.
"""

from __future__ import annotations

import posixpath
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

# The stub is marked noindex so search engines keep the moved page (and
# not this placeholder) in their results; the meta refresh is what tells
# them where the content went.
REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0; url={target}">
    <meta name="robots" content="noindex">
    <title>This page has moved</title>
  </head>
  <body>
    <p>This page has moved. If you are not redirected automatically,
       <a href="{target}">follow this link to its new location</a>.</p>
  </body>
</html>
"""


def _resolve_target(old_docname: str, target: str) -> str:
    """Turn a redirect target into a URL relative to the old page."""
    if "://" in target or target.startswith(("/", "#")):
        return target

    if not target.endswith(".html"):
        target = f"{target}.html"

    # Both paths are docname-style (posix, relative to the book root), so
    # a relative link keeps the stub working under any base URL.
    old_dir = posixpath.dirname(old_docname)
    return posixpath.relpath(target, old_dir) if old_dir else target


def write_redirects(app: Sphinx, exception: Exception | None) -> None:
    """build-finished event handler — write the redirect stubs."""
    if exception is not None:
        return

    redirects = app.config.nd_redirects or {}
    if not redirects:
        return

    if app.builder.name not in ("html", "dirhtml"):
        return

    outdir = Path(app.outdir)

    for old_docname, target in redirects.items():
        old_docname = str(old_docname).strip("/")

        if old_docname in app.env.found_docs:
            logger.warning(
                "nd_redirects: %s is still a page in this book; "
                "not overwriting it with a redirect stub",
                old_docname,
            )
            continue

        stub_path = outdir / f"{old_docname}.html"
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        stub_path.write_text(
            REDIRECT_TEMPLATE.format(target=_resolve_target(old_docname, str(target))),
            encoding="utf-8",
        )
        logger.info("nd_redirects: wrote redirect %s -> %s", old_docname, target)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("nd_redirects", {}, "html")
    app.connect("build-finished", write_redirects)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
