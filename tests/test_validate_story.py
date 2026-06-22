import tempfile
import unittest
from pathlib import Path

from scripts.validate_story import validate_file


VALID = """---
id: test
revision: v1
status: needs-human-review
created_at: 2026-06-22
source_refs: []
claim_status: unresolved
supersedes: null
stale_reason: null
---
[unresolved] The door may be locked.
"""


class ValidateStoryTests(unittest.TestCase):
    def write(self, directory: Path, name: str, text: str) -> Path:
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_artifact_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.write(root, "outline-v1.md", VALID)
            self.assertEqual(validate_file(path, root), [])

    def test_unresolved_body_requires_unresolved_top_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.write(root, "outline-v1.md", VALID.replace("claim_status: unresolved", "claim_status: confirmed"))
            codes = {finding.code for finding in validate_file(path, root)}
            self.assertIn("claim_status.unresolved", codes)

    def test_revision_must_match_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.write(root, "outline-v2.md", VALID)
            codes = {finding.code for finding in validate_file(path, root)}
            self.assertIn("revision.filename", codes)


if __name__ == "__main__":
    unittest.main()
