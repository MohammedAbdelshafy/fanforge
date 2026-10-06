"""Tests for FanForge (stdlib unittest)."""

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fanforge import brief as brief_mod
from fanforge import jobs as jobs_mod
from fanforge import gallery as gallery_mod
from fanforge.backends import registry
from fanforge.backends.mock import MockBackend
from fanforge.brief import BriefValidationError, load_brief, validate_brief
from fanforge.jobs import (
    STATUS_DONE,
    STATUS_QUEUED,
    load_jobs,
    queue_jobs,
    run_queued_jobs,
)

SAMPLE_BRIEF = {
    "project": "test-project",
    "items": [
        {"id": "a", "prompt": "first test prompt", "kind": "image", "aspect": "16:9"},
        {"id": "b", "prompt": "second test prompt", "kind": "video"},
        {"id": "c", "prompt": "third test prompt", "kind": "audio", "notes": "n"},
    ],
}


def write_brief(tmpdir, data):
    path = Path(tmpdir) / "brief.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class BriefValidationTests(unittest.TestCase):
    def test_valid_brief_accepted(self):
        data = validate_brief(json.loads(json.dumps(SAMPLE_BRIEF)))
        self.assertEqual(data["project"], "test-project")

    def test_missing_project_rejected(self):
        with self.assertRaises(BriefValidationError):
            validate_brief({"items": SAMPLE_BRIEF["items"]})

    def test_empty_items_rejected(self):
        with self.assertRaises(BriefValidationError):
            validate_brief({"project": "p", "items": []})

    def test_bad_kind_rejected(self):
        bad = json.loads(json.dumps(SAMPLE_BRIEF))
        bad["items"][0]["kind"] = "hologram"
        with self.assertRaises(BriefValidationError):
            validate_brief(bad)

    def test_missing_prompt_rejected(self):
        bad = json.loads(json.dumps(SAMPLE_BRIEF))
        del bad["items"][1]["prompt"]
        with self.assertRaises(BriefValidationError):
            validate_brief(bad)

    def test_duplicate_ids_rejected(self):
        bad = json.loads(json.dumps(SAMPLE_BRIEF))
        bad["items"][2]["id"] = "a"
        with self.assertRaises(BriefValidationError):
            validate_brief(bad)

    def test_malformed_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "brief.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(BriefValidationError):
                load_brief(path)

    def test_load_brief_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_brief(tmp, SAMPLE_BRIEF)
            data = load_brief(path)
            self.assertEqual(len(data["items"]), 3)


class QueueTests(unittest.TestCase):
    def test_queue_expansion_three_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = queue_jobs(SAMPLE_BRIEF, Path(tmp) / "job1")
            self.assertEqual(len(jobs), 3)
            self.assertTrue(all(j["status"] == STATUS_QUEUED for j in jobs))
            job_file = Path(tmp) / "job1" / "jobs.jsonl"
            self.assertTrue(job_file.exists())
            lines = job_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), 3)
            for line in lines:
                json.loads(line)  # each line is valid JSON

    def test_job_ids_unique_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs1 = queue_jobs(SAMPLE_BRIEF, Path(tmp) / "j1")
            jobs2 = queue_jobs(SAMPLE_BRIEF, Path(tmp) / "j2")
            ids1 = [j["job_id"] for j in jobs1]
            self.assertEqual(len(set(ids1)), 3)
            self.assertEqual(ids1, [j["job_id"] for j in jobs2])


class MockRunTests(unittest.TestCase):
    def _queued_dir(self, tmp):
        job_dir = Path(tmp) / "job1"
        queue_jobs(SAMPLE_BRIEF, job_dir)
        return job_dir

    def test_mock_run_produces_three_real_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = self._queued_dir(tmp)
            done, failed = run_queued_jobs(job_dir, MockBackend())
            self.assertEqual(done, 3)
            self.assertEqual(failed, 0)
            for job in load_jobs(job_dir):
                asset = job_dir / job["asset"]
                self.assertTrue(asset.exists(), f"missing asset {asset}")
                self.assertGreater(asset.stat().st_size, 0, "asset is empty")
                # must be a parseable SVG, not junk
                root = ET.fromstring(asset.read_text(encoding="utf-8"))
                self.assertTrue(root.tag.endswith("svg"))

    def test_mock_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            d1 = self._queued_dir(tmp + "/x")
            d2 = self._queued_dir(tmp + "/y")
            run_queued_jobs(d1, MockBackend())
            run_queued_jobs(d2, MockBackend())
            a1 = sorted((d1 / "assets").glob("*.svg"))
            a2 = sorted((d2 / "assets").glob("*.svg"))
            self.assertEqual(len(a1), 3)
            for p1, p2 in zip(a1, a2):
                self.assertEqual(p1.read_bytes(), p2.read_bytes())

    def test_status_transitions_queued_to_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = self._queued_dir(tmp)
            before = load_jobs(job_dir)
            self.assertTrue(all(j["status"] == STATUS_QUEUED for j in before))
            run_queued_jobs(job_dir, MockBackend())
            after = load_jobs(job_dir)
            self.assertTrue(all(j["status"] == STATUS_DONE for j in after))
            self.assertTrue(all(j["backend"] == "mock" for j in after))
            self.assertTrue(all(j["finished_at"] for j in after))

    def test_failed_backend_marks_job_failed(self):
        from fanforge.backends.base import GeneratorBackend

        class Broken(GeneratorBackend):
            name = "broken"

            def generate(self, job, assets_dir):
                raise RuntimeError("boom")

        with tempfile.TemporaryDirectory() as tmp:
            job_dir = self._queued_dir(tmp)
            done, failed = run_queued_jobs(job_dir, Broken())
            self.assertEqual((done, failed), (0, 3))
            self.assertTrue(all(j["status"] == "failed" for j in load_jobs(job_dir)))

    def test_run_with_no_queue_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                run_queued_jobs(Path(tmp) / "nope", MockBackend())


class GalleryTests(unittest.TestCase):
    def test_gallery_references_all_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp) / "job1"
            queue_jobs(SAMPLE_BRIEF, job_dir)
            run_queued_jobs(job_dir, MockBackend())
            gallery_path = gallery_mod.build_gallery(job_dir, project="test-project")
            self.assertTrue(gallery_path.exists())
            text = gallery_path.read_text(encoding="utf-8")
            for job in load_jobs(job_dir):
                self.assertIn(job["item_id"], text)
                self.assertIn(job["asset"], text)  # asset path referenced
                self.assertTrue((job_dir / job["asset"]).exists())


class RegistryTests(unittest.TestCase):
    def test_registry_loads_mock(self):
        cls = registry.get("mock")
        self.assertIs(cls, MockBackend)
        self.assertEqual(cls().name, "mock")

    def test_registry_unknown_backend_errors(self):
        with self.assertRaises(KeyError):
            registry.get("does-not-exist")

    def test_registry_lists_mock(self):
        self.assertIn("mock", registry.available())


class CliTests(unittest.TestCase):
    def test_cli_end_to_end(self):
        from fanforge.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            brief_path = write_brief(tmp, SAMPLE_BRIEF)
            job_dir = str(Path(tmp) / "job1")
            self.assertEqual(main(["queue", "--brief", str(brief_path), "--out", job_dir]), 0)
            self.assertEqual(main(["run", "--dir", job_dir, "--backend", "mock"]), 0)
            self.assertEqual(
                main(["gallery", "--dir", job_dir, "--project", "test-project"]), 0
            )
            self.assertTrue((Path(job_dir) / "GALLERY.md").exists())
            self.assertEqual(len(list((Path(job_dir) / "assets").glob("*.svg"))), 3)

    def test_cli_queue_rejects_bad_brief(self):
        from fanforge.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            bad = dict(SAMPLE_BRIEF)
            bad["items"] = []
            brief_path = write_brief(tmp, bad)
            self.assertEqual(
                main(["queue", "--brief", str(brief_path), "--out", str(Path(tmp) / "j")]), 2
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
