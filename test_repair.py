"""Regression tests using the complete, captured public catalogue as a fixture."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import repair_catalogue as repair

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
KNOWN_SHAPES = {
    ("PHerc0500P2", "20250526151718"): [28096, 18209, 18209],
    ("PHerc0500P2", "20250528085330"): [15838, 9423, 9423],
    ("PHerc0500P2", "20250820143440"): [7057, 4196, 4196],
    ("PHerc0343P", "20250521134555"): [5398, 5057, 5057],
}


def apply_patch_independently(original, patch):
    """Small test/replace interpreter, independent of the repair mutator."""
    document = copy.deepcopy(original)
    for operation in patch:
        parts = [p.replace("~1", "/").replace("~0", "~") for p in operation["path"][1:].split("/")]
        parent = document
        for key in parts[:-1]:
            parent = parent[int(key)] if isinstance(parent, list) else parent[key]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if operation["op"] == "test":
            if parent[key] != operation["value"]:
                raise ValueError("JSON Patch precondition failed")
        elif operation["op"] == "replace":
            if isinstance(parent, dict) and key not in parent:
                raise KeyError(key)
            parent[key] = copy.deepcopy(operation["value"])
        else:
            raise ValueError("Unsupported operation")
    return document


class RealCatalogueRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = repair.read_json(EVIDENCE / "metadata.original.json")
        cls.arrays = repair.load_evidence(EVIDENCE)

    def test_live_fixture_has_the_seven_reported_failures(self):
        result = repair.audit(self.original, self.arrays)
        self.assertEqual(result["selected_shapes_matching_arrays"], 0)
        self.assertEqual(result["selected_references_resolving"], 0)

    def test_default_repairs_six_and_preserves_segment(self):
        result, patch = repair.repair(self.original, self.arrays)
        self.assertEqual(sum(p["op"] == "replace" for p in patch), 6)
        for (sample, volume), expected in KNOWN_SHAPES.items():
            self.assertEqual(result["samples"][sample]["volumes"][volume]["properties"]["shape"], expected)
        original_segment = self.original["samples"]["PHerc0009B"]["segments"]["20250910185200"]
        self.assertEqual(result["samples"]["PHerc0009B"]["segments"]["20250910185200"], original_segment)
        self.assertEqual(repair.audit(result, self.arrays)["selected_references_resolving"], 2)

    def test_opt_in_segment_uses_the_declared_original_volume(self):
        result, patch = repair.repair(self.original, self.arrays, True)
        ref = result["samples"]["PHerc0009B"]["segments"]["20250910185200"]["creation"]["derived_from"]
        self.assertEqual(ref, {"type": "volume", "id": "20250820154339"})
        checked = repair.verify(self.original, result, self.arrays, True)
        self.assertEqual(checked["semantic_change_count"], 7)
        self.assertEqual(checked["after"]["selected_references_resolving"], 3)

    def test_generated_patch_matches_corrected_document(self):
        for include in (False, True):
            with self.subTest(include_segment=include):
                result, patch = repair.repair(self.original, self.arrays, include)
                self.assertEqual(apply_patch_independently(self.original, patch), result)
                first_replace = next(i for i, p in enumerate(patch) if p["op"] == "replace")
                self.assertTrue(all(p["op"] == "test" for p in patch[:first_replace]))
                self.assertTrue(all(p["op"] == "replace" for p in patch[first_replace:]))

    def test_repeat_repair_has_no_changes(self):
        for include in (False, True):
            result, unused = repair.repair(self.original, self.arrays, include)
            second, patch = repair.repair(result, self.arrays, include)
            self.assertEqual(second, result)
            self.assertEqual(patch, [])

    def test_conflicting_shape_aborts_without_mutating_input(self):
        changed = copy.deepcopy(self.original)
        changed["samples"]["PHerc0500P2"]["volumes"]["20250820143440"]["properties"]["shape"] = [1, 2, 3]
        saved = copy.deepcopy(changed)
        with self.assertRaises(repair.RepairError):
            repair.repair(changed, self.arrays)
        self.assertEqual(changed, saved)

    def test_changed_reference_identity_aborts(self):
        changed = copy.deepcopy(self.original)
        changed["samples"]["PHerc0009B"]["volumes"]["20250521125136"]["creation"]["derived_from"]["id"] = "different"
        with self.assertRaises(repair.RepairError):
            repair.repair(changed, self.arrays)

    def test_segment_proposal_rejects_changed_original_volume(self):
        changed = copy.deepcopy(self.original)
        changed["samples"]["PHerc0009B"]["segments"]["20250910185200"]["original_volume_id"] = "different"
        with self.assertRaises(repair.RepairError):
            repair.repair(changed, self.arrays, True)

    def test_unrelated_user_metadata_survives_and_input_is_unchanged(self):
        changed = copy.deepcopy(self.original)
        changed["review_note"] = {"keep": ["local annotation", 1, True]}
        saved = copy.deepcopy(changed)
        result, unused = repair.repair(changed, self.arrays, True)
        self.assertEqual(changed, saved)
        self.assertEqual(result["review_note"], changed["review_note"])
        self.assertEqual(len(repair.differences(changed, result)), 7)

    def test_verify_detects_an_unrelated_change(self):
        result, unused = repair.repair(self.original, self.arrays, True)
        result["unexpected"] = "change"
        with self.assertRaises(repair.RepairError):
            repair.verify(self.original, result, self.arrays, True)

    def test_corrupted_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "evidence"
            shutil.copytree(EVIDENCE, copy)
            target = copy / "PHerc0500P2_20250526151718.zarray.json"
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(repair.RepairError, "hash mismatch"):
                repair.load_evidence(copy)

    def test_cli_refuses_to_overwrite_an_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output, patch = Path(tmp) / "output.json", Path(tmp) / "patch.json"
            output.write_text("preserve me")
            process = subprocess.run([sys.executable, str(HERE / "repair_catalogue.py"), "apply",
                                      "--catalogue", str(EVIDENCE / "metadata.original.json"),
                                      "--evidence", str(EVIDENCE), "--out", str(output), "--patch", str(patch)],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(output.read_text(), "preserve me")
            self.assertFalse(patch.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
