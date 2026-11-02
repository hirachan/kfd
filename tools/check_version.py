#!/usr/bin/env python3
"""Check the skill's concrete version declarations using only the stdlib."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERNS = (
    re.compile(r"\(KFD\)\s+v?(\d+\.\d+(?:\.\d+)?)"),
    re.compile(r"\bKFD\s+v?(\d+\.\d+(?:\.\d+)?)"),
    re.compile(r"KFD_VERSION:\s*(\d+\.\d+(?:\.\d+)?)"),
)
YAML_VERSION_PATTERN = re.compile(
    r"^version:\s*[\"']?(\d+\.\d+(?:\.\d+)?)", re.MULTILINE
)


def main():
    problems = []
    try:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        print(f"VERSION: cannot read version: {exc}")
        return 1

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        problems.append("VERSION: expected a MAJOR.MINOR.PATCH version")

    paths = [ROOT / name for name in ("SKILL.md", "README.md", "README_ja.md")]
    for directory in ("references", "assets", "examples"):
        paths.extend(path for path in sorted((ROOT / directory).rglob("*")) if path.is_file())

    texts = {}
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            problems.append(f"{relative}: cannot scan a non-UTF-8 file")
            continue
        except OSError as exc:
            problems.append(f"{relative}: cannot read file: {exc}")
            continue
        texts[relative] = text
        patterns = VERSION_PATTERNS
        if path.suffix.lower() in (".yaml", ".yml"):
            patterns += (YAML_VERSION_PATTERN,)
        reported = set()
        for pattern in patterns:
            for match in pattern.finditer(text):
                found = match.group(1)
                line = text.count("\n", 0, match.start(1)) + 1
                if found != version and (line, found) not in reported:
                    problems.append(f"{relative}:{line}: found {found}, expected {version}")
                    reported.add((line, found))

    skill = texts.get("SKILL.md", "")
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", skill, re.DOTALL)
    description = None
    if frontmatter:
        description = re.search(r"^description:\s*(.*)$", frontmatter.group(1), re.MULTILINE)
    version_token = re.escape(version) + r"(?![\d.])"
    if not description or not re.search(
        r"\(KFD\)\s+v?" + version_token, description.group(1)
    ):
        problems.append(f"SKILL.md: frontmatter description must declare KFD {version}")
    if not re.search(
        r"^# Knowledge-First Development \(KFD\)\s+v?" + version_token + r"\s*$",
        skill,
        re.MULTILINE,
    ):
        problems.append(f"SKILL.md: H1 must declare KFD {version}")
    if not re.search(r"^\s*KFD_VERSION:\s*" + re.escape(version) + r"\s*$", skill, re.MULTILINE):
        problems.append(f"SKILL.md: missing KFD_VERSION: {version}")

    if "KFD_VERSION: {{KFD_VERSION}}" not in texts.get("assets/project-AGENTS.md", ""):
        problems.append("assets/project-AGENTS.md: missing KFD_VERSION: {{KFD_VERSION}}")

    try:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        problems.append(f"CHANGELOG.md: cannot read file: {exc}")
    else:
        first_release = re.search(r"^## \[([^\]\n]+)\]", changelog, re.MULTILINE)
        if not first_release or first_release.group(1) != version:
            problems.append(f"CHANGELOG.md: first release heading must be ## [{version}]")

    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"version OK: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
