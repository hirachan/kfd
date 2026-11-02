---
name: kfd
description: Apply Knowledge-First Development (KFD) 7.6.0 to new or existing software projects. Use when a project declares KFD, when the human asks to adopt or use KFD, or when making product-meaning changes, bug fixes, business-rule changes, UI behavior changes, persistence/security changes, tests, or implementation changes that must stay aligned with explicit Knowledge.
---
# Knowledge-First Development (KFD) 7.6.0

KFD keeps current product meaning explicit and reviewable before implementation changes.

## Priorities

1. Do not regress externally observable behavior.
2. Keep current product meaning understandable and reviewable by humans.
3. Use the smallest sufficient context for safe changes.

Do not refactor, rename, relocate, abstract, or optimize unrelated implementation unless explicitly requested or necessary to preserve these priorities.

## When to apply KFD

Apply this skill when the repository's `AGENTS.md` declares KFD, the human explicitly asks to adopt or use KFD, or the current task belongs to a project already using KFD.

This skill implements KFD 7.6.0. The authoritative project declaration is `KFD_VERSION` in `AGENTS.md`, using `MAJOR.MINOR[.PATCH]`. A project is compatible when its major matches this skill's major and its minor is no greater than this skill's minor; patch does not affect compatibility. Otherwise, stop and tell the human; do not silently reinterpret the declaration as this version. When this skill's minor is newer, follow this skill and optionally propose updating the declaration, but never change it silently.

## Adoption and human language

KFD must be adoptable at any time, including after substantial implementation exists, without a separate initialization command or migration step. When first used:
1. Preserve existing source/test layout, build system, documentation, and `AGENTS.md` instructions.
2. If the human-facing language is not established, ask the human before generating substantive Knowledge or human-facing documentation.
3. Merge the section from `assets/project-AGENTS.md` into project `AGENTS.md`, preserving unrelated instructions and filling placeholders (`{{KFD_VERSION}}` = this skill's version):
   ```text
   KFD_VERSION: 7.6.0
   PROJECT_HUMAN_LANGUAGE: <language>
   ```
4. Create `knowledge/index.yaml` from `assets/project-index.yaml` and `parking-lot.md` only if they do not exist.
5. Do not create `checkpoint.yaml` until interrupted work needs resumable context.
6. Create/refine Knowledge Units incrementally for the area being changed, not the entire existing product.
7. For implemented areas without Knowledge, establish only the minimum baseline needed for this change from relevant behavior, tests, documentation, and explicit human intent. Do not canonize incidental implementation details. If intended meaning cannot be established safely, use **Decision Required**.

For new projects the same rules apply; `app/src/` and `app/tests/` are preferred defaults only when no framework or structure establishes something better. Do not overwrite existing KFD files to match templates; merge/extend while preserving current meaning and unrelated human changes.

When other agent tools are used, existing tool-specific instructions (`CLAUDE.md`, `.cursor/rules/`, `GEMINI.md`, `.github/copilot-instructions.md`) should point to `AGENTS.md`, not duplicate its KFD section (Claude Code: `@AGENTS.md` in `CLAUDE.md`). Touch these files only if they exist or the human uses that tool; never create them speculatively.

Human-facing meaning uses the chosen language: Knowledge explanations, Parking Lot entries, Checkpoint notes, generated views, reviews, questions, and normal product discussion. Keep YAML keys, unit IDs, file/directory names, source identifiers/paths, and KFD structural identifiers in English: **Structure in English; human-facing meaning in the project's chosen language.**

## Source of truth

`knowledge/index.yaml` is the catalog: `knowledge: <unit-id>: {name, summary?}`. A name is required; summary is optional. Unit files are `knowledge/<unit-id>/knowledge.yaml`, with optional `decisions.yaml` alongside.

`knowledge.yaml` is the source of truth for the current Why and What of that unit. Each unit owns its `dependencies` and implementation/test ownership under `mapping`. Tests are Evidence. Implementation is How. Unit/rule IDs use kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`); rule IDs are unique within a unit. `contract.rules` is a list or groups of rule lists; groups are not part of IDs. Qualified rule references use `<unit-id>/<rule-id>`.

Optional rule fields: `applies_when` is a non-empty applicability condition (absent = throughout unit scope); `uses` lists local `<rule-id>` or qualified `<unit-id>/<rule-id>` references to shared rules—prefer it over restating shared conditions. `status` defaults to `active` or may be `retired`; `superseded_by` is a non-empty reference list allowed only on retired rules. Normally delete retired rules (Git is history); retain them only while something still needs to refer to them (e.g. `affects_rules`, or explaining existing data), with `superseded_by` when applicable.

The normative formats are `schema/index.schema.json`, `schema/knowledge.schema.json`, and `schema/decisions.schema.json`. `decisions.yaml` is not a change log: record only important past decisions/rejected alternatives that would otherwise be rediscovered incorrectly; Git is ordinary history.

Integrated documents such as `userstories.md` are generated views, not a second source of truth; never edit them to change product meaning. Read `references/knowledge-model.md` when creating units, changing dependencies/ownership, handling persistence/security, or generating integrated views.

## Parking Lot

`parking-lot.md` preserves valuable intent/ideas/observations outside current implementation. The boundary is current work, not size: refine current instructions directly into Knowledge; keep remaining intent coarse in the Parking Lot. Small clear instructions normally go directly to a unit; large instructions must not trigger full specification of many inferred future units.

Agents may append useful out-of-scope discoveries without permission: future ideas, refactors/simplifications, suspicious implementation/likely bugs, missing coverage, inconsistencies, or questions. Record briefly and continue; do not expand the task. Entries are coarse and short, not approved requirements, detailed specifications, implementation plans, or a progress ledger.

Optional recommended tags: `[idea]` future idea; `[refactor]` simplification; `[risk]` suspected bug; `[missing-test]` coverage gap; `[inconsistency]` design inconsistency; `[question]` open question.

Append one-line entries at the end of the relevant section; keep both sides' entries on merge conflicts. Do not use checkboxes or implemented/pending status. Do not implement or promote Parking Lot content merely because it exists. Promotion happens only when the current instruction clearly includes it or the human explicitly selects it for implementation. Refine it into Knowledge and remove/rewrite the parked item so only non-current intent remains.

Read `references/parking-lot-checkpoint.md` for Parking Lot and interrupted-context boundaries.

## Prompt intake

For each instruction:
1. Identify the smallest coherent slice being implemented now and locate/create its Knowledge Units.
2. Park valuable remaining intent without fully specifying it; classify the requested change.
3. For changed product meaning: Knowledge -> human approval -> Tests -> Implementation.
4. Write/update tests as required and implement; park out-of-scope discoveries rather than expanding scope.

## Checkpoint

`checkpoint.yaml` is optional short-term memory for resuming interrupted AI work, not product Knowledge, history, or a progress ledger. When creating it, add `checkpoint.yaml` to `.gitignore` unless the human wants it shared; `parking-lot.md` and `knowledge/` are shared and committed.

Keep only information materially reducing next-session rediscovery, e.g. `focus: insurance` and `note: Stripe webhook handling was the last active implementation area.` Do not maintain complete/partial lists, completed-task inventories, rule copies, or implementation summaries. Determine conformance from Knowledge, tests, and implementation when needed. Clear the checkpoint when no meaningful interrupted context remains.

## Application and test layout

For new projects prefer `app/src/` for implementation and `app/tests/` for verification. Organize tests primarily around Knowledge Units, e.g. `app/tests/<knowledge-id>/`, even when implementation spans another structure. Do not force this onto established projects; Knowledge and source boundaries need not match. Implementation/test locations are mapping information, not top-level product meaning; keep them under `mapping`.

## Context discipline

Use the smallest sufficient context. Start with this skill and project `AGENTS.md`, a resumable checkpoint if present, `knowledge/index.yaml`, target `knowledge.yaml`, directly affected tests, and implementation paths mapped by the unit.

Expand only on evidence: a dependency needs understanding, a test exposes unexplained effects, implementation conflicts with Knowledge, or the change crosses units. Do not scan unrelated repository areas for completeness. If routine unit changes repeatedly need excessive unrelated reading, reconsider its boundary or exposed implementation coupling; do not split/reorganize speculatively.

## Change classification

Classify before editing.

### Knowledge change

Externally visible product meaning includes permissions/data exposure; stored data/schema/migration/compatibility; prices/payments/refunds/eligibility/business rules; states/transitions; UI meaning/grouping/visibility/navigation/actions; external effects/integrations.

Required order:
1. Resolve material ambiguity through **Decision Required**; apply the **Consistency gate**.
2. Update `knowledge.yaml` in every affected unit and verify saved Knowledge.
3. Present **Knowledge Review** and wait for human approval before tests/implementation.
4. Update/add tests, then implement.
5. Update unit `dependencies`/`mapping` if dependencies, ownership, or evidence changed; update index catalog entries only when units are added/removed/renamed or their name/summary changes.
6. Regenerate affected human views; record important decisions only when they prevent future misunderstanding.

### Knowledge-preserving bug fix

When observed behavior clearly violates written Knowledge, apply the Consistency gate, add/update a regression test, fix implementation, and verify affected and full tests. Do not require Knowledge Review and do not rewrite Knowledge unless it was insufficient to identify the bug.

### Meaning-preserving change

Wording, spacing, color, internal cleanup, and equivalent implementation changes need no Knowledge update/Review if permissions, visibility, navigation, actions, persistence, and meaning remain unchanged. Add tests only in proportion to regression risk.

## Consistency gate

Read `references/consistency.md` before Knowledge Review for any product-meaning change that touches existing rules.

- Identify affected concepts and search narrowly for related rules, including unchanged rules, undeclared dependencies, and relevant maintained product documents; expand only on relevant evidence.
- Check each related rule's applicability across changed boundaries and distinct operations sharing the behavior. Revise, narrow, or retire obsolete rules; do not leave obsolete unconditional rules active.
- Prefer shared rule references to repeated conditions. Preserve historical rules only with explicit applicability and according to the lifecycle guidance above.
- Before Knowledge Review and completion, re-read actual saved affected Knowledge, not planned edits, patch output, or review prose; confirm revised/retired edits landed and preserved rules still apply.
- Correct failed edits and re-read; editing failure alone is not a product-meaning decision.
- Compare relevant active saved rules under overlapping conditions, including maintained documents claiming current normative authority.
- Unambiguous new requirements may supersede old rules: update the obsolete rules and verify the saved result.
- Genuine remaining conflicts require **Decision Required** with sources, overlap, consequences, alternatives, and any justified recommendation. Never silently choose a rule, invent exceptions, or claim consistency.
- Block Knowledge Review and dependent Tests/Implementation until the human decision is approved and reflected in saved Knowledge; safely independent work may continue.
- Reconcile saved rules only after the decision is approved; then re-read, verify consistency, and review actual resulting Knowledge. Material edits after approval require renewed Review and approval.
- Knowledge Review approval is not approval of an unresolved conflict resolution.
- Apply the saved-rule conflict check to Knowledge-preserving bug fixes too; block dependent fixes on unresolved conflicts.
- When Python is available, run `uv run <skill-dir>/scripts/kfd_lint.py <project-root>` or `python3 <skill-dir>/scripts/kfd_lint.py <project-root>` (with PyYAML and jsonschema installed) and fix reported errors; structural validation never replaces semantic checks.
- Keep all checks proportional to affected concepts, without a project-wide inventory or new mandatory file.

## Decision Required

Stop and ask before implementation when a material product choice is unresolved: reasonable interpretations differ visibly; persistence/migration/permissions/privacy/security is unspecified; a request conflicts with Knowledge; active saved rules disagree under overlapping conditions; another unit's owned meaning must change; or UI meaning/disclosure is unclear.

Use concrete choices and `assets/decision-required.md` when useful. Do not stop for implementation details that preserve product meaning. Approval must come from a human in the conversation; silence, timeouts, or absence of a human are never approval, including for Decision Required. With no human available, stop and report the needed decision.

## Knowledge Review

Before implementing a Knowledge change, summarize only changed product meaning, based on verified saved files:

```text
Knowledge Review: <Knowledge Unit name>

- Users will ...
- The system will ...
- The system will not ...
- Existing data will ...

Approve this product meaning to continue.
```

For changed existing rules, briefly identify related rules revised, preserved (why still applicable), or retired/superseded, and relevant new boundaries/operations sharing the behavior. Conversation does not substitute for updating `knowledge.yaml`. Use `assets/knowledge-review.md` when a fuller artifact helps.

Only a human in the conversation may approve. Silence, timeouts, and absence of a human are never approval. When committing is requested or expected by repository workflow (KFD never requires it), commit approved Knowledge separately from tests/implementation with `KFD-Review: approved` and, when the approver is known, `Reviewed-by: <name>` trailers. This also covers approved Decision Required resolutions reflected in Knowledge. If not committing, state which Knowledge changes were approved in the final report.

With no human available (non-interactive/autonomous/CI/background runs), still update and verify Knowledge, then STOP before tests/implementation and hand it over for review: if allowed to create PRs, open a draft PR containing only the Knowledge change with the Knowledge Review text in its description; otherwise leave it uncommitted/on its branch and report the Review text. Knowledge-preserving bug fixes and meaning-preserving changes may complete without a human.

## Cross-Knowledge changes

Each unit records dependencies and implementation/test ownership in `dependencies` and `mapping`.
- Reading published outputs without changing meaning requires no stop; update dependency metadata when needed.
- Changing another unit's owned product meaning requires Decision Required and Review of every affected unit.
- One implementation file must not be independently owned by multiple units; mark shared files `shared`.
- Keep implementation appropriate to framework/codebase; Knowledge boundaries need not match source boundaries.

Record newly discovered task-relevant dependencies during the same change.

## Persistence and security

Stored data, schema constraints, migrations, compatibility, permissions, privacy, authentication, prices, and payment state always require explicit Knowledge coverage and Knowledge Review. Browser input is untrusted; enforce authorization and business rules server-side.

## Tests

Every important rule needs conformance evidence; prefer test names corresponding to stable rule IDs and mark test comments/docstrings `Conforms to <unit-id>/<rule-id>`. Product-meaning changes without suitable coverage are incomplete. Read `references/knowledge-model.md` for details.

## Generated human views

Regenerate existing affected views, including `userstories.md`, after product-meaning changes and whenever the linter reports staleness. Register generated paths in `knowledge/index.yaml` under `views`; generate the required header with `python3 <skill-dir>/scripts/kfd_lint.py <root> --view-header` (or `--view-header=a,b` for selected units). Cite supporting rules after guarantee/rule sentences as `{unit-id/rule-id}` or `{a/x, b/y}`. Preserve Knowledge meaning; never invent guarantees or edit views as a second source of truth. Read `references/knowledge-model.md` for header, citations, and generation procedures.

## Knowledge Unit boundaries

Units bound independently changeable product meaning, not technical layers. Keep enough meaning together for safe changes without unrelated reading. When ordinary changes repeatedly need unrelated rules/states/implementation/units, propose a meaning-preserving Knowledge refactor. Do not split just because a file is long or reorganize implementation to mirror Knowledge hierarchy.

## Completion check

Before finishing, confirm the classification and Consistency gate; required human decisions/Review approval; relevant tests updated and run; accurate dependencies/ownership; linter free of errors when runnable; refreshed affected views; preserved unrelated user changes; no unrequested improvement; parked useful out-of-scope discoveries; and checkpointed interrupted context only when useful. A no-human Knowledge handover stops at Review, not completed implementation.

Report result, verification, important unresolved risk, and any decision still needed.

## Bundled resources

Use only when needed:
- `references/consistency.md` — related-rule search, applicability, saved-file verification, conflicts, and re-review.
- `references/knowledge-model.md` — unit structure, mapping, decisions, dependencies, persistence/security, tests, and generated views.
- `references/parking-lot-checkpoint.md` — Parking Lot and Checkpoint boundaries.
- `assets/knowledge.yaml` — minimal unit template.
- `assets/decisions.yaml` — optional decision-history template.
- `assets/decision-required.md` — Decision Required template.
- `assets/knowledge-review.md` — Knowledge Review template.
- `schema/index.schema.json` — normative catalog format.
- `schema/knowledge.schema.json` — normative unit format.
- `schema/decisions.schema.json` — normative decision-history format.
- `scripts/kfd_lint.py` — structural and conformance-reference checks.
- `CHANGELOG.md` — release history.
- `examples/participant-order-history.yaml` — worked unit.
- `examples/parking-lot.md` — worked Parking Lot.
- `examples/checkpoint.yaml` — worked Checkpoint.
- `examples/userstories.md` — worked generated view.
