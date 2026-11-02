"""Project-level regression coverage for the optional KFD linter."""

import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml
from jsonschema import Draft202012Validator


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/kfd_lint.py"
FIXTURE = Path(__file__).parent / "fixtures/valid"
VERSION = (REPO / "VERSION").read_text(encoding="utf-8").strip()
MAJOR, MINOR, PATCH = (int(part) for part in VERSION.split("."))


class LinterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        shutil.copytree(FIXTURE, self.root)
        (self.root / "AGENTS.md").write_text("KFD_VERSION: " + VERSION + "\n", encoding="utf-8")

    def read_yaml(self, relative):
        return yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))

    def write_yaml(self, relative, data):
        (self.root / relative).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def unit(self, name="orders"):
        return self.read_yaml("knowledge/{}/knowledge.yaml".format(name))

    def save_unit(self, data, name="orders"):
        self.write_yaml("knowledge/{}/knowledge.yaml".format(name), data)

    def lint(self, expected=0, strict=False):
        command = [sys.executable, str(SCRIPT), str(self.root)]
        if strict:
            command.append("--strict")
        result = subprocess.run(command, capture_output=True, text=True, cwd=self.temp.name)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertNotIn(str(self.root), result.stdout)
        return result.stdout

    def test_valid_project_and_yaml_date_normalization(self):
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")
        self.assertEqual(self.lint(strict=True), "0 error(s), 0 warning(s)\n")

    def test_default_root(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "0 error(s), 0 warning(s)\n")

    def test_unit_missing_from_index(self):
        index = self.read_yaml("knowledge/index.yaml")
        del index["knowledge"]["orders"]
        self.write_yaml("knowledge/index.yaml", index)
        self.assertIn("unit orders is not listed in index", self.lint(1))

    def test_index_entry_without_unit_file(self):
        index = self.read_yaml("knowledge/index.yaml")
        index["knowledge"]["absent"] = {"name": "Absent"}
        self.write_yaml("knowledge/index.yaml", index)
        self.assertIn("index unit absent has no knowledge/absent/knowledge.yaml", self.lint(1))

    def test_id_must_equal_directory(self):
        unit = self.unit()
        unit["id"] = "different"
        self.save_unit(unit)
        self.assertIn("unit id different does not match directory orders", self.lint(1))

    def test_duplicate_rule_across_groups(self):
        unit = self.unit()
        unit["contract"]["rules"]["extra"] = [{"id": "own-only", "rule": "Repeated"}]
        self.save_unit(unit)
        self.assertIn("duplicate rule id: own-only", self.lint(1))

    def test_missing_mapping_path(self):
        unit = self.unit()
        unit["mapping"]["implementation"]["shared"].append("src/absent.py")
        self.save_unit(unit)
        self.assertIn("mapping path does not exist: src/absent.py", self.lint(1))

    def test_invalid_mapping_paths(self):
        for value in ("/tmp/absolute.py", "../outside.py", "src/../outside.py", "C:/absolute.py", "src\\bad.py"):
            with self.subTest(value=value):
                unit = self.unit()
                unit["mapping"]["implementation"]["shared"] = [value]
                self.save_unit(unit)
                self.assertIn("schema violation", self.lint(1))

    def test_directory_mapping_requires_trailing_slash(self):
        unit = self.unit()
        unit["mapping"]["implementation"]["primary"] = ["src/orders"]
        self.save_unit(unit)
        self.assertIn("mapping directory path must end with '/'", self.lint(1))

    def test_primary_directory_contains_other_units_file(self):
        unit = self.unit("profiles")
        unit["mapping"]["implementation"]["primary"] = ["src/orders/history.py"]
        self.save_unit(unit, "profiles")
        self.assertIn("primary ownership overlap", self.lint(1))

    def test_same_primary_file_in_two_units(self):
        orders = self.unit()
        orders["mapping"]["implementation"]["primary"] = ["src/profiles.py"]
        self.save_unit(orders)
        self.assertIn("primary ownership overlap", self.lint(1))

    def test_primary_shared_overlap_warns(self):
        orders = self.unit()
        orders["mapping"]["implementation"]["shared"].append("src/profiles.py")
        self.save_unit(orders)
        output = self.lint()
        self.assertIn("primary/shared ownership overlap", output)
        self.assertIn("0 error(s), 1 warning(s)", output)

    def test_unknown_dependency_unit(self):
        for kind in ("reads", "writes"):
            with self.subTest(kind=kind):
                unit = self.unit()
                unit["dependencies"] = {kind: {"absent": ["id"]}}
                self.save_unit(unit)
                self.assertIn("unknown dependency unit absent in dependencies." + kind, self.lint(1))

    def test_self_dependency_warns(self):
        unit = self.unit()
        unit["dependencies"]["reads"]["orders"] = ["id"]
        self.save_unit(unit)
        self.assertIn("self-dependency", self.lint())

    def test_unknown_conformance_reference(self):
        for reference in ("absent/missing", "orders/missing"):
            with self.subTest(reference=reference):
                path = self.root / "checks/test_contract.py"
                path.write_text((FIXTURE / "checks/test_contract.py").read_text() + "\n# Conforms to " + reference + "\n")
                self.assertIn("unknown conformance ref " + reference, self.lint(1))

    def test_missing_evidence_warns_and_strict_fails(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"].append({"id": "uncovered", "rule": "Require evidence."})
        self.save_unit(unit)
        output = self.lint()
        self.assertIn("no conformance evidence for orders/uncovered", output)
        self.assertIn("0 error(s), 1 warning(s)", output)
        self.assertEqual(output, self.lint(1, strict=True))

    def test_binary_undecodable_and_large_files_are_skipped(self):
        checks = self.root / "checks"
        (checks / "binary.dat").write_bytes(b"\0# Conforms to absent/binary")
        (checks / "undecodable.dat").write_bytes(b"\xff# Conforms to absent/undecodable")
        (checks / "large.txt").write_bytes(b"# Conforms to absent/large\n" + b"x" * (1024 * 1024))
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_unresolved_affected_rules(self):
        for reference in ("missing", "profiles/missing", "absent/missing"):
            with self.subTest(reference=reference):
                decisions = self.read_yaml("knowledge/orders/decisions.yaml")
                decisions["decisions"][0]["affects_rules"] = [reference]
                self.write_yaml("knowledge/orders/decisions.yaml", decisions)
                self.assertIn("unresolved rule ref " + reference, self.lint(1))

    def test_schema_violation_in_each_document(self):
        for relative in ("knowledge/index.yaml", "knowledge/orders/knowledge.yaml", "knowledge/orders/decisions.yaml"):
            with self.subTest(relative=relative):
                original = (self.root / relative).read_text()
                data = self.read_yaml(relative)
                data["unexpected"] = True
                self.write_yaml(relative, data)
                output = self.lint(1)
                self.assertIn("ERROR " + relative + ": schema violation at $:", output)
                (self.root / relative).write_text(original)

    def test_invalid_unit_does_not_cascade_reference_errors(self):
        # Orders' tests already reference profiles/stable-id, and its decisions
        # reference that rule too. Neither can be checked if profiles is invalid.
        unit = self.unit("profiles")
        unit["unexpected"] = True
        self.save_unit(unit, "profiles")
        output = self.lint(1)
        self.assertIn("ERROR knowledge/profiles/knowledge.yaml: schema violation", output)
        self.assertNotIn("unknown conformance ref", output)
        self.assertNotIn("unresolved rule ref", output)

    def test_yaml_parse_failure(self):
        (self.root / "knowledge/orders/knowledge.yaml").write_text("id: [unterminated\n")
        self.assertIn("YAML parse/read failure", self.lint(1))

    def test_incompatible_and_invalid_versions(self):
        versions = [
            f"{MAJOR + 1}.0.0",
            f"{MAJOR}.{MINOR + 1}",
            "invalid",
            str(MAJOR),
            VERSION + ".1",
        ]
        if MAJOR > 0:
            versions.append(f"{MAJOR - 1}.{MINOR}.0")
        for version in versions:
            with self.subTest(version=version):
                (self.root / "AGENTS.md").write_text("KFD_VERSION: " + version + "\n")
                self.assertIn("KFD_VERSION", self.lint(1))

    def test_compatible_older_minor_and_patch_ignored(self):
        versions = [f"{MAJOR}.{MINOR}", f"{MAJOR}.{MINOR}.999"]
        if MINOR > 0:
            versions.extend([f"{MAJOR}.{MINOR - 1}", f"{MAJOR}.{MINOR - 1}.999"])
        for version in versions:
            with self.subTest(version=version):
                (self.root / "AGENTS.md").write_text("KFD_VERSION: " + version + "\n")
                self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_missing_agents_and_missing_declaration_warn(self):
        agents = self.root / "AGENTS.md"
        agents.unlink()
        self.assertIn("AGENTS.md is missing", self.lint())
        agents.write_text("# No version declaration\n")
        self.assertIn("KFD_VERSION declaration is missing", self.lint())

    def test_numeric_legacy_index_version_and_dependencies_warn_only(self):
        index = self.read_yaml("knowledge/index.yaml")
        # One-digit minor avoids floating-point YAML losing a trailing zero
        # (for example, numeric 1.10 becomes 1.1).
        legacy_minor = min(max(MINOR - 1, 0), 9)
        legacy_version = f"{MAJOR}.{legacy_minor}"
        index["version"] = float(legacy_version)
        index["knowledge"]["orders"]["dependencies"] = {"reads": ["profiles"]}
        self.write_yaml("knowledge/index.yaml", index)
        (self.root / "AGENTS.md").write_text(f"KFD_VERSION: {MAJOR}.{MINOR}.{PATCH + 1}\n")
        output = self.lint()
        self.assertIn("legacy index version differs", output)
        self.assertIn("legacy dependencies in index entry orders", output)
        self.assertIn("0 error(s), 2 warning(s)", output)
        (self.root / "AGENTS.md").write_text("KFD_VERSION: " + legacy_version + ".0\n")
        output = self.lint()
        self.assertNotIn("legacy index version differs", output)
        self.assertIn("0 error(s), 1 warning(s)", output)

    def test_missing_index_is_usage_error(self):
        (self.root / "knowledge/index.yaml").unlink()
        self.assertIn("ERROR knowledge/index.yaml: required index not found", self.lint(2))

    def test_missing_dependency_is_usage_error(self):
        result = subprocess.run([sys.executable, "-S", str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Missing dependency", result.stderr)
        self.assertIn("pip install pyyaml jsonschema", result.stderr)

    def test_findings_are_deterministic_and_sorted(self):
        unit = self.unit()
        unit["dependencies"]["reads"]["absent"] = []
        unit["contract"]["rules"]["access"].append({"id": "uncovered", "rule": "Evidence"})
        self.save_unit(unit)
        first = self.lint(1)
        self.assertEqual(first, self.lint(1))
        findings = first.splitlines()[:-1]
        self.assertEqual(findings, sorted(findings, key=lambda line: (line.split(" ", 1)[1].split(": ", 1)[0], line.split(" ", 1)[0], line.split(": ", 1)[1])))


class SchemaTests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self):
        for name in ("index", "knowledge", "decisions"):
            with self.subTest(name=name):
                schema = json.loads((REPO / "schema" / (name + ".schema.json")).read_text())
                Draft202012Validator.check_schema(schema)

    def test_participant_order_history_example(self):
        schema = json.loads((REPO / "schema/knowledge.schema.json").read_text())
        example = yaml.safe_load((REPO / "examples/participant-order-history.yaml").read_text())

        def normalize_dates(value):
            if isinstance(value, datetime.date):
                return value.isoformat()
            if isinstance(value, dict):
                return {key: normalize_dates(item) for key, item in value.items()}
            if isinstance(value, list):
                return [normalize_dates(item) for item in value]
            return value

        Draft202012Validator(schema).validate(normalize_dates(example))


if __name__ == "__main__":
    unittest.main()
