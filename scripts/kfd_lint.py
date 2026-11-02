#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6", "jsonschema>=4"]
# ///
"""Validate a project's KFD catalog, contracts, ownership, and evidence."""

import argparse
import datetime
import json
from pathlib import Path, PurePosixPath
import re
import sys


VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)(?:\.([0-9]+))?\Z")
REFERENCE = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
MARKER_RE = re.compile(r"Conforms to\s+(" + REFERENCE + r"(?:\s*,\s*" + REFERENCE + r")*)")
MAX_TEXT_SIZE = 1024 * 1024


def normalize(value):
    """YAML dates are strings in the JSON data model used by the schemas."""
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def json_path(parts):
    result = "$"
    for part in parts:
        result += "[{}]".format(part) if isinstance(part, int) else "[{}]".format(json.dumps(part))
    return result


def rules_in(unit):
    rules = unit["contract"]["rules"]
    return rules if isinstance(rules, list) else [rule for group in rules.values() for rule in group]


def version_tuple(text):
    match = VERSION_RE.fullmatch(text)
    return tuple(int(value or 0) for value in match.groups()) if match else None


class Linter:
    def __init__(self, root, schemas, skill_version, yaml, validator):
        self.root = root
        self.schemas = schemas
        self.skill_version = skill_version
        self.yaml = yaml
        self.validator = validator
        self.findings = set()

    def report(self, level, path, message):
        relative = path.relative_to(self.root).as_posix()
        self.findings.add((relative, level, message))

    def error(self, path, message):
        self.report("ERROR", path, message)

    def warn(self, path, message):
        self.report("WARN", path, message)

    def load(self, path, schema_name):
        try:
            data = normalize(self.yaml.safe_load(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, self.yaml.YAMLError, ValueError, RecursionError) as exc:
            self.error(path, "YAML parse/read failure: " + " ".join(str(exc).splitlines()))
            return None
        if schema_name == "index" and isinstance(data, dict):
            legacy = data.get("version")
            if isinstance(legacy, (int, float)) and not isinstance(legacy, bool):
                data["version"] = str(legacy)
        # JSON object keys must be strings; reject YAML-only keys before validation.
        def check_keys(value, parts=()):
            if isinstance(value, dict):
                for key, item in value.items():
                    if not isinstance(key, str):
                        self.error(path, "schema violation at {}: object keys must be strings".format(json_path(parts)))
                        return False
                    if not check_keys(item, parts + (key,)):
                        return False
            elif isinstance(value, list):
                for position, item in enumerate(value):
                    if not check_keys(item, parts + (position,)):
                        return False
            return True
        if not check_keys(data):
            return None
        errors = list(self.validator(self.schemas[schema_name]).iter_errors(data))
        for error in errors:
            self.error(path, "schema violation at {}: {}".format(json_path(error.absolute_path), error.message))
        return None if errors else data

    def check_version(self, index):
        path = self.root / "AGENTS.md"
        declaration = None
        if not path.is_file():
            self.warn(path, "AGENTS.md is missing; declare KFD_VERSION")
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                self.error(path, "cannot read version declaration: {}".format(exc))
                text = ""
            match = re.search(r"KFD_VERSION:\s*(\S+)", text)
            if not match:
                self.warn(path, "KFD_VERSION declaration is missing")
            else:
                declaration = match.group(1)
                project = version_tuple(declaration)
                if project is None:
                    self.error(path, "invalid KFD_VERSION: {}".format(declaration))
                elif project[0] != self.skill_version[0] or project[1] > self.skill_version[1]:
                    self.error(path, "incompatible KFD_VERSION: {}".format(declaration))
        if index is not None and "version" in index:
            legacy = str(index["version"])
            old_version = version_tuple(legacy)
            declared_version = version_tuple(declaration) if declaration else None
            if old_version is None or declared_version is None or old_version != declared_version:
                self.warn(self.root / "knowledge/index.yaml", "legacy index version differs from AGENTS.md declaration")

    def mapping_path(self, source, value):
        path = PurePosixPath(value)
        if not value or path.is_absolute() or re.match(r"^[A-Za-z]:", value) or ".." in path.parts or "\\" in value:
            self.error(source, "invalid mapping path: {} (use project-relative / paths without '..')".format(value))
            return None
        target = self.root / value
        if not target.exists():
            self.error(source, "mapping path does not exist: {}".format(value))
            return None
        if target.is_dir() and not value.endswith("/"):
            self.error(source, "mapping directory path must end with '/': {}".format(value))
        return target

    def run(self):
        index_path = self.root / "knowledge/index.yaml"
        index = self.load(index_path, "index")
        self.check_version(index)
        catalog = index["knowledge"] if index is not None else {}
        unit_paths = sorted((self.root / "knowledge").glob("*/knowledge.yaml"))
        found = {path.parent.name for path in unit_paths}
        if index is not None:
            for unit_id, entry in sorted(catalog.items()):
                if unit_id not in found:
                    self.error(index_path, "index unit {} has no knowledge/{}/knowledge.yaml".format(unit_id, unit_id))
                if "dependencies" in entry:
                    self.warn(index_path, "legacy dependencies in index entry {}; move into the unit's dependencies".format(unit_id))
            for unit_id in sorted(found - set(catalog)):
                self.error(self.root / "knowledge" / unit_id / "knowledge.yaml", "unit {} is not listed in index".format(unit_id))
        units = {}
        for path in unit_paths:
            unit = self.load(path, "knowledge")
            if unit is not None:
                units[path.parent.name] = (path, unit)
                if unit["id"] != path.parent.name:
                    self.error(path, "unit id {} does not match directory {}".format(unit["id"], path.parent.name))
        invalid_units = found - set(units)
        known = set(catalog) | found
        refs = set()
        ownership = []
        test_files = set()
        for unit_id, (path, unit) in sorted(units.items()):
            seen = set()
            for rule in rules_in(unit):
                rule_id = rule["id"]
                if rule_id in seen:
                    self.error(path, "duplicate rule id: {}".format(rule_id))
                seen.add(rule_id)
                refs.add(unit_id + "/" + rule_id)
            for kind, dependencies in unit.get("dependencies", {}).items():
                for dependency in sorted(dependencies):
                    if dependency not in known:
                        self.error(path, "unknown dependency unit {} in dependencies.{}".format(dependency, kind))
                    elif dependency == unit_id:
                        self.warn(path, "self-dependency in dependencies.{}: {}".format(kind, dependency))
            mapping = unit.get("mapping", {})
            for kind, values in mapping.get("implementation", {}).items():
                for value in values:
                    target = self.mapping_path(path, value)
                    if target is not None:
                        ownership.append((unit_id, kind, target, path, value))
            for value in mapping.get("tests", []):
                target = self.mapping_path(path, value)
                if target is not None:
                    candidates = target.rglob("*") if target.is_dir() else [target]
                    test_files.update(candidate for candidate in candidates if candidate.is_file())
        for position, left in enumerate(ownership):
            for right in ownership[position + 1:]:
                if left[0] == right[0] or left[1] == right[1] == "shared":
                    continue
                a, b = left[2], right[2]
                overlap = a == b or (a.is_dir() and a in b.parents) or (b.is_dir() and b in a.parents)
                if overlap:
                    message = "{} ownership overlap: {} ({}) and {} ({})".format(
                        "primary" if left[1] == right[1] else "primary/shared", left[0], left[4], right[0], right[4])
                    if left[1] == right[1]:
                        self.error(left[3], message)
                    else:
                        self.warn(left[3], message)
        evidence = set()
        for path in sorted(test_files):
            try:
                if path.stat().st_size > MAX_TEXT_SIZE:
                    continue
                raw = path.read_bytes()
                if b"\0" in raw:
                    continue
                text = raw.decode("utf-8")
            except (OSError, UnicodeError):
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                for marker in MARKER_RE.finditer(line):
                    for reference in re.split(r"\s*,\s*", marker.group(1)):
                        if reference.split("/", 1)[0] in invalid_units:
                            continue
                        if reference not in refs:
                            self.error(path, "line {}: unknown conformance ref {}".format(line_number, reference))
                        else:
                            evidence.add(reference)
        for reference in sorted(refs - evidence):
            unit_id = reference.split("/", 1)[0]
            self.warn(units[unit_id][0], "no conformance evidence for {}".format(reference))
        for path in sorted((self.root / "knowledge").glob("*/decisions.yaml")):
            decisions = self.load(path, "decisions")
            if decisions is None:
                continue
            for position, decision in enumerate(decisions["decisions"]):
                for reference in decision.get("affects_rules", []):
                    qualified = reference if "/" in reference else path.parent.name + "/" + reference
                    if qualified.split("/", 1)[0] in invalid_units:
                        continue
                    if qualified not in refs:
                        self.error(path, "decisions[{}].affects_rules: unresolved rule ref {}".format(position, reference))

    def print_findings(self):
        for path, level, message in sorted(self.findings):
            print("{} {}: {}".format(level, path, message))
        errors = sum(level == "ERROR" for _, level, _ in self.findings)
        warnings = len(self.findings) - errors
        print("{} error(s), {} warning(s)".format(errors, warnings))
        return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="treat warnings as a failing result")
    args = parser.parse_args(argv)
    try:
        import yaml
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        print("Missing dependency: {}. Install PyYAML and jsonschema with 'python3 -m pip install pyyaml jsonschema', or use 'uv run scripts/kfd_lint.py'.".format(exc.name), file=sys.stderr)
        return 2
    root = Path(args.project_root).resolve()
    if not (root / "knowledge/index.yaml").is_file():
        print("ERROR knowledge/index.yaml: required index not found")
        print("1 error(s), 0 warning(s)")
        return 2
    resources = Path(__file__).resolve().parent.parent
    try:
        schemas = {name: json.loads((resources / "schema" / (name + ".schema.json")).read_text(encoding="utf-8"))
                   for name in ("index", "knowledge", "decisions")}
        skill_version = version_tuple((resources / "VERSION").read_text(encoding="utf-8").strip())
        if skill_version is None:
            raise ValueError("invalid skill VERSION")
    except (OSError, ValueError) as exc:
        print("Cannot load KFD schemas/VERSION: {}".format(exc), file=sys.stderr)
        return 2
    linter = Linter(root, schemas, skill_version, yaml, Draft202012Validator)
    linter.run()
    errors, warnings = linter.print_findings()
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
