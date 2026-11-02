# Changelog

All notable changes to Knowledge-First Development (KFD) are documented here.
This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), with the newest release first.

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
