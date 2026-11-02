# Changelog

All notable changes to Knowledge-First Development (KFD) are documented here.
This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with the newest release first.

## [7.6.0] - 2026-11-02

### Added

- `references/consistency.md` for detailed consistency procedures.
- Optional rule fields `applies_when`, `uses`, `status`, and `superseded_by`, with linter checks.
- Generated-view registration through `views` in the index, a `kfd-sources` header with source hashes, `{unit-id/rule-id}` citations, `--view-header`, and stale-view detection.
- Approval recording through the `KFD-Review: approved` trailer and explicit behavior when no human is available.
- A standard Parking Lot tag vocabulary.
- Guidance for `CLAUDE.md`, Cursor, Gemini, and Copilot instruction files.
- `checkpoint.yaml` is gitignored by default.
- Behavior scenarios in `evals/` and the `evals/run_evals.py` harness.
- Eval harness `commands_succeed` expectations for running project commands after an agent run.

### Changed

- Consolidated repeated consistency rules in `SKILL.md` into one Consistency gate; moved detailed procedures to `references/consistency.md`.
- Shortened the Tests and Generated views sections in favor of `references/knowledge-model.md`.
- Updated examples with a single-language Parking Lot, a traceable userstories view, and rule lifecycle fields.
- The linter accepts a sentence-final `.` after conformance references.
- Rule-level schema errors report precise paths.
- Existing 7.5 projects need no changes unless rules already used the keys `applies_when`, `uses`, `status`, or `superseded_by` with other meanings; all new fields are optional.

## [7.5.0] - 2026-11-02

### Added

- JSON Schemas for the file formats: `schema/index.schema.json`, `schema/knowledge.schema.json`, and `schema/decisions.schema.json`.
- Optional project linter `scripts/kfd_lint.py` and its tests.
- Version consistency checker `tools/check_version.py` and a CI workflow.
- This changelog.
- An explicit compatibility rule: a skill can serve a project with the same major version and a project minor version no newer than the skill's; patch versions do not affect compatibility. Incompatible declarations require stopping and telling the human. Updating an older compatible declaration requires human approval, not a silent change.

### Changed

- `knowledge/index.yaml` is a catalog only; the top-level `version` key is no longer used (a legacy key is tolerated, and `KFD_VERSION` in `AGENTS.md` is authoritative).
- Unit `knowledge.yaml` files own `dependencies` and `mapping`.
- Rule references use `<unit-id>/<rule-id>` instead of `unit/group.rule`; groups are not part of rule identifiers.
- Conformance markers use `Conforms to <unit-id>/<rule-id>`.
- `assets/project-AGENTS.md` uses `{{KFD_VERSION}}`, filled with the skill version on adoption.
- Example mapping paths use `app/src` and `app/tests/<unit-id>/`.
- The Knowledge model reference document is version-free.

### Fixed

- Templates declared version 7.3 while the skill was 7.4.2.
- The README referenced a missing `CHANGELOG.md`.

### Migrating from 7.4.x / 7.3

- Move any `dependencies` from index entries into the corresponding unit's `knowledge.yaml`.
- No quoting changes are required.
- Rename `unit/group.rule` references to `unit/rule`, including conformance markers and decision references.

## [7.4.2] - 2026-10-19

### Added

- Saved Knowledge verification and mandatory Decision Required for conflicts among active saved rules (`0b1a913`).

### Fixed

- Corrected the `VERSION` file from 7.3 (`a6401ca`).

## [7.4.1] - 2026-10-19

### Added

- Rule applicability check (`556dc15`).

## [7.4] - 2026-10-19

### Changed

- Check related existing Knowledge before adding new Knowledge; replaced the Knowledge Consistency section with context-discipline search and change-classification steps (`838ceea`, preceded by `57c76f0`, "add Knowledge Consistency").

## [7.3] - 2026-10-19

### Added

- Initial public release (`76ba53c`).
