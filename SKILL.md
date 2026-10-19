---
name: kfd
description: Apply Knowledge-First Development (KFD) 7.3 to new or existing software projects. Use when a project declares KFD, when the human asks to adopt or use KFD, or when making product-meaning changes, bug fixes, business-rule changes, UI behavior changes, persistence/security changes, tests, or implementation changes that must stay aligned with explicit Knowledge.
---

# Knowledge-First Development (KFD) 7.3

KFD keeps current product meaning explicit and reviewable before implementation changes.

## Priorities

1. Do not regress externally observable behavior.
2. Keep current product meaning understandable and reviewable by humans.
3. Use the smallest sufficient context for safe changes.

Do not refactor, rename, relocate, abstract, or optimize unrelated implementation unless explicitly requested or necessary to preserve these priorities.

## When to apply KFD

Apply this skill when any of the following is true:

- the repository's `AGENTS.md` declares that it uses KFD;
- the human explicitly asks to adopt or use KFD;
- the current task is part of a project that already uses KFD.

If the repository declares `KFD_VERSION`, respect that declaration. This skill implements KFD 7.3. If a project declares an incompatible KFD version, do not silently reinterpret it as 7.3.

## Adoption and human language

KFD must be adoptable at any time, including after substantial implementation already exists. Do not require a separate initialization command or migration step.

When KFD is first used in a project:

1. Preserve the project's existing source layout, test layout, build system, documentation, and existing `AGENTS.md` instructions.
2. If the human-facing language is not yet established, ask the human which language to use before generating substantive Knowledge or human-facing documentation.
3. Record KFD in project `AGENTS.md`. If `AGENTS.md` already exists, merge a small KFD section into it instead of replacing unrelated instructions. Record:

   ```text
   KFD_VERSION: 7.3
   PROJECT_HUMAN_LANGUAGE: <language>
   ```

4. Create `knowledge/index.yaml` only if it does not exist.
5. Create `parking-lot.md` only if it does not exist.
6. Do not create `checkpoint.yaml` until interrupted work actually needs resumable context.
7. Do not attempt to describe the entire existing product up front. Create or refine Knowledge Units incrementally for the product area being changed now.
8. When the touched area already has implementation but no Knowledge, establish only the minimum baseline Knowledge needed for the current change from relevant existing behavior, tests, documentation, and explicit human intent. Do not automatically canonize incidental implementation details as product meaning. If the intended meaning cannot be established safely, use **Decision Required**.

For a brand-new project, the same rules apply. `app/src/` and `app/tests/` are merely preferred defaults when no framework or project structure already establishes something better.

Do not overwrite existing KFD files merely to make them match bundled templates. Merge or extend them while preserving current project meaning and unrelated human changes.

Human-facing meaning uses the chosen language: Knowledge explanations, Parking Lot entries, Checkpoint notes, generated `userstories.md`, reviews, questions, and normal product discussion.

Keep structural vocabulary in English: YAML keys, Knowledge Unit IDs, file/directory names, source identifiers and paths, and KFD structural identifiers.

**Structure in English; human-facing meaning in the project's chosen language.**

## Source of truth

`knowledge/index.yaml` lists the Knowledge Units managed by KFD.

Each unit normally has:

```text
knowledge/<id>/knowledge.yaml
knowledge/<id>/decisions.yaml   # optional
```

`knowledge.yaml` is the source of truth for the current Why and What of that unit. Tests are Evidence. Implementation is How.

`decisions.yaml` is not a change log. Use it only when an important past decision or rejected alternative would otherwise be rediscovered incorrectly. Git remains the ordinary history.

Human-facing integrated documents such as `userstories.md` are generated views. They are not a second source of truth and must not be edited to change product meaning.

Read `references/knowledge-model.md` when creating a Knowledge Unit, changing dependencies/ownership, handling persistence/security, or generating integrated views.

## Parking Lot

`parking-lot.md` is the pre-Knowledge area for valuable product intent, ideas, and observations that are worth preserving but are not part of the current implementation.

The boundary is based on current work, not merely on size:

- if an instruction is part of the work being implemented now, refine it directly into Knowledge;
- if valuable intent is not being implemented now, preserve it in the Parking Lot;
- a small, clear instruction normally goes directly to the relevant Knowledge Unit;
- a large instruction must not cause the agent to fully specify many future Knowledge Units merely because they can be inferred. Refine the current implementation slice into Knowledge and keep remaining intent coarse in the Parking Lot.

An agent may append to the Parking Lot without asking for permission when normal work reveals something useful but not necessary for the current task, including:

- a future product idea;
- a possible refactor or implementation simplification;
- a suspicious implementation or likely future bug;
- missing test coverage;
- a design inconsistency or open question.

Do not expand the current task merely because such an item was discovered. Record it briefly and continue the requested work.

Parking Lot entries should normally remain coarse and short. They are not approved requirements, detailed specifications, implementation plans, or a progress ledger.

Do not use checkboxes or implemented/pending status to track progress. When Parking Lot intent becomes part of current work, refine the relevant part into Knowledge and remove or rewrite the parked item so the Parking Lot continues to represent only intent that has not become current Knowledge.

Do not implement or promote Parking Lot content merely because it exists. Promotion happens only when the current instruction clearly includes it or the human explicitly selects it for implementation.

Read `references/parking-lot-checkpoint.md` when deciding whether to park an item or preserve interrupted working context.

## Prompt intake

For each user instruction:

1. identify the smallest coherent slice actually being implemented now;
2. locate or create the Knowledge Unit(s) required for that slice;
3. preserve valuable remaining intent in the Parking Lot without fully specifying it;
4. classify the requested change;
5. update Knowledge before tests and implementation when product meaning changes;
6. write or update tests as required;
7. implement the change;
8. park useful out-of-scope discoveries instead of silently expanding scope.

A small instruction may flow directly:

```text
Prompt -> Knowledge -> Tests -> Implementation
```

A broader instruction may split:

```text
Prompt
  |-- current implementation slice -> Knowledge -> Tests -> Implementation
  `-- valuable remaining intent ----> Parking Lot
```

## Checkpoint

`checkpoint.yaml` is optional short-term working memory for resuming interrupted AI work across sessions. It is not product Knowledge, history, or a progress ledger.

Keep it minimal. Record only information that materially reduces rediscovery in the next session, for example:

```yaml
focus: insurance
note: Stripe webhook handling was the last active implementation area.
```

Do not maintain complete/partial status lists, completed-task inventories, rule copies, or implementation summaries. Determine current conformance from Knowledge, tests, and implementation when needed.

Clear the checkpoint when there is no meaningful interrupted context to preserve.

## Application and test layout

For new projects, prefer:

```text
app/
  src/
  tests/
```

`app/src/` contains implementation and `app/tests/` contains verification.

Tests are organized primarily around Knowledge Units, not source-code layout. A Knowledge Unit may map to `app/tests/<knowledge-id>/` while its implementation spans a different structure under `app/src/`.

Do not force this layout onto existing projects when their framework or established structure makes another layout more natural. Knowledge boundaries and source-code boundaries do not have to match.

Within `knowledge.yaml`, implementation and test locations are mapping information, not top-level product meaning. Keep them under `mapping`.

## Context discipline

Use the smallest sufficient context for each task.

Start with:

1. this skill and project `AGENTS.md`;
2. `checkpoint.yaml`, only when it contains resumable context;
3. `knowledge/index.yaml`;
4. the target `knowledge.yaml`;
5. directly affected tests;
6. implementation paths listed for the target Knowledge Unit.

Expand context only when evidence requires it, including when:

- a declared dependency must be understood;
- a test exposes an unexplained effect;
- implementation evidence conflicts with the Knowledge;
- the requested change crosses Knowledge Unit boundaries.

Do not scan or understand unrelated parts of the repository merely for completeness.

If routine changes to one Knowledge Unit repeatedly require excessive unrelated reading, reconsider the Knowledge Unit boundary or the implementation coupling exposed by the task. Do not split or reorganize speculatively.

## Change classification

Classify the request before editing.

### Knowledge change

A change to externally visible product meaning, including:

- permissions or data exposure;
- stored data, schema, migration, or compatibility;
- prices, payments, refunds, eligibility, or business rules;
- states or transitions;
- UI meaning, grouping, visibility, navigation, or available actions;
- external effects or integrations.

Required order:

1. Resolve material ambiguity with **Decision Required**.
2. Update `knowledge.yaml`.
3. Show **Knowledge Review** and wait for approval.
4. Update or add tests.
5. Implement.
6. Update index metadata if dependencies, ownership, or evidence changed.
7. Regenerate affected human-facing views when present.
8. Record an important decision only when it prevents future misunderstanding.

### Knowledge-preserving bug fix

When observed behavior clearly violates written Knowledge:

1. add or update a regression test;
2. fix the implementation;
3. verify affected and full tests.

Do not require Knowledge Review and do not rewrite Knowledge unless it was insufficient to identify the bug.

### Meaning-preserving change

Wording, spacing, color, internal cleanup, and equivalent implementation changes do not require a Knowledge update or Knowledge Review if permissions, visibility, navigation, actions, persistence, and meaning remain unchanged.

Add tests only in proportion to regression risk.

## Decision Required

Stop and ask before implementation when a material product choice remains unresolved.

Typical triggers:

- two reasonable interpretations produce different visible results;
- persistence, migration, permissions, privacy, or security is not specified;
- the request conflicts with current Knowledge;
- another Knowledge Unit would need to change what it owns;
- UI meaning or disclosure is unclear.

Use concrete choices. Follow `assets/decision-required.md` when a fuller review artifact helps.

Do not stop for an implementation detail that does not change product meaning.

## Knowledge Review

Before implementing a Knowledge change, summarize only the changed product meaning:

```text
Knowledge Review: <Knowledge Unit name>

- Users will ...
- The system will ...
- The system will not ...
- Existing data will ...

Approve this product meaning to continue.
```

Conversation is not a substitute for updating `knowledge.yaml`.

Use `assets/knowledge-review.md` when a fuller review artifact helps.

## Cross-Knowledge changes

The index records dependencies and implementation ownership.

- Reading another Knowledge Unit's published output does not require stopping when the read does not change its meaning. Update dependency metadata when needed.
- Changing another Knowledge Unit's owned product meaning requires a Decision Required and review of every affected Knowledge Unit.
- One implementation file must not be independently owned by multiple Knowledge Units. Shared files must be marked `shared`.
- Knowledge boundaries do not require matching source-code boundaries. Keep implementation structure appropriate to the framework and codebase.

When a newly discovered dependency is relevant to the task, record it in the index during the same change.

## Persistence and security

Stored data, schema constraints, migrations, compatibility, permissions, privacy, authentication, prices, and payment state always require explicit Knowledge coverage and Knowledge Review.

Browser input is untrusted. Authorization and business rules must be enforced server-side.

## Tests

Every important rule needs conformance evidence. Prefer test names that correspond to stable rule IDs.

Example:

```python
def test_profile_birth_date_is_used_for_insurance_quote():
    """Conforms to visitor-insurance/pricing.profile-birth-date."""
```

A product-meaning change without suitable conformance coverage is incomplete.

## Generated human views

When `userstories.md` exists, regenerate it from the current Knowledge Base after product-meaning changes that affect the view.

The generated view may reorganize Knowledge for human readability, but it must:

- preserve the meaning of the Knowledge Base;
- omit implementation details unless the view explicitly requires them;
- never invent rules, states, permissions, or guarantees;
- clearly state that it is generated and must not be edited directly.

A request for a complete human-readable specification should be fulfilled by reading all relevant Knowledge Units and generating the appropriate integrated view, not by creating a separately maintained specification.

## Knowledge Unit boundaries

Knowledge Units are boundaries of independently changeable product meaning, not technical layers.

A good Knowledge Unit contains enough meaning to change safely without unrelated reading. If a unit grows so that ordinary changes repeatedly require unrelated rules, states, implementation, or other Knowledge Units, propose a meaning-preserving Knowledge refactor.

Do not split merely because a file is long. Do not reorganize implementation merely to mirror the Knowledge hierarchy.

## Knowledge Consistency

Before approving or implementing a Knowledge change:

1. Identify the business rules and concepts affected by the change.
2. Search other Knowledge Units for rules that describe the same behavior, including indirect references and exceptions.
3. Check whether the proposed change makes any existing Knowledge outdated, contradictory, or ambiguous.
4. Prefer one authoritative definition of a shared business rule. Other Knowledge Units should reference that definition instead of independently redefining it.
5. Preserve intentional historical rules only when their applicability conditions are explicit.
6. If two Knowledge rules contradict each other, do not invent an exception to reconcile them. Use Decision Required unless explicit human intent resolves the conflict.
7. Include affected Knowledge Units, preserved behaviors, and detected inconsistencies in Knowledge Review.

Before fixing an implementation inconsistency:

1. Check whether the relevant Knowledge is internally consistent.
2. If the Knowledge is contradictory or ambiguous, do not modify correct implementation behavior to satisfy an arbitrarily selected rule.
3. Resolve the Knowledge inconsistency first, then update Tests and Implementation.

Keep this verification limited to the affected business concepts. Do not load or rewrite the entire Knowledge Base unless necessary.

## Completion check

Before finishing, verify:

- the change classification was correct;
- no unresolved material decision remains;
- current Knowledge matches the result;
- Knowledge Review was approved when required;
- relevant tests were updated and run;
- dependencies and ownership are accurate;
- generated human views were refreshed when applicable;
- unrelated user changes were preserved;
- no unrequested improvement was implemented;
- useful out-of-scope discoveries were parked instead of expanding scope;
- interrupted working context was checkpointed only when useful.

Report the result, verification, important unresolved risk, and any decision still needed.

## Bundled resources

Use these only when needed:

- `references/knowledge-model.md` — Knowledge Unit structure, mapping, decisions, dependencies, persistence/security, and generated views.
- `references/parking-lot-checkpoint.md` — guidance for Parking Lot and Checkpoint boundaries.
- `assets/knowledge.yaml` — minimal Knowledge Unit template.
- `assets/decisions.yaml` — optional decision-history template.
- `assets/decision-required.md` — Decision Required presentation template.
- `assets/knowledge-review.md` — Knowledge Review presentation template.
- `examples/participant-order-history.yaml` — worked Knowledge Unit example.
- `examples/parking-lot.md` — worked Parking Lot example.
- `examples/checkpoint.yaml` — worked Checkpoint example.
- `examples/userstories.md` — worked generated human view.
