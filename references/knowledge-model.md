# KFD Knowledge model reference

Read this reference when creating or reshaping Knowledge Units, changing dependencies or ownership, handling persistence/security, or generating human-readable views.

## Source-of-truth structure

```text
knowledge/
  index.yaml
  <knowledge-id>/
    knowledge.yaml
    decisions.yaml       # optional
```

`knowledge/index.yaml` is the catalog of Knowledge Units. Its keys are unit IDs; each entry requires a non-empty `name` and may include a `summary`:

```yaml
knowledge:
  participant-order-history:
    name: 参加者向け注文履歴
    summary: 参加者本人の注文と決済状態を表示する。
```

The unit path is derived as `knowledge/<id>/knowledge.yaml`, not stored in the index. Index entries allow extra metadata for compatibility, but dependencies and ownership belong to the unit. A legacy top-level `version` is tolerated; the project's `KFD_VERSION` declaration belongs in `AGENTS.md`.

`knowledge/<id>/knowledge.yaml` expresses the current Why and What and owns its dependencies and implementation/test mapping. Tests are conformance evidence. Implementation expresses How. A unit requires `id`, `name`, `purpose`, and `contract`; its only optional top-level keys are `examples`, `dependencies`, and `mapping`. Its `id` must match its directory name.

The normative formats are `schema/index.schema.json`, `schema/knowledge.schema.json`, and `schema/decisions.schema.json`. Editors may select the appropriate schema with an optional YAML modeline, using a path or URL:

```yaml
# yaml-language-server: $schema=../../schema/knowledge.schema.json
```

`decisions.yaml` is optional and selective. It exists only to preserve an important historical decision or rejected alternative that would otherwise be rediscovered incorrectly. Git is the ordinary history.

## Recommended Knowledge Unit shape

Start from `assets/knowledge.yaml` and add only structures needed by the product meaning.

```yaml
id: participant-order-history
name: 参加者向け注文履歴
purpose:
  why: >
    参加者が自分の購入内容と決済状況を確認できるようにする。
contract:
  rules:
    - id: own-orders-only
      rule: 他の参加者の注文は表示しない。
dependencies:
  reads: {}
  writes: {}
mapping:
  implementation:
    primary:
      - app/src/orders/history.py
    shared:
      - app/src/payments/status.py
  tests:
    - app/tests/participant-order-history/
```

The Knowledge Unit may grow to contain actors, inputs, states, transitions, UI behavior, persistence, external effects, and examples when those structures are necessary to express current product meaning.

Do not add structure merely for completeness.

### Identifiers and rule references

Unit IDs and rule IDs use lowercase kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`). Rule IDs must be unique within a unit, including across groups. `contract.rules` may be a list, as above, or a map of groups to rule lists:

```yaml
contract:
  rules:
    access:
      - id: own-orders-only
        rule: 他の参加者の注文は表示しない。
    presentation:
      - id: current-payment-state
        rule: 支払いと返金は現在の確定状態を表示する。
```

Group names use lowercase words separated by hyphens or underscores. Groups organize rules for humans; they are not part of rule IDs. A fully qualified reference is `<unit-id>/<rule-id>`, such as `participant-order-history/own-orders-only`.

### Rule lifecycle and reuse

All lifecycle fields are optional:

- `applies_when` is a non-empty, human-language applicability condition. Without it, the rule applies throughout the unit's scope.
- `uses` is an array of shared rule references whose conditions this rule relies on instead of restating them. Use `<rule-id>` within the same unit or `<unit-id>/<rule-id>` across units.
- `status` is `active` (the default when absent) or `retired`.
- `superseded_by` is a non-empty array of rule references, allowed only with `status: retired`.

```yaml
contract:
  rules:
    - id: own-orders-only
      rule: ログイン参加者は自分の注文だけを閲覧できる。
    - id: current-payment-state
      applies_when: 注文履歴で支払い・返金状態を表示するとき。
      uses: [own-orders-only]
      rule: 支払いと返金は現在の確定状態を表示する。
```

Normally delete retired rules: Git is the history. Retain a retired rule only when something still needs to refer to it, such as `decisions.yaml` `affects_rules` or an explanation of existing data. Add `superseded_by` when applicable. Decision references may target retired rules; active rules must not rely on them.

## Mapping

Implementation and tests are mapping information, not top-level product meaning.

Keep them under:

```yaml
mapping:
  implementation:
    primary: []
    shared: []
  tests: []
```

A file owned by one Knowledge Unit belongs in `primary`. A file used by multiple units without independent ownership belongs in `shared`.

Paths are relative to the project root and use `/` separators. Directory paths end with `/`; absolute paths and `..` segments are not allowed. A path may be `primary` in at most one unit, including containment: one unit's primary directory cannot contain another unit's primary file or directory.

Tests should map primarily to Knowledge Units, not source-code layout.

## Dependencies

Record dependencies when a unit relies on product meaning or published outputs owned by another Knowledge Unit.

Reading another unit does not itself require a stop. Changing another unit's owned meaning does.

Dependencies live in the unit's `knowledge.yaml`, not the index. Under `reads` and `writes`, keys are other unit IDs and values are lists of published outputs or data:

```yaml
dependencies:
  reads:
    checkout-orders:
      - participant_orders
      - order_items
  writes:
    order-notifications:
      - delivery_requests
```

When the task discovers a dependency that materially affects the current unit, update the unit's dependencies during the same change.

## Persistence, compatibility, and security

Always make these explicit in Knowledge when applicable:

- stored data;
- schema constraints;
- migrations;
- backward/forward compatibility;
- permissions and data exposure;
- privacy;
- authentication;
- prices and payment state.

Treat browser input as untrusted. Enforce authorization and business rules server-side.

## Tests as Evidence

Every important rule needs suitable conformance evidence. Prefer stable rule IDs and tests whose names or documentation make the correspondence visible.

Use the marker `Conforms to <unit-id>/<rule-id>` in a test comment or docstring. A comma-separated list is allowed on the same line, for example `Conforms to orders/own-orders-only, payments/current-payment-state`.

Example:

```python
def test_profile_birth_date_is_used_for_insurance_quote():
    """Conforms to visitor-insurance/profile-birth-date."""
```

A product-meaning change without suitable conformance coverage is incomplete.

Tests are organized primarily around Knowledge Units, not source-code layout. A unit may map to `app/tests/<knowledge-id>/` while its implementation spans a different structure under `app/src/`. Do not force this layout onto projects whose framework or established structure makes another layout more natural. Knowledge boundaries and source-code boundaries do not have to match.

## Decisions

An optional unit-local `decisions.yaml` records selected historical decisions. Quote dates so they remain strings. `affects_rules` accepts local `<rule-id>` references for the same unit or qualified `<unit-id>/<rule-id>` references:

```yaml
decisions:
  - id: use-purchase-snapshot
    date: "2026-01-15"
    status: accepted
    decision: 注文時の商品情報を表示する。
    context: 購入後に商品設定が変更されることがある。
    reason: 購入時の内容を確認できるようにする。
    rejected: []
    affects_rules:
      - immutable-purchase-description
      - participant-order-history/current-payment-state
```

Each decision requires `id` (kebab-case), `date` (`YYYY-MM-DD` string), `status`, and `decision`. The remaining fields shown are optional. The top level contains only `decisions`; decision entries accept only the fields shown.

## Validation

The optional project linter checks structural consistency:

```sh
uv run scripts/kfd_lint.py <project-root>
# Alternatively, with PyYAML and jsonschema installed:
python3 scripts/kfd_lint.py <project-root>
```

The project root defaults to `.`. Add `--strict` to treat warnings as failures. Exit codes are `0` for no errors (warnings allowed), `1` for errors or strict-mode warnings, and `2` for usage errors, missing dependencies, or a missing `knowledge/index.yaml`.

It checks:

- YAML parsing and index, unit, and decisions schemas;
- catalog/file agreement, unit directory IDs, and duplicate rule IDs;
- mapping path existence, safe relative paths, and primary ownership overlaps;
- dependency targets, conformance markers, missing rule evidence, and decision rule references;
- the `AGENTS.md` version declaration and compatibility, plus legacy index metadata warnings;
- unresolved `uses` or `superseded_by` references, a rule using itself, active rules using retired rules, and `superseded_by` targets that are retired (errors);
- conformance markers referencing retired rules (warning: update or remove the test); retired rules do not receive missing-conformance-evidence warnings;
- registered view paths, generated headers and source units, source hashes, and inline rule citations (see below).

The linter does not check semantic consistency or establish that implementation and tests satisfy the product meaning.

## Generated human views

`userstories.md` and similar integrated documents are generated views, not a second source of truth. When asked for a complete human-readable specification, read all relevant Knowledge Units and generate an integrated view rather than maintaining a separate specification.

When regenerating a view:

- read all relevant Knowledge Units;
- preserve their meaning;
- reorganize only for human readability;
- omit implementation details unless the view requires them;
- never invent rules, states, permissions, or guarantees;
- mark the view as generated and not directly editable.

Register generated views in the optional top-level `views` array in `knowledge/index.yaml`:

```yaml
knowledge:
  participant-order-history:
    name: 参加者向け注文履歴
views:
  - userstories.md
```

View paths are project-relative, use `/` separators, and must not be absolute or contain `..` segments, just like mapping paths. Projects without `views` are unaffected by view checks.

Every generated view starts with this exact header as its first non-whitespace content:

```html
<!--
GENERATED FROM KFD KNOWLEDGE. DO NOT EDIT DIRECTLY.
kfd-sources:
  participant-order-history: 3f2a9c1b7e44
-->
```

Include one `  <unit-id>: <hash>` line per source unit, sorted by unit ID. The hash is the first 12 lowercase hexadecimal characters of SHA-256 of that unit's `knowledge.yaml` bytes after converting CRLF to LF.

Use the linter to obtain the header when regenerating a view:

```sh
python3 scripts/kfd_lint.py <project-root> --view-header
python3 scripts/kfd_lint.py <project-root> --view-header=participant-order-history,checkout-orders
```

`--view-header` prints the header for all index units, sorted; `--view-header=a,b` selects a subset. These commands exit `0` on success or `2` with a message for an unknown unit or missing index.

Every guarantee or rule sentence in a view should cite the supporting rules immediately after the sentence: `{<unit-id>/<rule-id>}` or, for multiple rules, `{a/x, b/y}`. For example:

```text
ログイン参加者は自分の注文だけを閲覧できる。 {participant-order-history/own-orders-only}
```

For each registered view the linter reports:

- errors for invalid or missing paths, missing or malformed headers or `kfd-sources`, unknown source units, and citations of unknown rules;
- warnings for stale source hashes (regenerate the view), citations of retired rules, and citations from units not listed in `kfd-sources`.

## Knowledge Unit boundaries

A Knowledge Unit is a boundary of independently changeable product meaning, not a technical layer.

Split or reshape a unit only when ordinary changes repeatedly require unrelated rules, states, implementation, or other Knowledge Units. Do not split because a file is long, and do not reorganize implementation merely to mirror Knowledge boundaries.
