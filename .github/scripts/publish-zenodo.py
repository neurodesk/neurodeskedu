#!/usr/bin/env python3
"""Publish educational content to Zenodo with versioning support.

Supported content types:
- Jupyter notebooks (.ipynb)
- Tutorial markdown files (.md)

Exit codes:
    0 - Published successfully (new deposition or new version)
    1 - Error
    2 - Skipped (content unchanged, checksum matches)
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from notebook_metadata import extract_authors_from_content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_content_type(content_path: str) -> str:
    """Return a stable content type label from path extension."""
    lowered = content_path.lower()
    if lowered.endswith(".ipynb"):
        return "notebook"
    if lowered.endswith(".md"):
        return "tutorial"
    return "content"


def build_content_page_url(content_key: str, site_base_url: str) -> str:
    """Build the public website URL for a content key in books/."""
    normalized = content_key.replace("\\", "/").strip()
    if normalized.startswith("books/"):
        relative = normalized[len("books/") :]
    else:
        relative = normalized.lstrip("./")

    if "." in relative:
        page_rel = relative.rsplit(".", 1)[0] + ".html"
    else:
        page_rel = relative + ".html"

    return f"{site_base_url.rstrip('/')}/{page_rel.lstrip('/')}"


def compute_content_checksum(content_path: str) -> str:
    """Compute a stable checksum per content type.

    For notebooks, checksum includes only source cells so output-only changes do not
    trigger DOI updates. For markdown/tutorial files, checksum includes full text.
    """
    content_type = detect_content_type(content_path)

    if content_type == "notebook":
        with open(content_path, "r", encoding="utf-8") as fh:
            notebook = json.load(fh)

        sources = []
        for cell in notebook.get("cells", []):
            source = cell.get("source", [])
            if isinstance(source, list):
                sources.append("".join(source))
            else:
                sources.append(str(source))

        payload = "\n".join(sources)
    else:
        with open(content_path, "r", encoding="utf-8") as fh:
            payload = fh.read().replace("\r\n", "\n")

    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def build_zenodo_metadata(content_name: str, content_type: str,
                          content_key: str, page_url: str,
                          creators: list[dict]) -> dict:
    """Build Zenodo deposition metadata payload."""
    if content_type == "notebook":
        title = f"Neurodesk Notebook: {content_name}"
        summary = "Executed Jupyter notebook from the Neurodesk education platform."
        keywords = ["neurodesk", "neuroimaging", "jupyter", "notebook"]
    elif content_type == "tutorial":
        title = f"Neurodesk Tutorial: {content_name}"
        summary = "Tutorial page from the Neurodesk education platform."
        keywords = ["neurodesk", "neuroimaging", "tutorial", "education"]
    else:
        title = f"Neurodesk Content: {content_name}"
        summary = "Educational content from the Neurodesk platform."
        keywords = ["neurodesk", "neuroimaging", "education"]

    return {
        "metadata": {
            "title": title,
            "upload_type": "lesson",
            "description": (
                f"{summary}\n\n"
                f"Original website: {page_url}\n"
                f"Source path: {content_key}"
            ),
            "creators": creators,
            "license": "MIT",
            "keywords": keywords,
        }
    }


def api_request(url, *, method="GET", data=None, files=None, token=None,
                headers=None, retries=3, backoff=5):
    """Make an HTTP request to the Zenodo API with retry logic.

    ``files`` should be a tuple (filename, file_bytes, content_type) for a
    single file upload.  When *files* is given, the request is sent as
    multipart/form-data.  Otherwise *data* (bytes) is sent as the body.
    """
    hdrs = {"Authorization": f"Bearer {token}"} if token else {}
    if headers:
        hdrs.update(headers)

    for attempt in range(1, retries + 1):
        try:
            if files:
                fname, fbytes, ctype = files
                boundary = f"----ZenodoBoundary{int(time.time()*1000)}"
                body = bytearray()
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(
                    f'Content-Disposition: form-data; name="file"; '
                    f'filename="{fname}"\r\n'.encode()
                )
                body.extend(f"Content-Type: {ctype}\r\n\r\n".encode())
                body.extend(fbytes)
                body.extend(f"\r\n--{boundary}--\r\n".encode())
                hdrs["Content-Type"] = f"multipart/form-data; boundary={boundary}"
                req = urllib.request.Request(url, data=bytes(body), headers=hdrs,
                                            method=method)
            else:
                if data is not None:
                    hdrs.setdefault("Content-Type", "application/json")
                req = urllib.request.Request(url, data=data, headers=hdrs,
                                            method=method)

            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = resp.read()
                if resp_body:
                    return json.loads(resp_body)
                return {}

        except urllib.error.HTTPError as exc:
            status = exc.code
            err_body = exc.read().decode("utf-8", errors="replace")
            if status in (429, 500, 502, 503, 504) and attempt < retries:
                wait = backoff * attempt
                print(f"  Retryable HTTP {status}, waiting {wait}s "
                      f"(attempt {attempt}/{retries})...")
                time.sleep(wait)
                continue
            print(f"HTTP {status}: {err_body}", file=sys.stderr)
            raise
        except urllib.error.URLError as exc:
            if attempt < retries:
                wait = backoff * attempt
                print(f"  Network error: {exc.reason}, waiting {wait}s "
                      f"(attempt {attempt}/{retries})...")
                time.sleep(wait)
                continue
            raise


def delete_draft(api_url, dep_id, token):
    """Best-effort cleanup of a draft deposition."""
    try:
        api_request(f"{api_url}/api/deposit/depositions/{dep_id}",
                    method="DELETE", token=token, retries=1)
        print(f"  Cleaned up draft {dep_id}")
    except Exception:
        print(f"  Warning: could not clean up draft {dep_id}")


# ---------------------------------------------------------------------------
# Core publish logic
# ---------------------------------------------------------------------------

def publish_content(content_path, content_key, doi_mapping_path,
                    output_mapping_path, zenodo_token, api_url,
                    site_base_url):
    """Publish or version a content file on Zenodo.

    Returns the updated mapping entry dict, or None if skipped.
    """
    # Load existing mapping
    if os.path.isfile(doi_mapping_path):
        with open(doi_mapping_path, "r", encoding="utf-8") as fh:
            mapping = json.load(fh)
    else:
        mapping = {}

    # Compute checksum and short-circuit unchanged content
    checksum = compute_content_checksum(content_path)
    existing = mapping.get(content_key)

    if existing and existing.get("checksum") == checksum:
        print(f"Checksum unchanged for {content_key}, skipping.")
        return None  # exit code 2

    content_name = os.path.basename(content_path).rsplit(".", 1)[0]
    content_filename = os.path.basename(content_path)
    content_type = detect_content_type(content_path)
    page_url = build_content_page_url(content_key, site_base_url)

    authors = extract_authors_from_content(content_path)
    creators = [{"name": name} for name in authors] if authors else [{"name": "Neurodesk Project"}]

    if authors:
        print(f"Using {content_type} author metadata: {', '.join(authors)}")
    else:
        print(f"No author metadata found for {content_key}, using fallback creator: Neurodesk Project")

    # Read content bytes for upload
    with open(content_path, "rb") as fh:
        content_bytes = fh.read()

    metadata = build_zenodo_metadata(
        content_name=content_name,
        content_type=content_type,
        content_key=content_key,
        page_url=page_url,
        creators=creators,
    )

    draft_id = None

    try:
        if existing and existing.get("record_id"):
            # --- New version of existing deposition ---
            record_id = existing["record_id"]
            print(f"Creating new version of record {record_id}...")

            try:
                resp = api_request(
                    f"{api_url}/api/deposit/depositions/{record_id}/actions/newversion",
                    method="POST", token=zenodo_token,
                )
            except urllib.error.HTTPError as exc:
                # Zenodo allows one unpublished new version per record. A run whose
                # newversion call timed out can leave one behind, so resume it.
                if exc.code != 400:
                    raise
                print("  An unpublished new version already exists; reusing it...")
                resp = api_request(f"{api_url}/api/deposit/depositions/{record_id}",
                                   token=zenodo_token)

            # The response contains a link to the new draft
            new_draft_url = resp["links"]["latest_draft"]
            draft = api_request(new_draft_url, token=zenodo_token)
            if draft.get("submitted"):
                raise RuntimeError(f"No unpublished draft found for record {record_id}")
            draft_id = draft["id"]
            print(f"  New version draft: {draft_id}")

            # Delete old files from the new draft
            for file_entry in draft.get("files", []):
                api_request(
                    f"{api_url}/api/deposit/depositions/{draft_id}/files/{file_entry['id']}",
                    method="DELETE", token=zenodo_token,
                )
        else:
            # --- Brand new deposition ---
            print(f"Creating new deposition for {content_key}...")
            draft = api_request(
                f"{api_url}/api/deposit/depositions",
                method="POST",
                data=json.dumps(metadata).encode(),
                token=zenodo_token,
            )
            draft_id = draft["id"]
            print(f"  New deposition draft: {draft_id}")

        # Upload content file
        bucket_url = None
        # Prefer bucket API (newer) over files API
        if "links" in draft and "bucket" in draft["links"]:
            bucket_url = draft["links"]["bucket"]

        if bucket_url:
            print(f"  Uploading {content_filename} via bucket API...")
            api_request(
                f"{bucket_url}/{content_filename}",
                method="PUT",
                data=content_bytes,
                headers={"Content-Type": "application/octet-stream"},
                token=zenodo_token,
            )
        else:
            print(f"  Uploading {content_filename} via files API...")
            api_request(
                f"{api_url}/api/deposit/depositions/{draft_id}/files",
                method="POST",
                files=(content_filename, content_bytes, "application/octet-stream"),
                token=zenodo_token,
            )

        # Update metadata
        print("  Updating metadata...")
        api_request(
            f"{api_url}/api/deposit/depositions/{draft_id}",
            method="PUT",
            data=json.dumps(metadata).encode(),
            token=zenodo_token,
        )

        # Publish
        print("  Publishing...")
        published = api_request(
            f"{api_url}/api/deposit/depositions/{draft_id}/actions/publish",
            method="POST",
            token=zenodo_token,
        )

        # Extract DOI information
        concept_doi = published.get("conceptdoi", "")
        concept_recid = str(published.get("conceptrecid", ""))
        record_id = str(published["id"])
        doi_url = (
            f"https://doi.org/{concept_doi}"
            if concept_doi
            else published.get("links", {}).get("conceptdoi", "")
        )

        print(f"  Published! DOI: {doi_url}")
        print(f"  concept_recid={concept_recid}, record_id={record_id}")

        # Update mapping
        mapping[content_key] = {
            "doi_url": doi_url,
            "website_url": page_url,
            "concept_recid": concept_recid,
            "record_id": record_id,
            "content_type": content_type,
            "checksum": checksum,
            "authors": authors,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        with open(output_mapping_path, "w", encoding="utf-8") as fh:
            json.dump(mapping, fh, indent=2)
            fh.write("\n")

        return mapping[content_key]

    except Exception:
        # Try to clean up the draft on failure
        if draft_id is not None:
            delete_draft(api_url, draft_id, zenodo_token)
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Publish notebooks/tutorial markdown files to Zenodo with versioning."
    )
    parser.add_argument("--notebook-path", "--content-path", dest="content_path", required=True,
                        help="Path to content file (.ipynb or .md)")
    parser.add_argument("--notebook-key", "--content-key", dest="content_key", required=True,
                        help="Canonical key in doi-mapping.json (e.g. books/examples/...) ")
    parser.add_argument("--doi-mapping", required=True,
                        help="Path to doi-mapping.json input")
    parser.add_argument("--output-mapping", required=True,
                        help="Path to write updated doi-mapping.json")
    parser.add_argument("--zenodo-token", required=True,
                        help="Zenodo API token")
    parser.add_argument("--api-url", default="https://zenodo.org",
                        help="Zenodo API base URL (default: https://zenodo.org)")
    parser.add_argument("--site-base-url", default="https://neurodesk.org/edu",
                        help="Public base URL for published notebook/tutorial pages")
    args = parser.parse_args()

    try:
        result = publish_content(
            content_path=args.content_path,
            content_key=args.content_key,
            doi_mapping_path=args.doi_mapping,
            output_mapping_path=args.output_mapping,
            zenodo_token=args.zenodo_token,
            api_url=args.api_url,
            site_base_url=args.site_base_url,
        )
        if result is None:
            sys.exit(2)  # Unchanged
        sys.exit(0)  # Published
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
