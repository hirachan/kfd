# Parking Lot and Checkpoint reference

## Parking Lot

`parking-lot.md` is pre-Knowledge. It preserves valuable intent or observations that are not part of current implementation work.

Good Parking Lot entries are:

- short;
- coarse;
- useful later;
- clearly outside the current implementation slice.

Use these optional but recommended English tags as structural vocabulary; write the entry itself in the project's chosen human language:

- `[idea]` — future product idea;
- `[refactor]` — possible refactor or simplification;
- `[risk]` — suspicious implementation or likely bug;
- `[missing-test]` — missing coverage;
- `[inconsistency]` — design inconsistency;
- `[question]` — open question.

Keep each entry on one line and append it at the end of the relevant section. If `parking-lot.md` has a merge conflict, keep both sides' entries.

Parking Lot entries are not approved requirements and do not authorize implementation.

Do not use checkboxes, done/pending states, complete task inventories, or detailed implementation plans. When an item becomes current work, refine the relevant meaning into Knowledge and remove or rewrite the parked entry.

The agent may append useful side discoveries without asking for permission merely to record them, but must not expand current scope because of them.

See `examples/parking-lot.md` for a worked example.

## Checkpoint

`checkpoint.yaml` is optional short-term resume memory for interrupted agent work.

It is local working memory for one person or agent. When creating it, add `checkpoint.yaml` to `.gitignore` unless the human wants it shared. In contrast, `parking-lot.md` and `knowledge/` are shared and committed.

Use it only when a future session would materially benefit from knowing the active area and a small amount of resume context.

Recommended shape:

```yaml
focus: participant-order-history
note: 注文履歴の表示実装を確認中。次は返金状態の表示経路から再開する。
```

Do not put these into a Checkpoint:

- complete or partial status lists;
- completed-task inventories;
- copies of Knowledge rules;
- implementation summaries that can be rediscovered cheaply;
- progress-ledger data.

Clear the Checkpoint when there is no meaningful interrupted context to preserve.
