# KFD 7.3 Knowledge model reference

Read this reference when creating or reshaping Knowledge Units, changing dependencies or ownership, handling persistence/security, or generating human-readable views.

## Source-of-truth structure

```text
knowledge/
  index.yaml
  <knowledge-id>/
    knowledge.yaml
    decisions.yaml       # optional
```

`knowledge/index.yaml` is the catalog of Knowledge Units.

`knowledge/<id>/knowledge.yaml` expresses the current Why and What. Tests are conformance evidence. Implementation expresses How.

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
dependencies: {}
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

Tests should map primarily to Knowledge Units, not source-code layout.

## Dependencies

Record dependencies when a unit relies on product meaning or published outputs owned by another Knowledge Unit.

Reading another unit does not itself require a stop. Changing another unit's owned meaning does.

When the task discovers a dependency that materially affects the current unit, update the index metadata during the same change.

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

Example:

```python
def test_profile_birth_date_is_used_for_insurance_quote():
    """Conforms to visitor-insurance/pricing.profile-birth-date."""
```

A product-meaning change without suitable conformance coverage is incomplete.

## Generated human views

`userstories.md` and similar integrated documents are generated views, not a second source of truth.

When regenerating a view:

- read all relevant Knowledge Units;
- preserve their meaning;
- reorganize only for human readability;
- omit implementation details unless the view requires them;
- never invent rules, states, permissions, or guarantees;
- mark the view as generated and not directly editable.

## Knowledge Unit boundaries

A Knowledge Unit is a boundary of independently changeable product meaning, not a technical layer.

Split or reshape a unit only when ordinary changes repeatedly require unrelated rules, states, implementation, or other Knowledge Units. Do not split because a file is long, and do not reorganize implementation merely to mirror Knowledge boundaries.
