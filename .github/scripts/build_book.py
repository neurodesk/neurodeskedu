#!/usr/bin/env python3
"""Build the MyST site from saved outputs without modifying source notebooks."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import html
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote, unquote, urlencode

import yaml

from notebook_metadata import extract_authors_from_content


def discover(book: Path) -> tuple[list[Path], list[dict]]:
    pages = sorted(
        p.relative_to(book) for p in book.rglob("*")
        if p.suffix in {".md", ".ipynb"}
        and not any(part.startswith(("_", ".")) for part in p.relative_to(book).parts)
    )
    if Path("intro.md") not in pages:
        raise ValueError("The book needs an intro.md landing page")
    stems = [p.with_suffix("").as_posix() for p in pages]
    if len(stems) != len(set(stems)):
        raise ValueError("Markdown and notebook pages cannot share a source stem")

    def entries(folder: Path) -> list[dict]:
        direct = [p for p in pages if p.parent == folder and p.name != "intro.md"]
        order = ["examples", "tutorials", "review"] if folder == Path("contribute") else []
        direct.sort(key=lambda p: (order.index(p.stem) if p.stem in order else len(order), p))
        nodes = [{"file": p.as_posix()} for p in direct]
        dirs = {folder / p.relative_to(folder).parts[0] for p in pages
                if p.is_relative_to(folder) and len(p.relative_to(folder).parts) > 1}
        preferred = ["examples", "tutorials", "contribute"] if folder == Path(".") else []
        for directory in sorted(dirs, key=lambda p: (
            preferred.index(p.name) if p.name in preferred else len(preferred), p
        )):
            intro = directory / "intro.md"
            if intro not in pages:
                raise ValueError(f"Missing section landing page: {intro}")
            node = {"file": intro.as_posix()}
            children = entries(directory)
            if children:
                node["children"] = children
            nodes.append(node)
        return nodes

    return pages, [{"file": "intro.md"}, *entries(Path("."))]


def frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not match:
        return {}, text
    return yaml.safe_load(match[1]) or {}, text[match.end():]


def link(label: str, url: str) -> str:
    label = re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", label.replace("\n", " "))
    return f"[{label}](<{quote(url, safe=':/?#=&%+@,;~')}>)"


def heading_id(text: str) -> str:
    text = re.sub(r"['‘’\"“”]+", "", text.strip().lower())
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"^([0-9-])", r"id-\1", text)
    return re.sub(r"-+", "-", text).strip("-")


def adapt_markdown(text: str, headings: set[str]) -> str:
    text = re.sub(r"(?im)(\b(?:github|twitter):\s*\[?)@([\w-]+)", r"\1\\@\2", text)
    text = re.sub(r"\(@([\w-]+)\)", r"(\\@\1)", text)

    def target(match: re.Match) -> str:
        normalized = heading_id(unquote(match[1]))
        return f"](#{normalized})" if normalized in headings else match[0]

    return re.sub(r"\]\(#([^\s)]+)\)", target, text)


# GitHub Pages rejects files of 100 MB or more, so widget state is split into parts.
WIDGET_PART_SIZE = 50 * 1024**2
# Widget JavaScript (about 5 MB for each NiiVue viewer) is stored once per site and fetched by reference.
ESM_REFERENCE = "nd-esm:"


def embed_widgets(notebook: dict, stage: Path, source: Path, base_url: str) -> None:
    mime = "application/vnd.jupyter.widget-view+json"
    outputs = [output for cell in notebook["cells"] for output in cell.get("outputs", [])
               if mime in output.get("data", {})]
    if not outputs or "widgets" not in notebook["metadata"]:
        return
    state = notebook["metadata"]["widgets"]["application/vnd.jupyter.widget-state+json"]
    models = state["state"]
    folder = stage / "_static/widgets"
    folder.mkdir(parents=True, exist_ok=True)
    for output in outputs:
        view = output["data"][mime]
        selected = {}
        pending = [view["model_id"]]
        while pending:
            model_id = pending.pop()
            if model_id in selected:
                continue
            if model_id not in models:
                selected = None
                break
            selected[model_id] = models[model_id]
            pending.extend(re.findall(r'"IPY_MODEL_([^"\\]+)"', json.dumps(models[model_id])))
        if selected is None:
            del output["data"][mime]
            continue
        stem = hashlib.sha256(f"{source}:{view['model_id']}".encode()).hexdigest()[:24]
        filename = stem + ".html"
        for model_id, model in selected.items():
            esm = model.get("state", {}).get("_esm")
            if isinstance(esm, str) and len(esm) >= 1000:
                name = "esm-" + hashlib.sha256(esm.encode()).hexdigest()[:24] + ".js"
                (folder / name).write_text(esm)
                selected[model_id] = {**model, "state": {**model["state"], "_esm": ESM_REFERENCE + name}}
        widget_state = json.dumps({**state, "state": selected})
        parts = []
        for start in range(0, len(widget_state), WIDGET_PART_SIZE):
            parts.append(f"{stem}.{len(parts)}.txt")
            (folder / parts[-1]).write_text(widget_state[start:start + WIDGET_PART_SIZE])
        widget_view = json.dumps(view).replace("<", "\\u003c")
        (folder / filename).write_text(
            '<!doctype html><html><head><meta charset="utf-8"><title>Interactive notebook output</title>'
            '<style>body{margin:0}.jupyter-widgets{max-width:100%}</style></head><body>'
            # Fit the iframe to the rendered widget; a fixed height leaves a gap under short viewers.
            '<script>new ResizeObserver(() => {const height = document.body.offsetHeight;'
            'if (height && frameElement) frameElement.style.height = height + "px";}).observe(document.body);</script>'
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js"></script>'
            f'<script type="{mime}">{widget_view}</script>'
            '<script>const load = path => fetch(path).then(response => {'
            'if (!response.ok) throw new Error(path + ": " + response.status); return response.text();});'
            'Promise.all(' + json.dumps(parts) + '.map(load)).then(async texts => {'
            'const data = JSON.parse(texts.join(""));'
            'await Promise.all(Object.values(data.state).map(async model => {const esm = model.state?._esm;'
            f'if (typeof esm === "string" && esm.startsWith("{ESM_REFERENCE}")) '
            f'model.state._esm = await load(esm.slice({len(ESM_REFERENCE)}));}}));'
            'const state = document.createElement("script");'
            'state.type = "application/vnd.jupyter.widget-state+json"; state.textContent = JSON.stringify(data);'
            'document.body.append(state); const embed = document.createElement("script");'
            'embed.src = "https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@1.0.15/dist/embed-amd.js";'
            'document.body.append(embed);}).catch(error => {document.body.textContent = '
            '"This interactive output could not be loaded (" + error.message + ").";});</script></body></html>'
        )
        output["data"] = {"text/html": (
            f'<iframe src="{html.escape(base_url, quote=True)}/_static/widgets/{filename}" '
            'title="Interactive notebook output" width="100%" height="620" loading="lazy"></iframe>'
        )}
    del notebook["metadata"]["widgets"]


def require_oxipng() -> None:
    if shutil.which("oxipng") is None:
        raise FileNotFoundError("oxipng is required; run python .github/scripts/install_oxipng.py")


def optimize_png(path: Path) -> None:
    result = subprocess.run(["oxipng", "-o", "2", "--strip", "safe", "--", str(path)],
                            capture_output=True, text=True)
    if result.returncode:
        diagnostic = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
        decoder_errors = {
            f"{path}: Invalid PNG header detected",
            f"{path}: Missing data in the file; the file is truncated",
        }
        if result.returncode == 1 and diagnostic in decoder_errors:
            print(f"::warning::Left {path.name} unoptimized: {diagnostic}")
        else:
            raise RuntimeError(f"oxipng failed for {path} (exit {result.returncode}): {result.stderr.strip()}")


def merge_streams(outputs: list[dict]) -> list[dict]:
    """Join each cell's stdout and stderr into one block apiece, as Jupyter Book 1 did (nb_merge_streams)."""
    merged, streams, parts = [], {}, {}
    for output in outputs:
        if output["output_type"] != "stream":
            merged.append(output)
        elif output["name"] in streams:
            # Join once at the end: appending to a growing string is quadratic for chatty cells.
            parts[output["name"]].append("".join(output["text"]))
        else:
            streams[output["name"]] = output
            parts[output["name"]] = ["".join(output["text"])]
            merged.append(output)
    for name, stream in streams.items():
        if len(parts[name]) > 1:
            stream["text"] = "".join(parts[name])
        if "\r" in "".join(stream["text"]):
            # Keep only the final state of lines redrawn with carriage returns (progress bars).
            # Per line, keep what follows the last carriage return that is not the line's final
            # character. A regex (".*\r(?=[^\n])") does the same but is quadratic on long lines.
            lines = "".join(stream["text"]).replace("\r\n", "\n").split("\n")
            stream["text"] = "\n".join(line[line.rfind("\r", 0, len(line) - 1) + 1:] for line in lines)
    return merged


def controls(source: Path, review_id: str | None, reviews: dict, settings: dict) -> str:
    blocks = []
    if review_id:
        entry = reviews.get(review_id, {})
        state = entry.get("state", "unreviewed")
        labels = {"reviewed": "Reviewed", "in-progress": "Under review", "stale": "Review out-of-date"}
        if state not in labels:
            state = "unreviewed"
        links = [link(label, entry[key]) for key, label in (
            ("review_issue_url", "review issue"), ("doi_url", "DOI")
        ) if entry.get(key)]
        if state in {"reviewed", "stale"}:
            links.extend(link("@" + login, "https://github.com/" + quote(login, safe=""))
                         for login in entry.get("reviewers", []))
        blocks.append(
            f":::{{admonition}} {labels.get(state, 'Unreviewed')}\n"
            f":class: nd-review-badge nd-review-badge--{state}\n\n"
            + " · ".join(links) + "\n:::"
        )
    if source.suffix == ".ipynb":
        repo = settings["repository"]
        query = urlencode({
            "repo": repo, "urlpath": f"lab/tree/{repo.rsplit('/', 1)[1]}/books/{source.as_posix()}",
            "branch": settings["branch"],
        }, safe="/")
        links = ["- " + link(hub["text"], hub["url"].rstrip("/") + "/hub/user-redirect/git-pull?" + query)
                 for hub in settings["hubs"]]
        blocks.append(":::{dropdown} Run this notebook\n:class: nd-launch\n\n" + "\n".join(links) + "\n:::")
    return "\n\n".join(blocks)


def prepare(book: Path, stage: Path, pages: list[Path], toc: list[dict], settings: dict, dois: dict) -> None:
    shutil.copytree(book, stage, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("_build", ".ipynb_checkpoints", "_ext"))
    config = yaml.safe_load((book / "myst.yml").read_text())
    config["project"]["toc"] = toc
    (stage / "myst.yml").write_text(yaml.safe_dump(config, sort_keys=False))
    registry = book / "_static/reviews.json"
    reviews = json.loads(registry.read_text()).get("reviews", {}) if registry.exists() else {}
    for source in pages:
        path = stage / source
        notebook = json.loads(path.read_text()) if source.suffix == ".ipynb" else None
        if notebook is not None:
            cells = notebook["cells"]
            first = cells[0] if cells and cells[0]["cell_type"] == "markdown" else None
            text = "".join(first["source"]) if first else ""
        else:
            text = path.read_text()
        markdown = "\n".join("".join(c["source"]) for c in notebook["cells"]
                             if c["cell_type"] == "markdown") if notebook is not None else text
        headings = {heading_id(h) for h in re.findall(r"(?m)^#{1,6} (.+)$", markdown)}
        meta, body = frontmatter(text)
        meta["execute"] = {"skip": True}
        review_id = meta.get("nd_review_id") or (notebook or {}).get("metadata", {}).get("nd_review_id")
        authors = extract_authors_from_content(str(book / source))
        if authors and not meta.get("authors"):
            meta["authors"] = [{"name": name} for name in authors]
        if meta.get("authors"):
            meta.pop("author", None)
        doi = dois.get("books/" + source.as_posix(), {}).get("doi_url")
        if doi:
            meta["doi"] = doi.removeprefix("https://doi.org/")
        repo_path = "books/" + quote(source.as_posix())
        meta["github"] = f"{settings['repository']}/blob/{settings['branch']}/{repo_path}"
        # GitHub's web editor shows executed notebooks (often several MB of outputs) as an empty
        # document; github.dev opens them in VS Code's notebook editor instead.
        editor = (settings["repository"].replace("://github.com/", "://github.dev/") + "/blob"
                  if notebook is not None else settings["repository"] + "/edit")
        meta["edit_url"] = f"{editor}/{settings['branch']}/{repo_path}"
        meta["downloads"] = [{
            "url": settings["base_url"] + "/_sources/" + quote(source.as_posix()),
            "title": "Download source notebook" if notebook is not None else "Download source",
            "filename": source.name, "static": False,
        }]
        extra = controls(source, review_id, reviews, settings)
        body = adapt_markdown(body, headings)
        heading = re.match(r"(\s*# [^\n]+(?:\n|\Z))(.*)", body, re.S)
        if heading:
            body = heading[1].rstrip("\n") + "\n\n" + extra + "\n\n" + heading[2]
        else:
            body = extra + "\n\n" + body
        text = "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + body
        if notebook is not None:
            for cell in cells:
                if cell["cell_type"] == "markdown":
                    cell["source"] = adapt_markdown("".join(cell["source"]), headings).splitlines(keepends=True)
                elif cell["cell_type"] == "code":
                    cell["outputs"] = merge_streams(cell.get("outputs", []))
                    # MyST parses scroll-output but the book theme ignores it. The theme does add a
                    # cell's metadata class to the rendered block, so review-badge.css can cap it.
                    if "scroll-output" in cell.get("metadata", {}).get("tags", []):
                        cell["metadata"]["class"] = "nd-scroll-output"
            if first is not None:
                first["source"] = text.splitlines(keepends=True)
            else:
                cells.insert(0, {"cell_type": "markdown", "id": "neurodesk-publication",
                                 "metadata": {}, "source": text.splitlines(keepends=True)})
            embed_widgets(notebook, stage, source, settings["base_url"])
            path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")
        else:
            path.write_text(text)


def finish(stage: Path, raw: Path, output: Path, pages: list[Path], settings: dict) -> None:
    require_oxipng()
    built = stage / "_build/html"
    routes = {}
    for path in (stage / "_build/site/content").glob("*.json"):
        article = json.loads(path.read_text())
        source = article.get("location", "").lstrip("/")
        if Path(source) in pages:
            route = "" if article["slug"] == "index" else article["slug"].replace(".", "/") + "/"
            if source in routes or route in routes.values():
                raise ValueError(f"Duplicate exported route: {source}")
            routes[source] = route
    if set(routes) != {p.as_posix() for p in pages}:
        raise ValueError(f"Missing exported pages: {set(map(str, pages)) - set(routes)}")
    # MyST pages only work under base_url. Copies served elsewhere (neurodesk.github.io/neurodeskedu,
    # neurodesk.org/example-notebooks) forward to the same page on the canonical site.
    base = settings["base_url"] + "/"
    guard = (f"<script>if (!location.pathname.startsWith({json.dumps(base)})) location.replace("
             f"{json.dumps(settings['site_url'] + base)} + location.pathname.split('/').slice(2).join('/')"
             " + location.search + location.hash);</script>")
    launch = "".join(f'<script src="{html.escape(base, quote=True)}_static/{name}" defer></script>'
                     for name in ("launch-menu.js", "home-button.js"))
    for source in pages:
        page = built / routes[source.as_posix()] / "index.html"
        text = page.read_text()
        authors = extract_authors_from_content(str(raw / source))
        tags = [f'<meta name="citation_author" content="{html.escape(name, quote=True)}">' for name in authors]
        if authors:
            names = html.escape(", ".join(authors), quote=True)
            tags += [f'<meta name="author" content="{names}">', f'<meta property="article:author" content="{names}">']
        text = re.sub(r"<head[^>]*>", lambda head: head[0] + guard + launch, text, count=1)
        page.write_text(text.replace("</head>", "".join(tags) + "</head>", 1))
        target = built / "_sources" / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raw / source, target)

    aliases = {p.with_suffix("").as_posix(): p.as_posix() for p in pages}
    aliases.update(settings.get("redirects", {}))
    for old, source in aliases.items():
        path = built / (old + ".html")
        if path.exists():
            raise ValueError(f"Redirect would overwrite an exported page: {path}")
        target = os.path.relpath(built / routes[source], path.parent).replace(os.sep, "/") + "/"
        target = quote(target, safe="/.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex">'
            f'<meta http-equiv="refresh" content="0; url={html.escape(target, quote=True)}">'
            f'<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>'
            f'</head><body><a href="{html.escape(target, quote=True)}">Continue to the page</a></body></html>\n'
        )
    # MyST publishes static_files at the site root and again under build/; pages only use the root copy.
    shutil.rmtree(built / "build/_static", ignore_errors=True)
    # MyST also exports every notebook to build/; the Downloads menu serves the raw source from _sources.
    for export in (built / "build").glob("*.ipynb"):
        export.unlink()
    (built / ".nojekyll").touch()
    (built / "neurodesk-pages.json").write_text(json.dumps(routes, indent=2) + "\n")
    # Lossless recompression saves about a third of the figure bytes. _sources stays byte-identical.
    pngs = [p for p in built.rglob("*.png") if p.relative_to(built).parts[0] != "_sources"]
    with ProcessPoolExecutor() as pool:
        list(pool.map(optimize_png, pngs))
    oversized = [str(p.relative_to(built)) for p in built.rglob("*") if p.is_file() and p.stat().st_size >= 100 * 1024**2]
    if oversized:
        raise ValueError(f"Files exceed the GitHub Pages publication limit: {oversized}")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(built, output)
    print(f"Published {len(routes)} pages and {len(aliases)} legacy redirects to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path("books"))
    parser.add_argument("--raw-books", type=Path)
    parser.add_argument("--doi-mapping", type=Path, default=Path("doi-mapping.json"))
    parser.add_argument("--base-url")
    args = parser.parse_args()
    require_oxipng()
    book = args.book.resolve()
    raw = (args.raw_books or book).resolve()
    stage = book / "_build/myst-source"
    if stage.exists():
        shutil.rmtree(stage)
    settings = yaml.safe_load((book / "publishing.yml").read_text())
    if args.base_url is not None:
        settings["base_url"] = args.base_url.rstrip("/")
    pages, toc = discover(book)
    dois = json.loads(args.doi_mapping.read_text()) if args.doi_mapping.exists() else {}
    prepare(book, stage, pages, toc, settings, dois)
    subprocess.run(["jupyter-book", "build", "--html", "--ci"], cwd=stage,
                   env={**os.environ, "BASE_URL": settings["base_url"]}, check=True)
    finish(stage, raw, book / "_build/html", pages, settings)


if __name__ == "__main__":
    main()
