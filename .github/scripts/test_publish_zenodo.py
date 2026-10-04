"""Tests for creating and resuming Zenodo publication drafts without network access."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


spec = importlib.util.spec_from_file_location(
    "publish_zenodo", Path(__file__).with_name("publish-zenodo.py")
)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublishZenodoTests(unittest.TestCase):
    api_url = "https://zenodo.example"
    content_key = "books/tutorials/example.md"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.content = root / "example.md"
        self.content.write_text("# Example\n\n**Author**: Jane Doe\n", encoding="utf-8")
        self.mapping_path = root / "doi-mapping.json"
        self.mapping = {
            self.content_key: {
                "record_id": "100", "concept_recid": "99", "checksum": "old",
            },
            "books/other.md": {"record_id": "50"},
        }
        self.mapping_path.write_text(json.dumps(self.mapping), encoding="utf-8")
        self.draft = {
            "id": 101, "submitted": False,
            "links": {"bucket": f"{self.api_url}/api/files/draft-bucket"},
            "files": [],
        }
        self.published = {"id": 101, "conceptrecid": "99", "conceptdoi": "10.5281/zenodo.99"}

    def publish(self):
        return publisher.publish_content(
            str(self.content), self.content_key,
            str(self.mapping_path), str(self.mapping_path),
            "test-token", self.api_url, "https://neurodesk.example/edu",
        )

    def test_new_version_publishes_and_updates_mapping(self):
        with patch.object(publisher, "api_request", side_effect=[
            {"id": 101}, self.draft, {}, {}, self.published,
        ]) as request:
            result = self.publish()
        self.assertEqual(request.call_args_list[0].args[0], f"{self.api_url}/api/records/100/versions")
        self.assertEqual(request.call_args_list[0].kwargs["method"], "POST")
        self.assertEqual(request.call_args_list[1].args[0], f"{self.api_url}/api/deposit/depositions/101")
        self.assertEqual(request.call_args_list[2].kwargs["data"], self.content.read_bytes())
        metadata = json.loads(request.call_args_list[3].kwargs["data"])["metadata"]
        self.assertEqual(metadata["creators"], [{"name": "Jane Doe"}])
        self.assertEqual(result["record_id"], "101")
        self.assertEqual(result["doi_url"], "https://doi.org/10.5281/zenodo.99")
        mapping = json.loads(self.mapping_path.read_text())
        self.assertEqual(mapping[self.content_key], result)
        self.assertEqual(mapping["books/other.md"], self.mapping["books/other.md"])

    def test_existing_draft_files_are_replaced_before_upload(self):
        self.draft["files"] = [{"id": "old-file"}, {"id": "partial-upload"}]

        def zenodo_request(url, *, method="GET", **kwargs):
            if url.endswith("/actions/newversion"):
                raise urllib.error.HTTPError(url, 400, "Please remove all files first.", {}, None)
            if url.endswith("/versions"):
                return {"id": 101}
            if method == "GET":
                return self.draft
            if url.endswith("/actions/publish"):
                return self.published
            return {}

        with patch.object(publisher, "api_request", side_effect=zenodo_request) as request:
            self.publish()
        deletions = [c for c in request.call_args_list if c.kwargs.get("method") == "DELETE"]
        self.assertEqual([c.args[0] for c in deletions], [
            f"{self.api_url}/api/deposit/depositions/101/files/old-file",
            f"{self.api_url}/api/deposit/depositions/101/files/partial-upload",
        ])
        self.assertEqual(request.call_args_list[4].kwargs["data"], self.content.read_bytes())

    def test_published_or_original_record_is_never_modified(self):
        for record_id, submitted in [(101, True), (100, False), (101, None)]:
            with self.subTest(record_id=record_id, submitted=submitted):
                draft = dict(self.draft, id=record_id, submitted=submitted)
                with patch.object(publisher, "api_request", side_effect=[{"id": record_id}, draft]) as request:
                    with self.assertRaisesRegex(ValueError, "unpublished new-version draft"):
                        self.publish()
                self.assertEqual(request.call_count, 2)
                self.assertEqual(json.loads(self.mapping_path.read_text()), self.mapping)

    def test_upload_failure_cleans_up_draft_and_preserves_mapping(self):
        error = urllib.error.URLError("upload interrupted")
        with patch.object(publisher, "api_request", side_effect=[
            {"id": 101}, self.draft, error, {},
        ]) as request:
            with self.assertRaises(urllib.error.URLError):
                self.publish()
        self.assertEqual(request.call_args.args[0], f"{self.api_url}/api/deposit/depositions/101")
        self.assertEqual(request.call_args.kwargs["method"], "DELETE")
        self.assertEqual(json.loads(self.mapping_path.read_text()), self.mapping)

    def test_version_creation_error_is_propagated_without_cleanup(self):
        error = urllib.error.HTTPError("versions", 403, "Forbidden", {}, None)
        with patch.object(publisher, "api_request", side_effect=error) as request:
            with self.assertRaises(urllib.error.HTTPError):
                self.publish()
        self.assertEqual(request.call_count, 1)
        self.assertEqual(json.loads(self.mapping_path.read_text()), self.mapping)

    def test_unchanged_content_skips_all_requests(self):
        self.mapping[self.content_key]["checksum"] = publisher.compute_content_checksum(str(self.content))
        self.mapping_path.write_text(json.dumps(self.mapping), encoding="utf-8")
        with patch.object(publisher, "api_request") as request:
            self.assertIsNone(self.publish())
        request.assert_not_called()

    def test_first_publication_still_creates_deposition(self):
        del self.mapping[self.content_key]
        self.mapping_path.write_text(json.dumps(self.mapping), encoding="utf-8")
        with patch.object(publisher, "api_request", side_effect=[
            self.draft, {}, {}, self.published,
        ]) as request:
            self.publish()
        self.assertEqual(request.call_args_list[0].args[0], f"{self.api_url}/api/deposit/depositions")
        self.assertEqual(request.call_args_list[0].kwargs["method"], "POST")


if __name__ == "__main__":
    unittest.main()
