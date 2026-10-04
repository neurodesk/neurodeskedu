#!/usr/bin/env python3
"""Tests for resuming Zenodo new versions left unpublished by an earlier run."""

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import urllib.error
from unittest import mock

import pytest

spec = importlib.util.spec_from_file_location(
    "publish_zenodo", Path(__file__).with_name("publish-zenodo.py"))
publish_zenodo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_zenodo)

API = "https://zenodo.test"


def fake_zenodo(record_draft):
    calls = []

    def request(url, *, method="GET", **kwargs):
        calls.append((method, url))
        if url.endswith("/actions/newversion"):
            raise urllib.error.HTTPError(url, 400, "BAD REQUEST", {}, io.BytesIO(b"{}"))
        if url == f"{API}/api/deposit/depositions/1":
            return {"links": {"latest_draft": f"{API}/api/deposit/depositions/2"}}
        if url == f"{API}/api/deposit/depositions/2" and method == "GET":
            return record_draft
        if url.endswith("/actions/publish"):
            return {"id": 2, "conceptrecid": 0, "conceptdoi": "10.5281/zenodo.0"}
        return {}

    return request, calls


def publish(tmp, request):
    content = Path(tmp) / "Example.ipynb"
    content.write_text(json.dumps({"cells": [{"cell_type": "markdown", "source": "**Author**: Jane Doe"}]}))
    mapping = Path(tmp) / "doi-mapping.json"
    mapping.write_text(json.dumps({"books/Example.ipynb": {"record_id": "1", "checksum": "old"}}))
    with mock.patch.object(publish_zenodo, "api_request", request):
        return publish_zenodo.publish_content(str(content), "books/Example.ipynb", str(mapping),
                                              str(mapping), "token", API, "https://site")


def test_existing_unpublished_version_is_reused_and_published():
    draft = {"id": 2, "submitted": False, "files": [{"id": "old-file"}],
             "links": {"bucket": f"{API}/bucket"}}
    request, calls = fake_zenodo(draft)
    with tempfile.TemporaryDirectory() as tmp:
        entry = publish(tmp, request)
    assert entry["record_id"] == "2"
    assert ("DELETE", f"{API}/api/deposit/depositions/2/files/old-file") in calls
    assert ("PUT", f"{API}/bucket/Example.ipynb") in calls
    assert ("POST", f"{API}/api/deposit/depositions/2/actions/publish") in calls


def test_published_record_is_never_treated_as_the_draft():
    request, calls = fake_zenodo({"id": 2, "submitted": True, "links": {}})
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(RuntimeError, match="No unpublished draft"):
        publish(tmp, request)
    assert not any(url.endswith("/actions/publish") for _, url in calls)
