"""Project-level regression coverage for the optional KFD linter."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
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

    def header(self, units=None, expected=0):
        option = "--view-header" if units is None else "--view-header=" + units
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.root), option], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def refresh_view(self):
        # Unit-mutating tests keep their unrelated registered view fresh.
        (self.root / "order-history.txt").write_text(
            self.header().stdout + "\nCustomers see their own orders. {orders/own-only, profiles/stable-id}\n",
            encoding="utf-8")

    def read_yaml(self, relative):
        return yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))

    def write_yaml(self, relative, data):
        (self.root / relative).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def unit(self, name="orders"):
        return self.read_yaml("knowledge/{}/knowledge.yaml".format(name))

    def save_unit(self, data, name="orders"):
        self.write_yaml("knowledge/{}/knowledge.yaml".format(name), data)
        self.refresh_view()

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

    def test_committed_fixture_is_clean_without_regeneration(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURE)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "0 error(s), 0 warning(s)\n")

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

    def test_mapping_file_cannot_have_trailing_slash(self):
        unit = self.unit()
        unit["mapping"]["implementation"]["primary"] = ["src/orders/history.py/"]
        self.save_unit(unit)
        self.assertIn("mapping path ending with '/' must be a directory", self.lint(1))

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

    def test_later_primary_directory_contains_earlier_units_file(self):
        orders = self.unit()
        orders["mapping"]["implementation"]["primary"] = ["src/orders/history.py"]
        self.save_unit(orders)
        profiles = self.unit("profiles")
        profiles["mapping"]["implementation"]["primary"] = ["src/orders/"]
        self.save_unit(profiles, "profiles")
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

    def test_docstring_markers_allow_sentence_punctuation_and_lists(self):
        path = self.root / "checks/test_contract.py"
        path.write_text(
            '"""Conforms to orders/own-only."""\n'
            '"""Conforms to orders/newest-first., profiles/stable-id."""\n',
            encoding="utf-8")
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

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

    def test_failed_unit_load_suppresses_incomplete_evidence_warnings(self):
        # Profiles owns the only mapping to the checks, including Orders' evidence.
        orders = self.unit()
        orders["mapping"].pop("tests")
        self.save_unit(orders)
        profiles = self.unit("profiles")
        profiles["mapping"]["tests"] = ["checks/"]
        self.save_unit(profiles, "profiles")
        path = self.root / "knowledge/profiles/knowledge.yaml"
        path.write_text("id: [unterminated\n", encoding="utf-8")
        output = self.lint(1)
        self.assertIn("YAML parse/read failure", output)
        self.assertNotIn("no conformance evidence", output)

    def test_stdout_escapes_unencodable_diagnostics(self):
        (self.root / "AGENTS.md").write_text("KFD_VERSION: é\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root)], capture_output=True, text=True,
            env={**os.environ, "PYTHONIOENCODING": "ascii:strict"})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn(r"invalid KFD_VERSION: \xe9", result.stdout)

    def test_yaml_parse_failure(self):
        (self.root / "knowledge/orders/knowledge.yaml").write_text("id: [unterminated\n")
        self.assertIn("YAML parse/read failure", self.lint(1))

    def test_duplicate_yaml_keys_are_parse_failures(self):
        for relative in ("knowledge/index.yaml", "knowledge/orders/knowledge.yaml",
                         "knowledge/orders/decisions.yaml"):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_text(encoding="utf-8")
                path.write_text(original + "\nduplicate: first\nduplicate: second\n", encoding="utf-8")
                output = self.lint(1)
                self.assertIn("YAML parse/read failure", output)
                self.assertIn("duplicate key: 'duplicate'", output)
                path.write_text(original, encoding="utf-8")

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

    def test_rule_lifecycle_schema_constraints(self):
        original = self.unit()
        for fields in (
            {"applies_when": ""},
            {"uses": ["bad/ref/extra"]},
            {"uses": "own-only"},
            {"status": "obsolete"},
            {"superseded_by": ["own-only"]},
            {"status": "active", "superseded_by": ["own-only"]},
            {"status": "retired", "superseded_by": []},
        ):
            with self.subTest(fields=fields):
                unit = yaml.safe_load(yaml.safe_dump(original))
                rule = unit["contract"]["rules"]["access"][0]
                rule.update(fields)
                self.save_unit(unit)
                self.assertIn("schema violation", self.lint(1))

    def test_grouped_rule_violation_reports_nested_json_path(self):
        unit = self.unit()
        unit["contract"]["rules"] = {"g": [{"id": "own-only", "rule": "Own orders.", "uses": "bad"}]}
        self.save_unit(unit)
        self.assertIn('schema violation at $["contract"]["rules"]["g"][0]["uses"]:', self.lint(1))

    def test_unresolved_lifecycle_references(self):
        for field in ("uses", "superseded_by"):
            for reference in ("missing", "profiles/missing", "absent/missing"):
                with self.subTest(field=field, reference=reference):
                    unit = self.unit()
                    rule = unit["contract"]["rules"]["access"][0 if field == "uses" else 1]
                    rule[field] = [reference]
                    self.save_unit(unit)
                    self.assertIn("." + field + ": unresolved rule ref " + reference, self.lint(1))

    def test_self_use_local_and_qualified(self):
        for reference in ("own-only", "orders/own-only"):
            with self.subTest(reference=reference):
                unit = self.unit()
                unit["contract"]["rules"]["access"][0]["uses"] = [reference]
                self.save_unit(unit)
                self.assertIn("orders/own-only uses itself", self.lint(1))

    def test_active_rule_cannot_use_retired_rule(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"][0]["uses"] = ["public-history"]
        self.save_unit(unit)
        self.assertIn("orders/own-only uses retired rule orders/public-history", self.lint(1))

    def test_local_uses_and_cross_unit_supersession_are_valid(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"][0]["status"] = "active"
        unit["contract"]["rules"]["display_rules"][0]["uses"] = ["own-only"]
        unit["contract"]["rules"]["access"][1]["superseded_by"] = ["profiles/stable-id"]
        self.save_unit(unit)
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_retired_rule_may_use_retired_rule(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"][1]["uses"] = ["public-history"]
        self.save_unit(unit)
        # Self-use is prohibited regardless of lifecycle status.
        self.assertIn("orders/public-history uses itself", self.lint(1))
        unit["contract"]["rules"]["access"].append(
            {"id": "older", "rule": "Historical behavior.", "status": "retired", "uses": ["public-history"]})
        unit["contract"]["rules"]["access"][1].pop("uses")
        self.save_unit(unit)
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_superseded_by_cannot_target_retired_rule(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"][1]["superseded_by"] = ["public-history"]
        self.save_unit(unit)
        self.assertIn("superseded_by targets retired rule orders/public-history", self.lint(1))

    def test_retired_marker_warns_but_retired_rule_needs_no_evidence(self):
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")
        path = self.root / "checks/test_contract.py"
        path.write_text(path.read_text() + "\n# Conforms to orders/public-history\n")
        output = self.lint()
        self.assertIn("retired rule orders/public-history; update or remove the test", output)
        self.assertNotIn("no conformance evidence", output)
        self.assertIn("0 error(s), 1 warning(s)", output)
        self.lint(1, strict=True)

    def test_lifecycle_and_views_suppress_invalid_unit_cascades(self):
        unit = self.unit()
        unit["contract"]["rules"]["access"][1]["superseded_by"] = ["profiles/missing"]
        self.save_unit(unit)
        path = self.root / "order-history.txt"
        path.write_text(path.read_text() + "\nUnknown while invalid. {profiles/missing}\n")
        profiles = self.unit("profiles")
        profiles["unexpected"] = True
        self.write_yaml("knowledge/profiles/knowledge.yaml", profiles)
        output = self.lint(1)
        self.assertIn("schema violation", output)
        for message in ("unresolved rule ref", "unknown citation", "unknown source", "stale source"):
            self.assertNotIn(message, output)

    def test_view_path_validation(self):
        outside = Path(self.temp.name) / "outside-view.txt"
        outside.write_text(self.header().stdout, encoding="utf-8")
        for value in ("", "/tmp/view", "../outside-view.txt", "src/../view", "C:/view", "src\\view"):
            with self.subTest(value=value):
                index = self.read_yaml("knowledge/index.yaml")
                index["views"] = [value]
                self.write_yaml("knowledge/index.yaml", index)
                self.assertIn("invalid view path", self.lint(1))

    def test_view_must_be_an_existing_file(self):
        for value in ("missing.txt", "src/", "src"):
            with self.subTest(value=value):
                index = self.read_yaml("knowledge/index.yaml")
                index["views"] = [value]
                self.write_yaml("knowledge/index.yaml", index)
                self.assertIn("view path must be an existing file", self.lint(1))

    def test_view_file_cannot_have_trailing_slash(self):
        index = self.read_yaml("knowledge/index.yaml")
        index["views"] = ["order-history.txt/"]
        self.write_yaml("knowledge/index.yaml", index)
        self.assertIn("view path ending with '/' must be a directory", self.lint(1))

    def test_view_tolerates_utf8_bom(self):
        path = self.root / "order-history.txt"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_views_must_be_array_of_strings(self):
        for value in ("order-history.txt", [42]):
            with self.subTest(value=value):
                index = self.read_yaml("knowledge/index.yaml")
                index["views"] = value
                self.write_yaml("knowledge/index.yaml", index)
                self.assertIn("schema violation", self.lint(1))

    def test_view_header_is_exact_and_sources_sorted(self):
        header = self.header().stdout
        malformed = [
            "No header\n",
            header.replace("DO NOT EDIT DIRECTLY.", "Edit freely."),
            header.replace("kfd-sources:", "sources:"),
            header.replace("  orders:", " orders:"),
            header.replace("  orders:", "  Orders:"),
            header.replace("-->", ""),
            "\n".join(header.splitlines()[:3] + list(reversed(header.splitlines()[3:-1])) + ["-->"]) + "\n",
            header.replace("kfd-sources:\n", "kfd-sources:\n" + header.splitlines()[3] + "\n"),
        ]
        for text in malformed:
            with self.subTest(text=text):
                (self.root / "order-history.txt").write_text(text)
                self.assertIn("malformed", self.lint(1))
        (self.root / "order-history.txt").write_text(" \n\t" + header)
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_unknown_view_source_unit(self):
        path = self.root / "order-history.txt"
        path.write_text(self.header().stdout.replace("  orders:", "  absent:"))
        self.assertIn("unknown source unit absent", self.lint(1))

    def test_stale_view_hash_warns_and_strict_fails(self):
        path = self.root / "knowledge/orders/knowledge.yaml"
        path.write_bytes(path.read_bytes() + b"\n")
        output = self.lint()
        self.assertIn("stale source hash for orders; regenerate the view", output)
        self.assertEqual(output, self.lint(1, strict=True))

    def test_view_citations_unknown_retired_and_missing_sources(self):
        path = self.root / "order-history.txt"
        path.write_text(self.header("orders").stdout +
                        "\nUnknown. {orders/missing, absent/missing}\n"
                        "Historical. {orders/public-history}\n"
                        "Identity. {profiles/stable-id}\n"
                        "{{PLACEHOLDER}} {{absent/placeholder}}\n")
        output = self.lint(1)
        self.assertIn("unknown citation rule orders/missing", output)
        self.assertIn("unknown citation rule absent/missing", output)
        self.assertIn("citation references retired rule orders/public-history", output)
        self.assertIn("citation unit profiles is not listed in kfd-sources", output)
        self.assertNotIn("placeholder", output.lower())

    def test_view_header_output_format_and_subset(self):
        hashes = {}
        for unit_id in ("orders", "profiles"):
            raw = (self.root / "knowledge" / unit_id / "knowledge.yaml").read_bytes()
            hashes[unit_id] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:12]
        expected = ("<!--\nGENERATED FROM KFD KNOWLEDGE. DO NOT EDIT DIRECTLY.\n"
                    "kfd-sources:\n  orders: {orders}\n  profiles: {profiles}\n-->\n").format(**hashes)
        self.assertEqual(self.header().stdout, expected)
        self.assertEqual(self.header("profiles,orders").stdout, expected)
        self.assertEqual(self.header("orders, profiles").stdout, expected)
        self.assertEqual(self.header(" orders, , profiles, ").stdout, expected)
        self.assertEqual(self.header("orders").stdout, expected.replace("  profiles: " + hashes["profiles"] + "\n", ""))
        self.assertEqual(self.header().stderr, "")

    def test_view_hash_normalizes_crlf(self):
        before = self.header().stdout
        for unit_id in ("orders", "profiles"):
            path = self.root / "knowledge" / unit_id / "knowledge.yaml"
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(self.header().stdout, before)
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")

    def test_view_header_unknown_unit_and_missing_index(self):
        result = self.header("orders,unknown", expected=2)
        self.assertIn("Unknown view source unit(s): unknown", result.stderr)
        self.assertEqual(result.stdout, "")
        (self.root / "knowledge/index.yaml").unlink()
        result = self.header(expected=2)
        self.assertIn("required index not found", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_view_header_invalid_index_diagnostics_go_to_stderr(self):
        for text in ("knowledge: [\n", "knowledge: []\n", "knowledge: {}\nknowledge: {}\n"):
            with self.subTest(text=text):
                (self.root / "knowledge/index.yaml").write_text(text, encoding="utf-8")
                result = self.header(expected=2)
                self.assertEqual(result.stdout, "")
                self.assertIn("ERROR knowledge/index.yaml:", result.stderr)

    def test_projects_without_registered_views_are_unaffected(self):
        index = self.read_yaml("knowledge/index.yaml")
        index.pop("views")
        self.write_yaml("knowledge/index.yaml", index)
        (self.root / "order-history.txt").write_text("Not a generated view.")
        self.assertEqual(self.lint(), "0 error(s), 0 warning(s)\n")


class SchemaTests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self):
        for name in ("index", "knowledge", "decisions"):
            with self.subTest(name=name):
                schema = json.loads((REPO / "schema" / (name + ".schema.json")).read_text())
                Draft202012Validator.check_schema(schema)

    def test_mapping_and_view_schemas_reject_unsafe_paths(self):
        knowledge = json.loads((REPO / "schema/knowledge.schema.json").read_text())
        index = json.loads((REPO / "schema/index.schema.json").read_text())
        mapping_path = knowledge["$defs"]["paths"]["items"]
        view_path = index["properties"]["views"]["items"]
        self.assertEqual(view_path, mapping_path)
        for value in ("", "/absolute", "..", "../outside", "src/../outside",
                      "src/..", "C:/absolute", "C:relative", "src\\file"):
            with self.subTest(value=value):
                self.assertFalse(Draft202012Validator(mapping_path).is_valid(value))

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

    def test_example_view_hash_and_citations_resolve(self):
        raw = (REPO / "examples/participant-order-history.yaml").read_bytes()
        expected_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:12]
        view = (REPO / "examples/userstories.md").read_text(encoding="utf-8-sig")
        header = re.match(
            r"\A\s*<!--\nGENERATED FROM KFD KNOWLEDGE\. DO NOT EDIT DIRECTLY\.\n"
            r"kfd-sources:\n  participant-order-history: ([0-9a-f]{12})\n-->\n", view)
        self.assertIsNotNone(header)
        self.assertEqual(header.group(1), expected_hash)
        unit = yaml.safe_load(raw)
        groups = unit["contract"]["rules"]
        rules = groups if isinstance(groups, list) else [rule for group in groups.values() for rule in group]
        refs = {unit["id"] + "/" + rule["id"] for rule in rules}
        citations = re.findall(r"\{([^{}]+)\}", view)
        self.assertTrue(citations)
        for citation in citations:
            for reference in citation.split(","):
                self.assertIn(reference.strip(), refs)


if __name__ == "__main__":
    unittest.main()
